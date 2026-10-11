"""Write the readable story documents from the event database.

The database is the source of truth for every card. This script renders it as Markdown so the
whole cast can be read, proofread and searched without opening SQLite. It reads the database and
writes three files in story/:

  cards.md            every character with their pre-party briefing and every card, round by round
  conversation-map.md who each card sends its player to, round by round
  photo-briefs.md     what each of the eleven pictures must show (from local_evidence_photos)

Re-run it after editing cards, then commit the result:  python3 scripts/export_story_reader.py
The files are host and editor references. They contain the solution; guests must not see them.
"""
from __future__ import annotations
import argparse, re, sqlite3
from collections import defaultdict
from pathlib import Path

ROUND_TITLE = {0: 'Round 0 (arrival)', 1: 'Round 1', 2: 'Round 2', 3: 'Round 3', 4: 'Round 4 (closing)'}


def round_label(value):
    return 'Toast cue (private)' if value is None else ROUND_TITLE.get(value, f'Round {value}')


def sort_key(name):
    return re.sub(r'[^a-z0-9 ]', '', name.lower())


def main():
    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--db', type=Path, default=root / 'data/valemeridian-event.sqlite')
    ap.add_argument('--out', type=Path, default=root / 'story')
    args = ap.parse_args()

    db = sqlite3.connect(args.db.as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    characters = {r['character_id']: dict(r) for r in db.execute('SELECT * FROM characters')}
    kinds = {r['clue_id']: r['record_kind'] for r in db.execute('SELECT clue_id, record_kind FROM local_clue_record_kinds')}
    targets = defaultdict(list)
    for r in db.execute('SELECT clue_id, target_name FROM clue_targets ORDER BY clue_id, target_order'):
        targets[r['clue_id']].append(r['target_name'])
    seat = {r['character_name']: r['table_number'] for r in db.execute(
        "SELECT character_name, table_number FROM seat_assignments WHERE plan_id IN "
        "(SELECT plan_id FROM seating_plans WHERE status='approved')")}
    # One performer plays both Vale twins, and the Game Master sits as the Family Solicitor.
    for alias, seated in [('Vincent Vale', 'Vincent Vale / Peter Vale'), ('Peter Vale', 'Vincent Vale / Peter Vale'),
                          ('Game Master', 'Family Solicitor')]:
        if seated in seat:
            seat[alias] = seat[seated]
    clues = [dict(r) for r in db.execute(
        "SELECT * FROM clues WHERE status='active' ORDER BY COALESCE(round, 0), clue_id")]

    by_character = defaultdict(list)
    for c in clues:
        by_character[c['character_id']].append(c)

    lines = [
        '# Every card, by character', '',
        'Generated from the event database by `scripts/export_story_reader.py`; do not edit by hand. '
        '**Contains the solution: host and editor reference only.**', '',
        f'{len(clues)} active clue records for {len(by_character)} characters. Headings and the '
        '"Sends them to" lines are for the reader; they are not printed on guest cards. '
        'Cards marked *private* are handed to one person only (performers and the Game Master); '
        'cards marked *evidence* are shared exhibits.', '',
    ]
    for cid in sorted(by_character, key=lambda k: sort_key(characters[k]['character_name'] if k in characters else k)):
        ch = characters.get(cid, {})
        name = ch.get('character_name') or by_character[cid][0]['character_name']
        meta = ' · '.join(x for x in [ch.get('character_type'), ch.get('assigned_subplot'),
                                      f"table {seat[name]}" if name in seat else None] if x)
        lines += [f'## {name}', '', f'*{meta}*' if meta else '', '']
        if ch.get('description'):
            lines += ['**Pre-party briefing**', ''] + ['> ' + p if p else '>' for p in ch['description'].split('\n')] + ['']
        if ch.get('secret'):
            lines += ['**Secret**', '', '> ' + ch['secret'].replace('\n', '\n> '), '']
        for c in by_character[cid]:
            kind = kinds.get(c['clue_id'], 'ordinary')
            tag = {'ordinary': '', 'performance': ' · *private*', 'facilitation': ' · *private*', 'artifact': ' · *evidence*'}.get(kind, f' · {kind}')
            lines += [f"### {round_label(c['round'])} — {c['clue_title']}", '', f"`{c['clue_id']}`{tag}", '',
                      c['clue_content'].strip(), '']
            if targets.get(c['clue_id']):
                lines += ['*Sends them to:* ' + ', '.join(targets[c['clue_id']]), '']
    args.out.mkdir(exist_ok=True)
    (args.out / 'cards.md').write_text('\n'.join(lines).rstrip() + '\n')

    # Conversation map
    rounds = defaultdict(list)
    for c in clues:
        if targets.get(c['clue_id']):
            rounds[c['round'] if c['round'] is not None else 0].append(c)
    out = ['# Conversation map', '',
           'Generated by `scripts/export_story_reader.py`. Each row is a card that sends its player to '
           'someone else: who, to whom, which card. Tables are those of the sample seating plan; a '
           'cross-table row is one that needs a walk or a question note.', '']
    total = 0
    for rnd in sorted(rounds):
        rows = sorted(rounds[rnd], key=lambda c: (c['character_name'].lower(), c['clue_id']))
        out += [f'## {round_label(rnd)}', '', '| From | To | Card | Table |', '|---|---|---|---|']
        for c in rows:
            for t in targets[c['clue_id']]:
                a, b = seat.get(c['character_name']), seat.get(t)
                where = '' if a is None or b is None else (f'{a}' if a == b else f'{a} → {b}')
                out.append(f"| {c['character_name']} | {t} | `{c['clue_id']}` | {where} |")
                total += 1
        out.append('')
    out.insert(3, f'{total} directions in all.')
    out.insert(4, '')
    (args.out / 'conversation-map.md').write_text('\n'.join(out).rstrip() + '\n')
    # Photograph briefs
    photos = [dict(r) for r in db.execute(
        "SELECT * FROM local_evidence_photos WHERE status='active' ORDER BY round, photo_id")]
    brief = ['# Picture briefs', '',
             'Generated by `scripts/export_story_reader.py` from the `local_evidence_photos` table. Each entry says '
             'what one picture must show so it works in the game. Each is written as a prompt: paste it into an AI image tool such as ChatGPT (the original pictures were made this way), with Claude or another assistant to adapt it to your cast and refine the result, then save the picture '
             'in `data/artwork/` under the file name given, and run `npm run photos` in `print-studio/`. '
             'See [../docs/evidence-photos.md](../docs/evidence-photos.md) for the rules that apply to the whole set.', '']
    for ph in photos:
        brief += [f"## {ph['title']}", '',
                  f"- **File:** `data/artwork/{ph['source_file']}` (about {ph['pixel_width']} × {ph['pixel_height']} px)",
                  f"- **Id:** `{ph['photo_id']}` · **Round:** {ph['round']} · **Held by:** {ph['holder_character']} · "
                  f"**Prints:** {ph['copies']}" + (' · **private**' if ph['private'] else ''),
                  f"- **Caption printed with it:** {ph['caption']}",
                  f"- **When:** {ph['cue'] or 'with its round'}", '', ph['description'], '']
    (args.out / 'photo-briefs.md').write_text('\n'.join(brief).rstrip() + '\n')
    print(f'Wrote {args.out / "cards.md"} ({len(clues)} cards), conversation-map.md ({total} directions) and photo-briefs.md ({len(photos)} pictures).')


if __name__ == '__main__':
    main()
