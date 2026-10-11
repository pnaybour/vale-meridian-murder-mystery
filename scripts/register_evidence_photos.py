"""Record the photographic evidence in the database.

The pictures themselves are not in the repository: put your own originals in data/artwork (see
docs/evidence-photos.md) and the print copies are generated. This table is what is kept: what each picture shows, who holds it,
when it is released, the caption that prints beneath it, and the fingerprint of the file it was
registered from, so a replaced or missing file is obvious.

  python3 scripts/register_evidence_photos.py            show what would change
  python3 scripts/register_evidence_photos.py --apply    write local_evidence_photos

print-studio/scripts/build_photos.py reads this table to make the print copies, and the
snapshot export turns it into printable entries.
"""
from __future__ import annotations
import argparse, hashlib, json, shutil, sqlite3, sys
from datetime import date, datetime, timezone
from pathlib import Path

PLAN = 'evidence-photos-2026-09-20'
ART = 'data/artwork'

SCHEMA = """CREATE TABLE IF NOT EXISTS local_evidence_photos (
  photo_id TEXT PRIMARY KEY,
  source_file TEXT NOT NULL,
  title TEXT NOT NULL,
  holder_character TEXT NOT NULL,
  round INTEGER NOT NULL,
  caption TEXT NOT NULL,
  description TEXT NOT NULL,
  print_size TEXT NOT NULL CHECK (print_size IN ('photo','document')),
  private INTEGER NOT NULL DEFAULT 0,
  cue TEXT NOT NULL DEFAULT '',
  clue_refs_json TEXT NOT NULL,
  copies INTEGER NOT NULL DEFAULT 1,
  pixel_width INTEGER,
  pixel_height INTEGER,
  file_sha TEXT,
  status TEXT NOT NULL CHECK (status IN ('active','retired')),
  plan_id TEXT NOT NULL,
  updated_at TEXT NOT NULL)"""

