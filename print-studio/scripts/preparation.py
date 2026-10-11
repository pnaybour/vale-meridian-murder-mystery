"""Shared preparation content for the application and its Markdown reference."""
import json
from pathlib import Path

APP = Path(__file__).resolve().parents[1]

def load_preparation():
    return json.loads((APP / 'source/physical-preparation.json').read_text())

def render_preparation(data):
    lines = ['# Vale Meridian — physical preparation checklist',
             f"Reviewed {data['reviewedAt']}. GM copy; contains story details.",
             data['reviewBasis'], data['statusNote']]
    section = None
    for item in data['items']:
        if item['section'] != section:
            section = item['section']
            lines.append('## ' + section)
        mark = '[ ] ' if item['status'] != 'Story only' else ''
        lines.extend([f"### {mark}{item['title']} — {item['status']}",
                      f"Quantity: {item['quantity']} · Responsible: {item['owner']} · Ready: {item['when']}",
                      item['detail']])
        if item['clueIds']:
            lines.append('Clue references: ' + ', '.join(item['clueIds']))
    return '\n\n'.join(lines) + '\n'

if __name__ == '__main__':
    output = APP.parent / 'story/physical-props.md'
    output.write_text(render_preparation(load_preparation()))
    print('Updated the readable preparation checklist:', output)
