"""Verify the actual exported PDF, not merely the input data."""
import json
import sys
from pathlib import Path
from pypdf import PdfReader
import pdfplumber

root=Path(__file__).resolve().parents[1]
pdf=Path(sys.argv[1]) if len(sys.argv)>1 else root/'output/valemeridian-complete-proof.pdf'
reader=PdfReader(pdf)
page_text=[''.join((p.extract_text() or '').split()) for p in reader.pages]
master=json.loads((root/'source/master-clues.json').read_text())['data']
for item in master:
    content=''.join(item['clue_content'].split())
    assert any(content in page for page in page_text), f"Missing or altered PDF text: {item['clueid']}"
with pdfplumber.open(pdf) as document:
    for number,page in enumerate(document.pages,1):
        for char in page.chars:
            assert char['x0'] >= 0 and char['x1'] <= page.width+0.5, f'Horizontal overflow on page {number}'
            assert char['top'] >= 0 and char['bottom'] <= page.height+0.5, f'Vertical overflow on page {number}'
assert len(reader.pages)>0
print(f'All {len(master)} master clue texts preserved in PDF; {len(reader.pages)} pages within A4 boundaries.')
