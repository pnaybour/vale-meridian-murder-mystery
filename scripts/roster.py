"""Put your own guests on the seating plan.

The kit ships with a sample roster ("Guest 01" and so on) already seated across eight tables. The
tables, seats and characters are the tested arrangement; what you change is who plays each
character. Export the roster to a spreadsheet, fill in the guest column, and import it again.

  python3 scripts/roster.py export                    write roster.csv from the database
  python3 scripts/roster.py export --out my-party.csv
  python3 scripts/roster.py import roster.csv         show what would change
  python3 scripts/roster.py import roster.csv --apply write the changes (after a backup)

roster.csv has one row per seat:

  table, seat, character   identify the seat; they must match the plan and are not changed
  guest                    the player's name as it should print on badges, place cards and signs
  group                    optional: guests with the same value are one family or party, and the
                           reviews count how many of them kept together (blank for none)
  dietary                  optional: printed on the table signs as short flags (GF, V, ...)

To change which character a guest plays, move their name to another row. To change a table, swap
guests between rows; the character a row plays decides the clues, so avoid editing the character
column. The Game Master row is the host (the Family Solicitor), and Helicopter Pilot is a child.

Afterwards refresh the Print Studio: (cd print-studio && npm run snapshot).
"""
from __future__ import annotations
import argparse, csv, shutil, sqlite3, sys
from datetime import date
from pathlib import Path

EVENT = 'valemeridian'
PLAN = 'approved-plan'
FIELDS = ['table', 'seat', 'character', 'guest', 'group', 'dietary']


def seats(db):
    return [dict(r) for r in db.execute(
        'SELECT s.table_number, s.seat_number, s.character_name, s.person_id, s.guest_name, '
        'COALESCE(s.real_world_group, "") AS grp, COALESCE(p.dietary_notes, "") AS dietary '
        'FROM seat_assignments s JOIN people p ON p.person_id = s.person_id '
        'WHERE s.plan_id=? ORDER BY s.table_number, s.seat_number', (PLAN,))]


