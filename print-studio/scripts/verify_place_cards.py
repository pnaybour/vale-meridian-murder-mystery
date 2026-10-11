"""Check the rendered reverse text against each card's trim and centre.

Usage: python3 scripts/verify_place_cards.py output/place-cards.pdf
Requires the matching .manifest.json emitted by the print generator.
"""
import json
import sys
from pathlib import Path

import pdfplumber

MM = 72 / 25.4
pdf = Path(sys.argv[1])
manifest = json.loads(pdf.with_suffix('.manifest.json').read_text())
cards = [p for p in manifest['placements'] if p['template'] == 'place']
assert cards, 'No place cards to verify'
brand = manifest.get('brand', {}).get('name', 'VALE MERIDIAN')
checked = set()
centred_lines = 0

with pdfplumber.open(pdf) as document:
    for page_number in sorted({p['page'] for p in cards}):
        page_cards = [p for p in cards if p['page'] == page_number]
        runs = []
        previous = None
        for char in document.pages[page_number - 1].chars:
            if char['matrix'][0] > -0.99 or char['matrix'][3] > -0.99:
                previous = None
                continue
            if (previous is None
                    or abs(char['matrix'][5] - previous['matrix'][5]) > 0.1
                    or char['fontname'] != previous['fontname']
                    or char['x0'] >= previous['x0']):
                runs.append([])
            runs[-1].append(char)
            previous = char

        for run in runs:
            label = ''.join(c['text'] for c in run)
            x0, x1 = min(c['x0'] for c in run), max(c['x1'] for c in run)
            top, bottom = min(c['top'] for c in run), max(c['bottom'] for c in run)
            containing = [p for p in page_cards
                          if (p['x'] + 4) * MM <= x0
                          and x1 <= (p['x'] + p['width'] - 4) * MM
                          and (p['y'] + 2) * MM <= top
                          and bottom <= (p['y'] + 39) * MM]
            assert len(containing) == 1, (
                f'Page {page_number}: reverse line outside its card: {label!r}'
            )
            card = containing[0]
            checked.add((card['id'], card['copy']))
            # Embedded fonts share a PDF name. The 6.2 pt menu lines are
            # centred; the 4.5 pt dietary lines remain left aligned.
            if abs(run[0]['size'] - 6.2) < 0.05 or label == brand:
                centre = (card['x'] + card['width'] / 2) * MM
                assert abs((x0 + x1) / 2 - centre) < 0.3 * MM, (
                    f'Page {page_number}: reverse line is off centre: {label!r}'
                )
                centred_lines += 1

assert len(checked) == len(cards), 'A place card is missing its reverse text'
print(f'All {len(cards)} place cards: reverse text inside trim margins; '
      f'{centred_lines} heading/menu lines centred.')
