"""Record the room layout in the database.

The seating itself lives in seat_assignments. This script records the facts that had no other
home: where each table stands, which room it is in, and the shape of the floor. The Print Studio
draws the guest "Find your table" sheet and the room plan from them, so those sheets cannot fall
out of step with the seating plan.

The layout below is a sample, not a survey. Change TABLES, OUTLINE and ROOMS to describe your own
venue, then re-run with --apply and refresh the Print Studio (npm run snapshot).

Units are metres from the top-left of the main room, x rightwards and y downwards.

  python3 scripts/register_room_layout.py            show what would change
  python3 scripts/register_room_layout.py --apply    write the layout tables
"""
from __future__ import annotations
import argparse, json, shutil, sqlite3, sys
from datetime import date, datetime, timezone
from pathlib import Path

PLAN = 'room-layout'

SCHEMA = [
 """CREATE TABLE IF NOT EXISTS local_room_layout (
      table_number INTEGER PRIMARY KEY,
      room TEXT NOT NULL,
      x REAL NOT NULL,
      y REAL NOT NULL,
      diameter_m REAL NOT NULL,
      plan_id TEXT NOT NULL,
      updated_at TEXT NOT NULL)""",
 """CREATE TABLE IF NOT EXISTS local_room_plan (
      plan_id TEXT PRIMARY KEY,
      outline_json TEXT NOT NULL,
      rooms_json TEXT NOT NULL,
      notes TEXT NOT NULL,
      updated_at TEXT NOT NULL)""",
]

# table_number -> (room, x, y, assumed diameter in metres). Tables 3 and 8 are through the
# opening, 8 nearest it. MAIN_ROOM_LIMIT is how many tables the main room holds.
# Diameters are planning assumptions, not hotel specifications.
TABLES = {
 1: ('main', 8.7, 1.5, 1.8),
 2: ('main', 10.5, 4.5, 1.8),
 3: ('adjoining', 6.0, 11.35, 1.2),
 4: ('main', 6.9, 4.5, 1.5),
 5: ('main', 1.5, 1.5, 1.5),
 6: ('main', 3.3, 4.5, 1.5),
 7: ('main', 5.1, 1.5, 1.5),
 8: ('adjoining', 6.0, 8.0, 1.5),
}
MAIN_ROOM_LIMIT = 6

# The floor as a single closed polygon: the wide main room, then the neck through to the
# adjoining room.
OUTLINE = [(0, 0), (12, 0), (12, 6), (8.5, 6), (8.5, 15), (3.5, 15), (3.5, 6), (0, 6)]

ROOMS = {
 'main': dict(name='Main room', short='Main room', caption=None),
 'adjoining': dict(name='Adjoining room', short='Adjoining room',
                   caption='Table 8 is nearest the opening.'),
}

NOTES = (
 'Illustrative layout, not a survey: metres from the top-left of the main room, x rightwards and y '
 'downwards, on an assumed 12 m by 6 m main room and a 9 m by 5 m second room. Diameters are '
 'assumed, with about 0.55 m allowed beyond each tabletop for an occupied chair. Tables 3 and 8 '
 'are through the opening, with 8 nearest it, which keeps cross-room clue exchanges down to 16 of '
 '56; the strongest links are 4-8, 1-4, 1-7, 3-8 and 6-7. Those counts measure clue instructions, '
 'not walking journeys. Table membership and clockwise order are fixed because guests sit in '
 'family and partner groups; a whole table may be rotated, never reordered.')



def main():
    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--db', type=Path, default=root / 'data/valemeridian-event.sqlite')
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()

    db = sqlite3.connect(args.db)
    seated = {r[0] for r in db.execute(
        "SELECT DISTINCT table_number FROM seat_assignments WHERE plan_id='approved-plan'")}
    bad = [f'table {t} has a position but no seats' for t in TABLES if t not in seated]
    bad += [f'table {t} has seats but no position' for t in seated if t not in TABLES]
    bad += [f'table {t}: unknown room {r!r}' for t, (r, *_ ) in TABLES.items() if r not in ROOMS]
    in_main = sum(1 for r, *_ in TABLES.values() if r == 'main')
    if in_main > MAIN_ROOM_LIMIT:
        bad.append(f'{in_main} tables in the main room; the room holds only {MAIN_ROOM_LIMIT}')
    if bad:
        db.close(); print('BLOCKED:', *bad, sep='\n  '); sys.exit(1)

    have = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='local_room_layout'").fetchone()
    before = dict(db.execute('SELECT table_number, room FROM local_room_layout')) if have else {}
    for t, (room, x, y, dia) in sorted(TABLES.items()):
        state = 'new' if t not in before else ('changed' if before[t] != room else 'same')
        print(f'  table {t}  {room:9s} at ({x:5.2f}, {y:5.2f})  {dia:.1f} m   {state}')
    print(f'\n{len(TABLES)} tables, {len(OUTLINE)}-point outline, {len(ROOMS)} rooms')
    if not args.apply:
        db.close(); print('Preview only. Re-run with --apply to write.'); return

    bk = root / 'data/backups' / f'valemeridian-event-before-room-layout-{date.today()}.sqlite'
    db.close()
    if not bk.exists(): shutil.copy2(args.db, bk)
    print(f'before-database: {bk}')
    now = datetime.now(timezone.utc).isoformat(timespec='seconds')
    db = sqlite3.connect(args.db)
    try:
        with db:
            for statement in SCHEMA: db.execute(statement)
            for t, (room, x, y, dia) in TABLES.items():
                db.execute('INSERT OR REPLACE INTO local_room_layout '
                           '(table_number, room, x, y, diameter_m, plan_id, updated_at) '
                           'VALUES (?,?,?,?,?,?,?)', (t, room, x, y, dia, PLAN, now))
            db.execute('INSERT OR REPLACE INTO local_room_plan '
                       '(plan_id, outline_json, rooms_json, notes, updated_at) VALUES (?,?,?,?,?)',
                       (PLAN, json.dumps(OUTLINE), json.dumps(ROOMS), NOTES, now))
        rows = dict(db.execute('SELECT table_number, room FROM local_room_layout'))
        if rows != {t: r for t, (r, *_ ) in TABLES.items()}:
            print('VERIFY FAILED: layout not written'); sys.exit(1)
        outline = json.loads(db.execute('SELECT outline_json FROM local_room_plan WHERE plan_id=?', (PLAN,)).fetchone()[0])
        if [tuple(p) for p in outline] != OUTLINE:
            print('VERIFY FAILED: outline not written'); sys.exit(1)
        print(f'verified: {len(rows)} tables positioned, outline and rooms stored')
    finally:
        db.close()


if __name__ == '__main__':
    main()