# photo_id, file, title, holder, round, printed caption, description for the GM, size, private, cue,
# cards it serves, how many copies to print
PHOTOS = [
 ('photo-decanter', 'decanter-frame.png', 'The decanter photograph', 'Vance Vellum', 2,
  'Vance Vellum · 10 October 1986, 19:29:10 · a woman from behind, her hand near the stopper. '
  'The frame does not show anything entering the wine.',
  "Vance's decanter frame, the single most useful picture in the game. A woman seen from behind at the private "
  "drinks table, her hand on the stopper, a filled glass beside her; her face is completely hidden and nothing "
  "is shown entering the wine, so it places somebody there without naming them. Black and white on purpose. "
  "What can be recognised is long blonde hair, a dark draped gown with a line of pearls along the shoulder, and "
  "a wide pearl cuff on the reaching wrist: enough for Nikki and Dakota to stand by their Round 3 "
  "identifications, not enough to settle it alone. The figure's hair, gown and bracelet are what the witnesses recognise, so keep them consistent with the murderer's costume, which should include a wide cuff bracelet on the right wrist. Nine copies print, so Vance can leave one at every table and "
  "keep his own. Released in Round 2 inside the pack, never on its own; Nikki and Dakota recognise the woman in Round 3.",
  'photo', 0, 'Round 2, in the pack', ['CLUE_VVL_R3', 'CLUE_NN_R3', 'CLUE178', 'CLUE_R3_DAKOTA_01'], 9),
 ('photo-lobby-signing', 'lobby-signing-1928.png', 'Signing in the lobby', 'Vance Vellum', 2,
  'Vance Vellum · written on the print: 10·10·86  7:28 pm  V.V.',
  "A young star in a pale cream suit signing an autograph in the lobby, head bent right down over the book so "
  "his face is not visible. The hidden face is deliberate: this is the only print whose subject is also a suspect, so the picture corroborates without "
  "doing the witness's job. Johnny's card is what names Robbie and places him there from 19:28 until the alarm. "
  "The time written on the border in Vance's hand also shows that he dates his frames, which matters when the "
  "decanter picture is questioned. The fan is a dark-haired woman in her fifties in red, chosen deliberately: an "
  "earlier version gave her long blonde hair and a dark dress, which inside the same pack read as the decanter "
  "woman one minute earlier and would have handed Veronica a false alibi.",
  'photo', 0, 'Round 2, in the pack', ['CLUE_VVL_R1', 'CLUE_VVL_R3', 'CLUE_RB_R3', 'CLUE147'], 9),
 ('photo-greeting', 'reception-greeting.png', 'Greetings at the door', 'Vance Vellum', 2,
  'Vance Vellum · reception',
  "Two women greeting each other at the door as a man watches from behind. One of the ordinary reception scenes "
  "Vance lists: people socialising, nothing about a recording or the decanter.",
  'photo', 0, 'Round 2, in the pack', ['CLUE_VVL_R1', 'CLUE_VVL_R3'], 9),
 ('photo-dance', 'reception-dance.png', 'A dance', 'Vance Vellum', 2,
  'Vance Vellum · reception',
  "A couple dancing in the main room. The 'dance' among Vance's reception frames.",
  'photo', 0, 'Round 2, in the pack', ['CLUE_VVL_R1', 'CLUE_VVL_R3'], 9),
 ('photo-group-toast', 'reception-group-toast.png', 'A group conversation', 'Vance Vellum', 2,
  'Vance Vellum · reception',
  "Five guests raising champagne together: the 'group conversation' in Vance's list of reception frames.",
  'photo', 0, 'Round 2, in the pack', ['CLUE_VVL_R1', 'CLUE_VVL_R3'], 9),
 ('photo-champagne', 'champagne-service.png', 'Champagne service', 'Vance Vellum', 2,
  'Vance Vellum · ordinary champagne service, separate from Vale’s private wine',
  "A waiter pouring champagne at the bar, with ice buckets and rows of glasses. This is Vance's Round 2 point in "
  "picture form: the general service was quite separate from Vale's private decanter.",
  'photo', 0, 'Round 2, in the pack', ['CLUE_VVL_R2', 'CLUE_VVL_R1', 'CLUE_VVL_R3'], 9),
 ('photo-lucien-mirror', 'lucien-luxe-mirror.png', 'Lucien Luxe beside the mirror', 'Vance Vellum', 2,
  'Vance Vellum · written on the print: 10·10·86  7:05 pm  V.V.',
  "Lucien Luxe beside the gilt mirror: navy velvet frock coat, ruffled shirt, "
  "purple scarf and one black leather glove, which is exactly the brief Lucien was given, with the room "
  "reflected behind. The time on the border is 7:05 pm, well inside the reception and long before the toast. "
  "This is a portrait rather than evidence: Vance's own to hand to Lucien, and the glove is costume, not a "
  "clue. It takes the place of the old anonymous 'Beside the mirror' frame, whose woman seen from behind in "
  "dark velvet resembled the decanter woman closely enough to start a false identification.",
  'photo', 0, 'Round 2, in the pack', ['CLUE_VVL_R1', 'CLUE_VVL_R3'], 9),
 ('photo-red-wine-pair', 'reception-red-wine-pair.png', 'A quiet word', 'Vance Vellum', 2,
  'Vance Vellum · reception',
  "A man leaning in to speak to a woman holding a glass of red wine. Useful colour for the sleeve; it is not the "
  "private decanter and should not be presented as it.",
  'photo', 0, 'Round 2, in the pack', ['CLUE_VVL_R1', 'CLUE_VVL_R3'], 9),
 ('photo-two-women', 'reception-two-women.png', 'Two guests', 'Vance Vellum', 2,
  'Vance Vellum · reception',
  "Two women laughing with champagne under the chandelier. Filler for the sleeve, so the dropped-prints moment "
  "with Nikki has something to drop.",
  'photo', 0, 'Round 2, in the pack', ['CLUE_VVL_R1', 'CLUE_VVL_R3', 'CLUE009'], 9),
 ('photo-vale-microphone', 'vale-at-the-microphone.png', 'Vincent Vale at the microphone', 'Game Master', 4,
  'For the public conclusion. Keep out of sight until Round 4.',
  "Vincent Vale in black tie at the lectern microphone, a glass of his private red wine in his hand, mid-speech: "
  "Vance's Polaroid of tonight's toast and the last photograph of Vale alive. Shot from inside the crowd at "
  "guest height, so the foreground is backs of heads and no guest in the room is identifiable — the picture "
  "cannot be mined for who was standing where. It shows Vincent Vale as the room's host. For the GM to "
  "show during the credits, step 8 of the closing sequence. Keep it out of sight until then: it shows "
  "the private wine in his hand. It referenced CLUE_GM_R4 and CLUE_VV_EPILOGUE until those cards were "
  "retired into the closing-sequence document.",
  'photo', 1, 'Keep out of sight until the credits, step 8 of the closing sequence', [], 1),
 ('passport-thatcher', 'passport-patricia-thatcher.png', 'An old British passport', 'Nikki Neon', 2,
  'Found under a loose cushion beside the sofa: Patricia Margaret Thatcher, issued 1974, expired 1984. '
  'Nikki shows it; Tina ‘Tank’ Thatcher explains the name.',
  "An expired pre-1988 British passport opened at the particulars page: Patricia Margaret Thatcher, born "
  "Sheffield 1946, profession 'civil servant', issued 1974 at Northallerton, expired 1984. Every number and "
  "office is invented and the image is watermarked for game use. Give it to Nikki with her Round 2 card; she "
  "shows it to Tina, who explains that Patricia Thatcher was her working name in intelligence. Crease it once "
  "so it does not look freshly printed.",
  'document', 0, 'Round 2, with Nikki’s card', ['CLUE009', 'CLUE015', 'CLUE130', 'CLUE_R2_GILES_01'], 1),
]

