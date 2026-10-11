"""Record handshake verdicts after a person has read the items.

Lists the current items that are unread or changed since their last review (see
handshake_items.py). With --apply it records them: every listed item gets the
--default verdict unless a --verdict rule matches its key prefix.

  python3 scripts/record_handshake_reviews.py
  python3 scripts/record_handshake_reviews.py --plan pass7-... --default ok \\
      --verdict "exchange|CLUE_R3_DAKOTA_01|Veronica Vane=by_design:reason" --apply

Only record what has actually been read. The review script reports anything recorded
as 'gap' until the text changes and it is read again.
"""
from __future__ import annotations
import argparse, shutil, sqlite3, sys
from datetime import date, datetime, timezone
from pathlib import Path

from handshake_items import REGISTRY_SQL, compare, current_items


def main():
    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--db', type=Path, default=root / 'data/valemeridian-event.sqlite')
    ap.add_argument('--plan', help='review round these verdicts belong to')
    ap.add_argument('--default', choices=['ok', 'gap', 'by_design'])
    ap.add_argument('--note', default='')
    ap.add_argument('--verdict', action='append', default=[],
                    help='KEY_PREFIX=VERDICT[:note]; first matching rule wins')
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()

    db = sqlite3.connect(f'file:{args.db}?mode=ro', uri=True)
    items = current_items(db)
    state = compare(db, items)
    # A deliberate exception survives a re-read: --default never downgrades a recorded
    # by_design verdict (an explicit --verdict rule still can).
    have = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='local_handshake_reviews'").fetchone()
    by_design = {} if not have else dict(db.execute(
        "SELECT item_key, note FROM local_handshake_reviews WHERE verdict='by_design'"))
    db.close()
    todo = state['unread'] + state['changed']
    print(f"{len(items)} handshake items: {len(state['reviewed'])} reviewed ok, {len(state['by_design'])} by design, "
          f"{len(state['gaps'])} open gaps, {len(state['unread'])} unread, {len(state['changed'])} changed since review")
    rules = []
    for v in args.verdict:
        prefix, _, rest = v.partition('=')
        verdict, _, note = rest.partition(':')
        if verdict not in ('ok', 'gap', 'by_design'):
            raise SystemExit(f'bad verdict in {v!r}')
        rules.append((prefix, verdict, note))
    plan = []
    for it in todo:
        rule = next((r for r in rules if it['key'].startswith(r[0])), None)
        verdict, note = (rule[1], rule[2]) if rule else (args.default, args.note)
        if not rule and it['key'] in by_design:
            verdict, note = 'by_design', by_design[it['key']]
        if verdict is None:
            print(f"  unread: {it['key']}")
            continue
        plan.append((it, verdict, note))
    unused = [r[0] for r in rules if not any(it['key'].startswith(r[0]) for it in todo)]
    if unused:
        raise SystemExit(f'rules matched nothing: {unused}')
    if not args.apply:
        from collections import Counter
        print('would record:', dict(Counter(v for _, v, _ in plan)) or 'nothing')
        print('Preview only. Re-run with --apply (and --plan) to write.'); return
    if not args.plan:
        raise SystemExit('--plan is required with --apply')

    bk = root / 'data/backups' / f'valemeridian-event-before-handshake-reviews-{args.plan}.sqlite'
    bk.parent.mkdir(parents=True, exist_ok=True)
    if bk.exists():
        raise SystemExit(f'Backup exists: {bk}')
    shutil.copy2(args.db, bk); print(f'before-database: {bk}')
    now = datetime.now(timezone.utc).isoformat(timespec='seconds')
    db = sqlite3.connect(args.db)
    try:
        with db:
            db.execute(REGISTRY_SQL)
            for it, verdict, note in plan:
                db.execute('INSERT OR REPLACE INTO local_handshake_reviews VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                           (it['key'], it['kind'], it['clue_id'], it['subject'], it['round'],
                            it['source_sha'], it['subject_sha'], verdict, note or None, args.plan, now))
        after = compare(db, current_items(db))
        if after['unread'] or after['changed']:
            print('VERIFY FAILED: items still unread after recording'); sys.exit(1)
        print(f"verified: {len(plan)} verdicts recorded; {len(after['gaps'])} open gaps, "
              f"{len(after['by_design'])} by design, {len(after['reviewed'])} ok")
    finally:
        db.close()


if __name__ == '__main__':
    main()
