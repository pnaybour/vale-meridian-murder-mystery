"""Record each guest's position around their table.

The Print Studio draws a seating diagram for every table and a floor plan for the venue. Both need
the angle of every chair, recorded here in local_seat_positions beside the table positions in
local_room_layout.

Seats are spaced evenly around each round table in seat order, clockwise. The only choice is where
the first seat of each table sits, so the table can be turned to suit the room: edit ROTATIONS.

Angles are degrees clockwise from the top of the room diagram, where the top is the far wall of
the main room. They describe where the chair stands, not which way the guest faces; guests face
inward. Table membership and clockwise order are fixed because people sit in family and partner
groups: a whole table may be rotated, never reordered.

  python3 scripts/register_seat_positions.py            show what would change
  python3 scripts/register_seat_positions.py --apply    write local_seat_positions
"""
from __future__ import annotations
import argparse, shutil, sqlite3, sys
from datetime import date, datetime, timezone
from pathlib import Path

PLAN = 'room-layout'
SEATING_PLAN = 'approved-plan'

# Angle of each table's first seat, in degrees clockwise from the top of the diagram.
ROTATIONS = {1: 35, 2: 150, 3: 55, 4: 340, 5: 320, 6: 285, 7: 30, 8: 115}

SCHEMA = """CREATE TABLE IF NOT EXISTS local_seat_positions (
  plan_id TEXT NOT NULL,
  person_id TEXT NOT NULL,
  table_number INTEGER NOT NULL,
  seat_number INTEGER NOT NULL,
  angle_deg REAL NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (plan_id, person_id))"""


def clock(angle):
    """The angle as a clock face position, which is how most people read these."""
    minutes = round(angle / 360 * 720) % 720
    hour, minute = divmod(minutes, 60)
    return f'{hour or 12}:{minute:02d}'


def main():
    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--db', type=Path, default=root / 'data/valemeridian-event.sqlite')
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()

    db = sqlite3.connect(args.db)
    db.row_factory = sqlite3.Row
    seats = [dict(r) for r in db.execute(
        'SELECT person_id, guest_name, table_number, seat_number FROM seat_assignments '
        'WHERE plan_id=? ORDER BY table_number, seat_number', (SEATING_PLAN,))]

    tables = sorted({s['table_number'] for s in seats})
    bad = [f'table {t} has seats but no rotation in ROTATIONS' for t in tables if t not in ROTATIONS]
    if bad:
        db.close(); print('BLOCKED:', *bad, sep='\n  '); sys.exit(1)

    angles = {}
    for number in tables:
        table = [s for s in seats if s['table_number'] == number]
        step = 360 / len(table)
        for i, s in enumerate(table):
            angles[s['person_id']] = (ROTATIONS[number] + i * step) % 360

    for number in tables:
        table = [s for s in seats if s['table_number'] == number]
        joined = ', '.join(f"seat {s['seat_number']} {clock(angles[s['person_id']])}" for s in table)
        print(f'  table {number}: {joined}')
    print(f'\n{len(seats)} seats positioned across {len(tables)} tables')
    if not args.apply:
        db.close(); print('Preview only. Re-run with --apply to write.'); return

    bk = root / 'data/backups' / f'valemeridian-event-before-seat-positions-{date.today()}.sqlite'
    db.close()
    bk.parent.mkdir(parents=True, exist_ok=True)
    if not bk.exists(): shutil.copy2(args.db, bk)
    print(f'before-database: {bk}')
    now = datetime.now(timezone.utc).isoformat(timespec='seconds')
    db = sqlite3.connect(args.db)
    try:
        with db:
            db.execute(SCHEMA)
            db.execute('DELETE FROM local_seat_positions WHERE plan_id=?', (PLAN,))
            for s in seats:
                db.execute('INSERT INTO local_seat_positions '
                           '(plan_id, person_id, table_number, seat_number, angle_deg, updated_at) '
                           'VALUES (?,?,?,?,?,?)',
                           (PLAN, s['person_id'], s['table_number'], s['seat_number'],
                            angles[s['person_id']], now))
        written = db.execute('SELECT count(*) FROM local_seat_positions WHERE plan_id=?', (PLAN,)).fetchone()[0]
        if written != len(seats):
            print(f'VERIFY FAILED: {written} of {len(seats)} written'); sys.exit(1)
        print(f'verified: {written} seat positions recorded')
    finally:
        db.close()


if __name__ == '__main__':
    main()
