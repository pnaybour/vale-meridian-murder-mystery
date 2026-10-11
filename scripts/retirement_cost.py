"""What would it cost to run the evening with fewer players?

Every character you retire takes their cards with them, and every other card that sends a player
to them, or names them, has to be edited. This tool counts those edits so you can choose whom
to retire. It only reads the database.

  python3 scripts/retirement_cost.py                       cheapest characters to retire first
  python3 scripts/retirement_cost.py --count 6             a suggested set of six, and what it costs
  python3 scripts/retirement_cost.py --remove "Cassette Carl,Wendy Woke"
                                                           the exact cards to edit for those two

It will not suggest the performers (Vincent/Peter, DJ Spinny T, Inspector Donna Reed, Veronica
Vane, Leo Lights, Wanda Wires, Scooter, Dakota Steele, Vance Vellum), and it never suggests a set
that leaves a case pillar with nobody who can supply it (see the seven pillars in
story/solution-and-canon.md). The counts are the *network* cost. They do not capture a character's
part in a story arc (two characters who are a couple, say), so read the cards of anyone you retire.
"""
from __future__ import annotations
import argparse, sqlite3
from collections import defaultdict
from pathlib import Path

import handshake_items as hi
from review_current_social_graph import CASE_PILLARS

PERFORMERS = {'Vincent Vale', 'Peter Vale', 'Vincent Vale / Peter Vale', 'DJ Spinny T', 'Leo Lights',
              'Wanda Wires', 'Scooter', 'Dakota Steele', 'Vance Vellum', 'Inspector Donna Reed',
              'Veronica Vane', 'Game Master', 'Family Solicitor'}


def main():
    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--db', type=Path, default=root / 'data/valemeridian-event.sqlite')
    ap.add_argument('--count', type=int, help='suggest this many characters to retire')
    ap.add_argument('--remove', help='comma-separated characters: list the cards to edit')
    args = ap.parse_args()

    db = sqlite3.connect(args.db.as_uri() + '?mode=ro', uri=True)
    items = [i for i in hi.current_items(db) if i['kind'] in ('exchange', 'mention')]
    seat = {r[0]: r[1] for r in db.execute('SELECT character_name, table_number FROM seat_assignments')}
    chars = sorted({r[0] for r in db.execute(
        "SELECT DISTINCT character_name FROM clues WHERE status='active' AND character_name IS NOT NULL")})
    pillars = {key: set(owners) for key, _, owners in CASE_PILLARS}

    def edits(removed):
        """Cards that stay in the game but name, or send a player to, a retired character."""
        found = defaultdict(list)
        for i in items:
            if i['subject'] in removed and i['owner'] not in removed:
                found[i['clue_id']].append(i)
        return found

    def safe(removed):
        return all(owners - removed for owners in pillars.values())

    candidates = [c for c in chars if c not in PERFORMERS]

    if args.remove:
        removed = {n.strip() for n in args.remove.split(',') if n.strip()}
        unknown = removed - set(chars)
        if unknown:
            raise SystemExit(f'No active character called: {", ".join(sorted(unknown))}')
        owned = db.execute(
            f"SELECT count(*) FROM clues WHERE status='active' AND character_name IN ({','.join('?' * len(removed))})",
            tuple(removed)).fetchone()[0]
        found = edits(removed)
        lost = [k for k, owners in pillars.items() if not (owners - removed)]
        print(f'Retiring {len(removed)}: {", ".join(sorted(removed))}')
        print(f'  {owned} cards retire with them; {len(found)} other cards need editing')
        if performers := sorted(removed & PERFORMERS):
            print(f'  WARNING: these have parts to play: {", ".join(performers)}')
        if lost:
            print(f'  WARNING: nobody left to supply the pillar(s): {", ".join(lost)}')
        for clue_id in sorted(found):
            first = found[clue_id][0]
            what = sorted({f"{i['kind']} of {i['subject']}" for i in found[clue_id]})
            print(f"  edit {clue_id} ({first['owner']}, round {first['round']}): {'; '.join(what)}")
        for name in sorted(removed):
            print(f"  free the seat: table {seat.get(name, '?')}, {name}")
        return

    if args.count:
        removed, steps = set(), []
        for _ in range(args.count):
            best = None
            for c in candidates:
                if c in removed or not safe(removed | {c}):
                    continue
                cost = len(edits(removed | {c}))
                if best is None or cost < best[0]:
                    best = (cost, c)
            if not best:
                break
            removed.add(best[1])
            steps.append((best[1], best[0]))
        print(f'A suggested {len(removed)}, in the order to retire them, and the cards needing edits after each:')
        for n, (name, cost) in enumerate(steps, 1):
            print(f'  {n:>2}. {name:<28} table {seat.get(name, "?")}   {cost} cards to edit so far')
        print('\nDetails for this set: python3 scripts/retirement_cost.py --remove "' + ', '.join(sorted(removed)) + '"')
        return

    rows = sorted((len(edits({c})), c) for c in candidates if safe({c}))
    print('Cheapest characters to retire, one at a time (cards that would need editing):\n')
    for cost, name in rows[:15]:
        print(f'  {cost:>3}  {name:<28} table {seat.get(name, "?")}')
    print(f'\n  ... {len(rows) - 15} more. Performers are never listed.')


if __name__ == '__main__':
    main()