def export(args, db):
    rows = seats(db)
    with open(args.out, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(FIELDS)
        for s in rows:
            w.writerow([s['table_number'], s['seat_number'], s['character_name'], s['guest_name'], s['grp'], s['dietary']])
    print(f'Wrote {len(rows)} seats to {args.out}. Fill in the guest column, then import it.')


def read(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        missing = [c for c in FIELDS[:4] if c not in (reader.fieldnames or [])]
        if missing:
            raise SystemExit(f'{path}: missing column(s): {", ".join(missing)}')
        return [{k: (v or '').strip() for k, v in row.items()} for row in reader]


def plan_changes(db, rows):
    current = {(s['table_number'], s['seat_number']): s for s in seats(db)}
    problems, changes, seen_guests = [], [], {}
    given = set()
    for n, row in enumerate(rows, start=2):
        try:
            key = (int(row['table']), int(row['seat']))
        except ValueError:
            problems.append(f'line {n}: table and seat must be numbers'); continue
        seat = current.get(key)
        if not seat:
            problems.append(f'line {n}: there is no table {key[0]} seat {key[1]} in the plan'); continue
        if row['character'] and row['character'] != seat['character_name']:
            problems.append(f"line {n}: table {key[0]} seat {key[1]} is {seat['character_name']}, not {row['character']}")
            continue
        if not row['guest']:
            problems.append(f'line {n}: guest is empty for {seat["character_name"]}'); continue
        if row['guest'] in seen_guests:
            problems.append(f'line {n}: {row["guest"]} is already on line {seen_guests[row["guest"]]}'); continue
        seen_guests[row['guest']] = n
        if key in given:
            problems.append(f'line {n}: table {key[0]} seat {key[1]} appears twice'); continue
        given.add(key)
        changes.append((seat, row))
    for key in sorted(set(current) - given):
        problems.append(f'table {key[0]} seat {key[1]} ({current[key]["character_name"]}) is missing from the file')
    return problems, changes


def apply_changes(db, changes):
    # The first guest named in each group is the booking contact the others are listed under.
    anchor = {}
    for seat, row in changes:
        if row.get('group'):
            anchor.setdefault(row['group'], row['guest'])
    # display_name is unique, so park every name before assigning the new ones.
    for seat, _ in changes:
        db.execute('UPDATE people SET display_name=? WHERE person_id=?', (f'~{seat["person_id"]}', seat['person_id']))
    for seat, row in changes:
        guest, group = row['guest'], row.get('group') or None
        contact = anchor[group] if group else guest
        pid = seat['person_id']
        db.execute('UPDATE people SET display_name=?, dietary_notes=? WHERE person_id=?',
                   (guest, row.get('dietary') or None, pid))
        db.execute('UPDATE event_guests SET real_world_group=?, booking_contact_name=? WHERE event_id=? AND person_id=?',
                   (group, contact, EVENT, pid))
        db.execute('UPDATE seat_assignments SET guest_name=?, real_world_group=?, booking_contact_name=? '
                   'WHERE plan_id=? AND person_id=?', (guest, group, contact, PLAN, pid))
        if seat['character_name'] == 'Helicopter Pilot':
            db.execute('UPDATE children SET child_name=? WHERE person_id=?', (guest, pid))


def main():
    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--db', type=Path, default=root / 'data/valemeridian-event.sqlite')
    sub = ap.add_subparsers(dest='command', required=True)
    e = sub.add_parser('export'); e.add_argument('--out', type=Path, default=Path('roster.csv'))
    i = sub.add_parser('import'); i.add_argument('file', type=Path); i.add_argument('--apply', action='store_true')
    args = ap.parse_args()

    db = sqlite3.connect(args.db)
    db.row_factory = sqlite3.Row
    if args.command == 'export':
        export(args, db); db.close(); return

    problems, changes = plan_changes(db, read(args.file))
    if problems:
        db.close(); print('BLOCKED:', *problems, sep='\n  '); sys.exit(1)
    # Groups (couples, families, work parties) should sit at one table. Report any that do not.
    tables_of = {}
    for seat, row in changes:
        if row.get('group'):
            tables_of.setdefault(row['group'], set()).add(seat['table_number'])
    split = {g: sorted(t) for g, t in tables_of.items() if len(t) > 1}
    sizes = {g: sum(1 for _, r in changes if r.get('group') == g) for g in tables_of}
    moved = [(s, r) for s, r in changes if s['guest_name'] != r['guest']]
    for seat, row in moved[:60]:
        print(f"  table {seat['table_number']} seat {seat['seat_number']:>2} {seat['character_name']:<28} {seat['guest_name']} -> {row['guest']}")
    if len(moved) > 60:
        print(f'  ... and {len(moved) - 60} more')
    print(f'\n{len(changes)} seats read; {len(moved)} guest names change.')
    if tables_of:
        kept = len(tables_of) - len(split)
        print(f'Groups: {len(tables_of)} ({sum(sizes.values())} guests); {kept} sit together at one table.')
        for g, t in sorted(split.items()):
            members = [r['guest'] for _, r in changes if r.get('group') == g]
            print(f"  split: group {g} ({', '.join(members)}) is at tables {', '.join(map(str, t))}")
    if not args.apply:
        db.close(); print('Preview only. Re-run with --apply to write.'); return

    backup = args.db.parent / 'backups' / f'valemeridian-event-before-roster-{date.today()}.sqlite'
    db.close()
    backup.parent.mkdir(parents=True, exist_ok=True)
    if not backup.exists():
        shutil.copy2(args.db, backup)
    print(f'before-database: {backup}')
    db = sqlite3.connect(args.db)
    try:
        with db:
            apply_changes(db, changes)
        check = {r[0]: r[1] for r in db.execute('SELECT person_id, display_name FROM people')}
        wrong = [s['person_id'] for s, r in changes if check.get(s['person_id']) != r['guest']]
        if wrong:
            print('VERIFY FAILED for', ', '.join(wrong)); sys.exit(1)
        print(f'verified: {len(changes)} guests recorded. Now refresh the Print Studio: '
              '(cd print-studio && npm run snapshot)')
    finally:
        db.close()


if __name__ == '__main__':
    main()