# Pictures stood down rather than deleted, so the reason survives: photo_id -> why.
RETIRED = {
 'photo-mirror': "Replaced by photo-lucien-mirror. Its anonymous woman, seen from behind in dark velvet with "
                 "the same hair and build, was close enough to the decanter woman to start a false "
                 "identification from the sleeve alone.",
}


def measure(path):
    """sha and pixel size of the original, when it is present."""
    if not path.exists(): return None, None, None
    from PIL import Image
    with Image.open(path) as image:
        w, h = image.size
    return w, h, hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def tidy(root, db_path, apply):
    """Keep only the artwork an active photograph uses; archive the rest rather than deleting it."""
    art = root / ART
    db = sqlite3.connect(db_path)
    keep = {r[0] for r in db.execute("SELECT source_file FROM local_evidence_photos WHERE status='active'")}
    db.close()
    present = {p.name for p in art.iterdir() if p.is_file() and not p.name.startswith('.')}
    stale = sorted(present - keep)
    absent = sorted(keep - present)
    print(f'{len(keep)} files are needed for printing; {len(present)} are in {ART}')
    for name in sorted(keep & present): print(f'  keep:    {name}')
    for name in stale: print(f'  archive: {name}')
    for name in absent: print(f'  MISSING: {name}  (an active photograph has no file)')
    if not stale:
        print('\nNothing to archive.'); return
    if not apply:
        print('\nPreview only. Re-run with --tidy --apply to move them.'); return
    dest = art / 'archive'
    dest.mkdir(exist_ok=True)
    for name in stale:
        target = dest / name
        if target.exists(): print(f'  already archived, left alone: {name}'); continue
        shutil.move(str(art / name), str(target))
    print(f'\nmoved {len(stale)} files to {ART}/archive; {len(keep & present)} remain to order')


