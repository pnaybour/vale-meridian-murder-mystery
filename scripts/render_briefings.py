"""Write one pre-party briefing per guest, from the email template and the database.

Each guest gets an HTML file with their character, the briefing, the dress guidance, and (if the
database has one) their menu. Nothing is sent: open the files, check them, and paste or attach
them into whatever you use to email your guests. The Game Master and the child's cameo role have
no briefing, and the performer who plays both Vale twins gets Vincent's, which mostly describes
Vincent (Peter's longer biography arrives on his first Peter card).

  python3 scripts/render_briefings.py                 writes briefings/<guest>.html
  python3 scripts/render_briefings.py --out my-mail   a different folder
  python3 scripts/render_briefings.py --only "Guest 07"

The template is templates/character-briefing-email.html. It uses {{name}}, {{character_name}},
{{character_description_html}}, {{starter}}, {{main}}, {{dessert}}, {{dietary_requirements}},
{{occasion}} and {{host_names}}. The last two come from data/event.json. A block between
<!-- MENU --> and <!-- /MENU --> is dropped when a guest has no menu.

A briefing must not say who will die or when. Any briefing that uses a word like "death",
"murder", "poison" or "collapsed" is listed as a warning so you can check it before it is sent.
"""
from __future__ import annotations
import argparse, html, json, re, sqlite3
from pathlib import Path


def paragraphs(text):
    """Briefing text as HTML paragraphs, with the two labelled lines in bold."""
    out = []
    for block in re.split(r'\n\s*\n', (text or '').strip()):
        block = block.strip()
        if not block:
            continue
        safe = html.escape(block).replace('\n', '<br>')
        safe = re.sub(r'^(Private Objective:|Dress guidance:)', r'<strong>\1</strong>', safe)
        out.append(f'<p style="margin:0 0 14px 0;">{safe}</p>')
    return '\n'.join(out)


# Words that would give away the murder. A match is a prompt to read the sentence, not an error:
# a character may legitimately mention a poisoned reputation, say.
SPOILER = re.compile(r"\b(death|dead|died|dies|murder\w*|poison\w*|kill\w*|corpse|collapsed)\b", re.I)


def spoilers(text):
    return [m.group(0).strip() for m in re.finditer(r"[^.!?]*" + SPOILER.pattern + r"[^.!?]*[.!?]?", text or "", re.I)]


def slug(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-') or 'guest'


def main():
    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--db', type=Path, default=root / 'data/valemeridian-event.sqlite')
    ap.add_argument('--out', type=Path, default=root / 'briefings')
    ap.add_argument('--only', help='only this guest, by name')
    args = ap.parse_args()

    event = json.loads((root / 'data/event.json').read_text())
    template = (root / 'templates/character-briefing-email.html').read_text()
    db = sqlite3.connect(args.db.as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    rows = db.execute(
        'SELECT p.person_id, p.display_name, p.dietary_notes, ca.character_name, ch.description, '
        'mo.starter, mo.main, mo.dessert '
        'FROM character_assignments ca '
        'JOIN people p ON p.person_id = ca.person_id '
        'JOIN characters ch ON ch.character_id = ca.character_id '
        'LEFT JOIN menu_orders mo ON mo.person_id = ca.person_id '
        "WHERE ca.game_master = 0 AND ch.status = 'active' ORDER BY p.person_id").fetchall()
    args.out.mkdir(parents=True, exist_ok=True)
    count = 0
    warnings = []
    for r in rows:
        if args.only and r['display_name'] != args.only:
            continue
        warnings += [f"{r['display_name']} ({r['character_name']}): {line}" for line in spoilers(r['description'])]
        has_menu = any(r[k] for k in ('starter', 'main', 'dessert'))
        page = template
        page = re.sub(r'\s*<!-- MENU -->.*?<!-- /MENU -->', '' if not has_menu else
                      lambda m: re.sub(r'<!-- /?MENU -->\s*', '', m.group(0)), page, flags=re.S)
        fields = {
            'name': html.escape(r['display_name']),
            'character_name': html.escape(r['character_name']),
            'character_description_html': paragraphs(r['description']),
            'starter': html.escape(r['starter'] or ''), 'main': html.escape(r['main'] or ''),
            'dessert': html.escape(r['dessert'] or ''),
            'dietary_requirements': html.escape(r['dietary_notes'] or 'None'),
            'occasion': html.escape(event['hosts']), 'host_names': html.escape(event.get('hostNames', event['hosts'])),
        }
        for key, value in fields.items():
            page = page.replace('{{' + key + '}}', value)
        left = re.findall(r'\{\{[a-z_]+\}\}', page)
        if left:
            raise SystemExit(f'Unfilled placeholders in the template: {sorted(set(left))}')
        (args.out / f"{slug(r['display_name'])}.html").write_text(page)
        count += 1
    print(f'Wrote {count} briefings to {args.out}')
    if warnings:
        print('\nCheck before sending: these briefings may mention the murder in advance:')
        print(*warnings, sep='\n')


if __name__ == '__main__':
    main()
