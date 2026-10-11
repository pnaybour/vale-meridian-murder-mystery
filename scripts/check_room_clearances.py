"""Check the drawn spacing against the assumed room.

The coordinates in local_room_layout are illustrative, on an assumed 12 m by 6 m main room. This
reports what that assumption implies, so the plan is not read as a survey. Where it says there is
no room behind a table, the likely reading is that the assumed room is too small, not that the
table will not fit: your venue is the judge of what fits.

Once you have measured your room, change OUTLINE and TABLES in scripts/register_room_layout.py;
these figures and the printed plan follow.

  python3 scripts/check_room_clearances.py
"""
from __future__ import annotations
import argparse, json, math, sqlite3
from pathlib import Path

CHAIR = 0.55     # metres beyond the tabletop for an occupied chair
SQUEEZE = 0.6    # metres more for a person to get past


def to_segment(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def main():
    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--db', type=Path, default=root / 'data/valemeridian-event.sqlite')
    args = ap.parse_args()

    db = sqlite3.connect(args.db)
    db.row_factory = sqlite3.Row
    tables = [dict(r) for r in db.execute('SELECT * FROM local_room_layout ORDER BY table_number')]
    outline = json.loads(db.execute('SELECT outline_json FROM local_room_plan').fetchone()[0])
    guests = dict(db.execute(
        "SELECT table_number, count(*) FROM seat_assignments "
        "WHERE plan_id='approved-plan' GROUP BY table_number"))
    db.close()

    reach = {t['table_number']: t['diameter_m'] / 2 + CHAIR for t in tables}
    at = {t['table_number']: (t['x'], t['y']) for t in tables}

    print(f'A chair needs {CHAIR} m beyond the tabletop; getting past needs about {SQUEEZE} m more.\n')
    print('Behind the chairs, to the nearest wall:')
    blocked = []
    for number, (x, y) in sorted(at.items()):
        nearest = min(to_segment(x, y, *outline[i], *outline[(i + 1) % len(outline)])
                      for i in range(len(outline)))
        gap = nearest - reach[number]
        if gap < SQUEEZE: blocked.append(number)
        note = '  no route behind' if gap < SQUEEZE else ''
        print(f'  table {number} ({guests.get(number, 0)} guests): {gap:5.2f} m{note}')

    print('\nBetween neighbouring tables:')
    for a in sorted(at):
        for b in sorted(at):
            if a >= b: continue
            gap = math.dist(at[a], at[b]) - reach[a] - reach[b]
            if gap >= 1.2: continue
            note = '  too narrow to pass' if gap < SQUEEZE else '  single file' if gap < 0.9 else ''
            print(f'  {a}-{b}: {gap:5.2f} m{note}')

    if blocked:
        print(f'\nOn the assumed depth, {len(blocked)} of {len(at)} tables have no route behind '
              f'them: {", ".join(map(str, blocked))}.')
        print('Read this as the drawing being tighter than your room, not as proof that the tables')
        print('will not fit: measure the room, then set the spacing on the day.')


if __name__ == '__main__':
    main()