def main():
    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--db', type=Path, default=root / 'data/valemeridian-event.sqlite')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--tidy', action='store_true',
                    help='move artwork not used by an active photograph into data/artwork/archive')
    args = ap.parse_args()
    if args.tidy:
        tidy(root, args.db, args.apply); return
    rows, missing = [], []
    recorded = {}
    probe = sqlite3.connect(args.db)
    if probe.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='local_evidence_photos'").fetchone():
        recorded = {r[0]: (r[1], r[2]) for r in probe.execute('SELECT photo_id, pixel_width, pixel_height FROM local_evidence_photos')}
    probe.close()
    for pid, filename, title, holder, rnd, caption, description, size, private, cue, refs, copies in PHOTOS:
        w, h, sha = measure(root / ART / filename)
        if sha is None:
            missing.append(filename)
            w, h = recorded.get(pid, (None, None))   # keep the recorded size: the original is not shipped
        rows.append((pid, filename, title, holder, rnd, caption, description, size, private, cue,
                     json.dumps(refs), copies, w, h, sha))
    db = sqlite3.connect(args.db)
    have = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='local_evidence_photos'").fetchone()
    before = {r[0]: r[1:] for r in db.execute('SELECT photo_id, file_sha, description FROM local_evidence_photos')} if have else {}
    print(f'{len(rows)} photographs; {len(before)} already recorded; {len(missing)} original files missing '
          f'{missing if missing else ""}')
    for r in rows:
        state = 'new' if r[0] not in before else ('changed' if before[r[0]] != (r[14], r[6]) else 'same')
        if state != 'same': print(f'  {state}: {r[0]} ({r[1]})')
    for pid in RETIRED:
        if pid in before: print(f'  retire: {pid}')
    if not args.apply:
        db.close(); print('Preview only. Re-run with --apply to write.'); return
    bk = root / 'data/backups' / f'valemeridian-event-before-evidence-photos-{date.today()}.sqlite'
    if not bk.exists():
        db.close(); shutil.copy2(args.db, bk); print(f'before-database: {bk}'); db = sqlite3.connect(args.db)
    now = datetime.now(timezone.utc).isoformat(timespec='seconds')
    try:
        with db:
            db.execute(SCHEMA)
            if 'retired_reason' not in {c[1] for c in db.execute('PRAGMA table_info(local_evidence_photos)')}:
                db.execute('ALTER TABLE local_evidence_photos ADD COLUMN retired_reason TEXT')
            for pid, why in RETIRED.items():
                db.execute("UPDATE local_evidence_photos SET status='retired', retired_reason=?, plan_id=?, "
                           'updated_at=? WHERE photo_id=?', (why, PLAN, now, pid))
            for r in rows:
                db.execute('INSERT OR REPLACE INTO local_evidence_photos (photo_id, source_file, title, '
                           'holder_character, round, caption, description, print_size, private, cue, clue_refs_json, '
                           'copies, pixel_width, pixel_height, file_sha, status, plan_id, updated_at) '
                           'VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', (*r, 'active', PLAN, now))
        bad = []
        for pid, *_ in rows:
            row = db.execute('SELECT description, clue_refs_json FROM local_evidence_photos WHERE photo_id=?', (pid,)).fetchone()
            if not row or len(row[0]) < 60: bad.append(f'{pid}: description missing or too short')
            for clue in json.loads(row[1]):
                if not db.execute("SELECT 1 FROM clues WHERE clue_id=? AND status='active'", (clue,)).fetchone():
                    bad.append(f'{pid}: references {clue}, which is not an active card')
        for pid in RETIRED:
            row = db.execute('SELECT status, retired_reason FROM local_evidence_photos WHERE photo_id=?', (pid,)).fetchone()
            if row and (row[0] != 'retired' or not row[1]): bad.append(f'{pid}: not retired with a reason')
        if bad: print('VERIFY FAILED:', *bad, sep='\n  '); sys.exit(1)
        n, r = db.execute("SELECT sum(status='active'), sum(status='retired') FROM local_evidence_photos").fetchone()
        print(f'verified: {n} photographs recorded with descriptions and card references, {r or 0} retired')
    finally:
        db.close()


if __name__ == '__main__':
    main()
