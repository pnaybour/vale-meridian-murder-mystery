"""Prepare the picture props for printing.

What each photograph is lives in the database (local_evidence_photos, written by
scripts/register_evidence_photos.py). The pictures themselves are not in the repository:
put your own in data/artwork/ under the file names the database records, and run this script.
Where a picture is missing it makes a labelled placeholder instead, so the studio, the PDF
generator and the tests all work before you have any artwork. The placeholder carries the
photograph's brief, so it doubles as a prompt for the picture you need.

  public/evidence/<id>.jpg   a screen copy for the proof panel
  lib/photos.json            the same picture as a data URL, for the PDF (loaded only when
                             a print pack is generated)

  python3 scripts/build_photos.py               rebuild every picture
  python3 scripts/build_photos.py --if-missing  only when lib/photos.json does not exist yet

Needs Pillow (pip install pillow). Re-run after changing artwork or the database.
"""
from __future__ import annotations
import base64, io, json, sqlite3, sys, textwrap
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover
    Image = None

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parent
ART = ROOT / 'data/artwork'
OUT = APP / 'public/evidence'
MAX_PIXELS = 1200          # 1200 px across a 100 mm print is about 300 dpi
CREAM, BURGUNDY, INK, MUTED = '#f4ecdd', '#732b40', '#242326', '#6a5960'
# Props that are pictures but not evidence photographs: id, original (or None), longest side in pixels.
# The prop money prints 130 mm wide, so it keeps its full size (about 360 dpi). With no original
# artwork a plain banknote is drawn.
EXTRAS = [('prop-money', 'valemeridian-prop-money.png', 1836),
          ('art-lab-report', 'valemeridian-lab-report.png', 2000)]


def fonts():
    data = json.loads((APP / 'lib/fonts.json').read_text())
    def load(style, size):
        return ImageFont.truetype(io.BytesIO(base64.b64decode(data[style])), size)
    return load


def photographs():
    db = sqlite3.connect((ROOT / 'data/valemeridian-event.sqlite').as_uri() + '?mode=ro', uri=True)
    try:
        if not db.execute("select 1 from sqlite_master where type='table' and name='local_evidence_photos'").fetchone():
            return []
        return [dict(photo_id=r[0], source_file=r[1], title=r[2], round=r[3], description=r[4],
                     width=r[5], height=r[6]) for r in db.execute(
            "select photo_id, source_file, title, round, description, pixel_width, pixel_height "
            "from local_evidence_photos where status='active' order by round, photo_id")]
    finally:
        db.close()


def scaled(width, height, longest):
    k = longest / max(width, height)
    return max(1, round(width * k)), max(1, round(height * k))


