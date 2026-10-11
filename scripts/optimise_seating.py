"""Suggest which characters should share a table.

The clue network says who is sent to whom. Characters who talk to each other most are best seated
together, so most conversations are a few words across a table instead of a walk across the room.
This runs a simulated-annealing search over the active clue cards in the database and prints the
tables it finds, with how much of the network each table keeps.

It only reads the database and changes nothing. The shipped plan (data/valemeridian-event.sqlite)
is already a good arrangement for 8 tables and 54 seats; use this when your room needs a different
number or size of tables.

  python3 scripts/optimise_seating.py                        8 tables of up to 7
  python3 scripts/optimise_seating.py --tables 6 --size 9
  python3 scripts/optimise_seating.py --fix "Vincent Vale=1"  pin a character to a table
  python3 scripts/optimise_seating.py --apart "Veronica Vane,Dakota Steele"

Characters pinned or kept apart are named exactly as in the database. Use --seed for a repeatable
result and --time to spend longer searching.
"""
from __future__ import annotations
import argparse
from pathlib import Path

from graph_builder import build_interaction_graph, load_local_clue_data
import seating_optimiser as so


def main():
    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--db', type=Path, default=root / 'data/valemeridian-event.sqlite')
    ap.add_argument('--tables', type=int, default=8, help='number of tables (default 8)')
    ap.add_argument('--size', type=int, default=7, help='seats per table (default 7)')
    ap.add_argument('--fix', action='append', default=[], metavar='NAME=TABLE', help='pin a character to a table')
    ap.add_argument('--apart', action='append', default=[], metavar='A,B', help='keep two characters at different tables')
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--time', type=float, default=20.0, help='seconds to search (default 20)')
    args = ap.parse_args()

    data = load_local_clue_data(args.db)
    graph = build_interaction_graph(data)
    # seating_optimiser works on an adjacency map keyed by sorted character pairs.
    graph['_adj'] = {so._edge_key(e['a'], e['b']): e['weight'] for e in graph['edges']}
    graph['unresolved_target_names'] = data['unresolved_target_names']
    fixed = {}
    for spec in args.fix:
        name, _, table = spec.rpartition('=')
        fixed[name] = int(table)
    apart = [pair.split(',') for pair in args.apart]

    result = so.optimise(graph, table_size=args.size, num_tables=args.tables, fixed_seats=fixed or None,
                         forbidden_pairs=apart or None, seed=args.seed, time_limit_s=args.time)
    print(f"{len(graph['nodes'])} characters in the clue network, {len(graph['edges'])} pairs, "
          f"{graph['total_weight']} pair-round conversations.")
    print(f"Kept at a table: {result['total_in_table_weight']} of {result['total_possible_weight']} "
          f"({result['capture_rate_pct']:.1f}%).\n")
    for table in result['tables']:
        print(f"Table {table['table_number']} ({len(table['guests'])} seats, {table['in_table_weight']} kept): "
              + ', '.join(table['guests']))
    if result.get('unresolved_target_names'):
        print('\nNames on cards that match no character:', ', '.join(result['unresolved_target_names']))


if __name__ == '__main__':
    main()