def placeholder(photo, load):
    """A cream card with the picture's id, title and brief, to be replaced by real artwork."""
    w, h = scaled(photo['width'], photo['height'], MAX_PIXELS)
    img = Image.new('RGB', (w, h), CREAM)
    d = ImageDraw.Draw(img)
    pad = round(min(w, h) * 0.05)
    d.rectangle([pad, pad, w - pad, h - pad], outline=BURGUNDY, width=max(2, w // 300))
    d.line([pad, pad, w - pad, h - pad], fill='#e2d6c2', width=max(1, w // 400))
    d.line([pad, h - pad, w - pad, pad], fill='#e2d6c2', width=max(1, w // 400))
    y = pad * 2
    inner = w - pad * 4
    for text, style, size, colour in [('PICTURE PLACEHOLDER', 'bold', round(min(w, h) / 17), BURGUNDY),
                                      (photo['title'], 'bold', round(min(w, h) / 21), INK),
                                      (f"{photo['photo_id']}  ·  Round {photo['round']}", 'normal', round(min(w, h) / 28), MUTED)]:
        font = load(style, size)
        while font.getlength(text) > inner and size > 8:
            size -= 1
            font = load(style, size)
        d.text((pad * 2, y), text, font=font, fill=colour)
        y += round(size * 1.5)
    y += pad // 2
    size = round(min(w, h) / 32)
    brief = load('normal', size)
    chars = max(20, int(inner / (size * 0.5)))
    for line in textwrap.wrap(photo['description'], chars)[:16]:
        d.text((pad * 2, y), line, font=brief, fill=INK)
        y += round(size * 1.35)
    foot = load('normal', round(min(w, h) / 38))
    d.text((pad * 2, h - pad * 2 - round(min(w, h) / 38)), 'Add your own picture: see docs/evidence-photos.md', font=foot, fill=MUTED)
    return img


def banknote(width, height, load):
    """A plain prop banknote (no portrait, no venue) when there is no original artwork."""
    img = Image.new('RGB', (width, height), CREAM)
    d = ImageDraw.Draw(img)
    b = round(width * 0.012)
    d.rectangle([b, b, width - b, height - b], outline=BURGUNDY, width=round(b * 0.8))
    d.rectangle([b * 3, b * 3, width - b * 3, height - b * 3], outline=BURGUNDY, width=max(2, b // 3))
    r = round(height * 0.11)
    for cx, cy in [(r * 2, r * 2), (width - r * 2, r * 2), (r * 2, height - r * 2), (width - r * 2, height - r * 2)]:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=BURGUNDY)
        d.text((cx, cy), '1000', font=load('bold', round(r * 0.8)), fill=CREAM, anchor='mm')
    logo = APP / 'public/valemeridian-logo.png'
    if logo.exists():
        mark = Image.open(logo).convert('RGBA')
        k = (width * 0.5) / mark.width
        mark = mark.resize((round(mark.width * k), round(mark.height * k)))
        img.paste(mark, ((width - mark.width) // 2, round(height * 0.17)), mark)
    d.text((width // 2, round(height * 0.52)), 'A NIGHT OF GLAMOUR & HIDDEN TRUTHS', font=load('bold', round(height * 0.05)), fill=INK, anchor='mm')
    d.text((width // 2, round(height * 0.66)), 'ONE THOUSAND GLAMOUR POUNDS', font=load('bold', round(height * 0.09)), fill=BURGUNDY, anchor='mm')
    d.text((width // 2, round(height * 0.84)), 'VV-1986-000000   ·   NOT LEGAL TENDER   ·   PROP ONLY', font=load('normal', round(height * 0.04)), fill=MUTED, anchor='mm')
    return img


def save(img, path, quality):
    img.convert('RGB').save(path, 'JPEG', quality=quality, optimize=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(path.read_bytes()).decode()


def main():
    if '--if-missing' in sys.argv and (APP / 'lib/photos.json').exists():
        return
    if Image is None:
        print('Pillow is needed to prepare pictures: pip install pillow')
        sys.exit(0 if '--if-missing' in sys.argv else 1)
    load = fonts()
    OUT.mkdir(parents=True, exist_ok=True)
    for stale in OUT.glob('*.jpg'):
        stale.unlink()
    photos = photographs()
    data_urls, made = {}, []
    for photo in photos:
        jpg = OUT / f"{photo['photo_id']}.jpg"
        source = ART / photo['source_file']
        if source.exists():
            img = Image.open(source)
            img.thumbnail((MAX_PIXELS, MAX_PIXELS))
        else:
            img = placeholder(photo, load)
            made.append(photo['photo_id'])
        data_urls[photo['photo_id']] = save(img, jpg, 80)
    for pid, name, size in EXTRAS:
        jpg = OUT / f'{pid}.jpg'
        source = ART / name
        if source.exists():
            img = Image.open(source)
            img.thumbnail((size, size))
        elif pid == 'prop-money':
            img = banknote(1836, 857, load)
            made.append(pid)
        else:
            continue
        data_urls[pid] = save(img, jpg, 92)
    (APP / 'lib/photos.json').write_text(json.dumps(data_urls) + '\n')
    total = sum(len(v) for v in data_urls.values()) / 1e6
    print(f'{len(data_urls)} pictures prepared in {OUT} and lib/photos.json ({total:.1f} MB)')
    if made:
        print('placeholders made for:', ', '.join(made), '(put originals in data/artwork/ to replace them)')


if __name__ == '__main__':
    main()
