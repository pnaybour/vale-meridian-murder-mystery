"""Pre-printed question notes for cross-table conversations.

Every Round 1-3 card that sends its owner to someone at another table gets a note with a
permanent key (Q<round>-<nn>). The note carries a short draft in the asker's own voice, which
the guest can add to or change; the reply space is left blank for the other guest. Round 0 is
the standing reception, so it has no notes. Same-table conversations need no note.

  python3 scripts/cross_table_notes.py            check: missing, stale and orphaned notes
  python3 scripts/cross_table_notes.py --apply    create the table if needed and add missing notes

Keys never change once given: a new cross-table card gets the next free number in its round.
A note is 'stale' when its card text, partner or either table has changed since it was
drafted; stale notes are reported and must be re-read (update the draft here and re-run with
--apply --redraft KEY). Drafts never carry the answer, and never put the asker's own secret on
paper, because other guests may carry the note.
"""
from __future__ import annotations
import argparse, hashlib, json, shutil, sqlite3, sys
from datetime import date, datetime, timezone
from pathlib import Path

PLAN = 'cross-table-notes-2026-09-19'

SCHEMA = """CREATE TABLE IF NOT EXISTS local_cross_table_notes (
  note_key TEXT PRIMARY KEY,
  clue_id TEXT NOT NULL,
  round INTEGER NOT NULL,
  from_character TEXT NOT NULL,
  from_table INTEGER NOT NULL,
  to_character TEXT NOT NULL,
  to_table INTEGER NOT NULL,
  draft TEXT NOT NULL,
  clue_sha TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('active','retired')),
  plan_id TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE (clue_id, to_character))"""

# (clue_id, recipient) -> draft in the asker's voice. The question only: no answer, no own secret.
DRAFTS = {
 # ---------------- Round 1 ----------------
 ('CLUE_CCH_R1', 'Dr. Beverly Steele'): "Dr Steele, I hear a great deal about what people take before they go on. Vale seemed unusually sharp tonight, even for him. What were you supplying him before the gala?",
 ('CLUE_RB_R1', 'Lucien Luxe'): "Lucien, Vale built us both the same way: the look, the songs, the secrets. If he kept something on me, he kept something on you. What are you afraid he might still release? Did either of us ever find a way out?",
 ('CLUE_SC_R1', 'Dakota Steele'): "Dakota, before the toast I carried a sealed silver compact marked VV for Beverly. I never opened it. Is the one you found the same? I'd rather not say who I handed it to until I know what this is about.",
 ('CLUE051', 'Ricky Blaze'): "Ricky, people say you forged Vale's signature on a loan. What did Vale do with it? Did he use you the way he used others?",
 ('CLUE_PENNY_R1', 'Brenda Blip'): "Brenda, I had a hand in the warm words Vale was going to say about Veronica tonight. What did he promise would come after the toast?",
 ('CLUE_POLLY_R1', 'Lola Lasalle'): "Lola, you guard your image like a policy. I spent thirty years reading other people's stories. Why are you so careful about press attention?",
 ('CLUE_FFG_R1', 'Veronica Vane'): "Veronica, after the toast I noticed a pale mark caught in the hem of your gown. I used no chalk on that hem, and I can't tell what it is by looking. I would rather you heard it from me.",
 ('CLUE162', 'Dr. Beverly Steele'): "Dr Steele, I saw a covered dish carried back to the service hatch where you were standing, and you looked rather worse than Cassie did. Why did it come back?",
 # ---------------- Round 2 ----------------
 ('CLUE_CC_R2', 'Leo Lights'): "Leo, I checked the playback after the collapse: armed, but nobody ever gave the play command. Your lights answered the same twenty seconds. What cue did you follow at 19:29, and how was it arranged?",
 ('CLUE_R2_REDHAND_02', 'DJ Spinny T'): "Spinny, I gather you were handed an envelope tonight and did exactly what it said. What were you paid to do, and did you ever find out who wanted it?",
 ('CLUE097', 'Penny Page'): "Penny, you write Vale's speeches. What were you asked to write for tonight's toast, and did it mention me?",
 ('CLUE177', 'Penny Page'): "Penny, you wrote Vale's words and watched him take the credit. Why have you had enough? I have my own reasons to hate the way he controlled other people's images.",
 ('CLUE_R2_RONNIE_REELS_01', 'Dr. Beverly Steele'): "Dr Steele, the silver compact Scooter carried: did it hold a ready-to-take dose, or a sample meant to be diluted?",
 ('CLUE_R2_TOMMY_01', 'Brenda Blip'): "Brenda, I have a copy of the BBC recording from your studio: Vale claiming half of Veronica's fees, and Veronica admitting she signed. Does that match what you heard?",
 ('CLUE006', 'Marianne Moonbeam'): "Marianne, you seem to see more than most. Will you gaze into the auras here tonight and tell me whether any of it threatens me?",
 ('CLUE_POLLY_R2', 'Barry Byte'): "Mr Byte, you supplied Vale's tapes. Did his archive hold paperwork as well as recordings?",
 ('CLUE_SC_R2', 'Dr. Beverly Steele'): "Dr Steele, the compact I carried for you has turned up, and I have it with me. Did it hold an ordinary finished dose, or an undiluted sample? I'd like to understand the favour I did you.",
 ('CLUE089', 'Lady Helena de Brissac'): "Lady Helena, I stopped Vale's covered dish because its seal had been disturbed. What did you see of it being taken back?",
 ('CLUE_R2_BEVERLY_01', 'Graham Greenwell'): "Graham, the silver compact held an undiluted sample of the ingredient in your remedy, not a ready dose. What have you been telling investors the remedy contains?",
 ('CLUE165', 'Ricky Blaze'): "Ricky, I saw you outside the main-room doors during the music. It was only a passing moment, so I can't vouch for the whole time, but I did see you there.",
 ('CLUE_PENNY_R2', 'Lucien Luxe'): "Lucien, Vale owned my words; I hear he owned something worse of yours, on film. Why do his recordings frighten you? I'll tell you why I want credit for my own work.",
 ('CLUE_SASHA_R2', 'Chuck Chambers'): "Mr Chambers, you know what gets said in Vale's green room. What does it say about me, and about Vale's money?",
 ('CLUE_RO_R2', 'Barry Byte'): "Mr Byte, I understand you kept a copy of the tapes you supplied to Vale. What is on your VV-1 copy, and did anything you copied for him touch government business?",
 ('CLUE_CCH_R2', 'DJ Spinny T'): "Spinny, I hear somebody paid you in cash tonight. Who paid you to raise the music, and what did the instruction say?",
 ('CLUE_VVL_R2', 'Fiona Fringe'): "Fiona, what did you notice about Veronica's gown after the toast? I've found something tonight I can't put a time to, and I suspect you have too.",
 ('CLUE021', 'Tommy Tech'): "Tommy, I have an older copy of Vale's tape, labelled VV-1: the BBC recording about Veronica's fees. What is on your copy? Let's compare.",
 ('CLUE_FFG_R2', 'Inspector Donna Reed'): "Inspector Reed, the pale mark I reported came from the hem of Veronica's gown. I noticed it after the toast; the sample is labelled F1. It troubled me as a designer, and it may matter to you.",
 ('CLUE173', 'Veronica Vane'): "Veronica, I was in the BBC studio when Vale said he took half your fees and you said you had signed. Why did that recording threaten your new BBC role?",
 ('CLUE_CCA_R2', 'Sabrina Sinclair'): "Sabrina, there's talk of a juicy BBC recording behind Vale's big story. Did you ever hear it, or only his word for it?",
 ('CLUE163', 'Cassie Chase'): "Cassie, I saw a covered dish being taken back towards the hatch. Whose was it, and why was it withdrawn?",
 ('CLUE175', 'Ronnie Redhand'): "Ronnie Redhand, word at the bar is that you took Vale's money during the strike. What did it buy from you?",
 ('CLUE090', 'DJ Spinny T'): "Spinny, could you see the main-room doorway from your booth during the music cue? I was outside it the whole time.",
 ('CLUE_WW_R2', 'Scooter'): "Scooter, nobody notices the people who keep an evening running, but I noticed you. What were you asked to carry tonight?",
 ('CLUE100', 'Peter Vale'): "Mr Vale, I'm told you have read your brother's papers. What did Veronica's contract say: how much of her earnings could he take, and does that stop now he is dead?",
 # ---------------- Round 3 ----------------
 ('CLUE129', 'Lady Helena de Brissac'): "Lady Helena, I understand Vale could have said something about your name, and that you have lived with that a long while. What was it he held? I have reasons of my own for asking.",
 ('CLUE161', 'Fiona Fringe'): "Miss Fringe, you designed Veronica's gown and I gather you found something on it after the toast. What was in the hem, and could it have got there innocently?",
 ('CLUE176', 'Ronnie Reels'): "Mr Reels, you had a camera on this room from the east wall all evening. What did your position let you see near the private drinks, and did you recognise anybody there?",
 ('CLUE144', 'Dakota Steele'): "Dakota, before the music I saw Veronica slip a deep-red envelope into your coat pocket at the cloakroom. What was in it?",
 ('CLUE131', 'Polly Premium'): "Polly, you noticed my greeting with Frankie earlier. May I explain it to you properly?",
 ('CLUE178', 'Vance Vellum'): "Vance, what exactly does your decanter photograph show, and when did you take it?",
 ('CLUE138', 'Marianne Moonbeam'): "Marianne, what do you actually put in your preparations? You believe in wellness the way I sell it, and I'd like to know how that feels.",
 ('CLUE123', 'Inspector Donna Reed'): "Inspector Reed, I have read the laboratory report. Does it show who put the stimulant in the wine? I'd like to hear your answer for myself.",
 ('CLUE_VV_R3', 'Fiona Fringe'): "Fiona, during the music I saw Veronica's profile beside the private decanter, in the gown you designed. What did you notice about that gown?",
 ('CLUE150', 'DJ Spinny T'): "Spinny, the recording Vale meant to play was the BBC exchange about Veronica's fees and her new role. What did your anonymous music instruction pay you to do?",
 ('CLUE_SC_R3', 'Cassie Chase'): "Cassie, I carried one thing meant for Vale tonight: a sealed compact, to Veronica. You stopped another. Did Vale ever receive the dish you sent back?",
 ('CLUE148', 'Wanda Wires'): "Wanda, people say Vale made you sign off a rehearsal before it was finished, then kept the paper. What was that like? Is signing your own name under pressure better than faking someone else's?",
 ('CLUE128', 'Inspector Donna Reed'): "Inspector Reed, before we talk properly: what do you make of what the laboratory found in the separate dish?",
 ('CLUE_PENNY_R3', 'Colin Cable'): "Colin, I'm sure the local recording holds the key to this murder. You checked the playback after the collapse: what did you find, and did the room ever hear it?",
 ('CLUE172', 'Veronica Vane'): "Veronica, I have my brother's management agreement in front of me. Clause 7 says his right to half your fees ends with his death; money already owed stays with the estate. I thought you should hear it from me.",
 ('CLUE_RO_R3', "'Nev' Neville"): "Nev, I owe you this: my file was wrong about you. What were you afraid of tonight?",
 ('CLUE_CCH_R3', 'Brenda Blip'): "Brenda, what did Vale promise to play at the toast, and what did you hear in the BBC studio? I'd rather have a first-hand account than my own theory.",
 ('CLUE_NN_R3', 'Ronnie Reels'): "Ronnie Reels, during the music I saw Veronica's face as she went to the private decanter, but people hid her hands. How much did your camera position let you see?",
 ('CLUE139', 'Leo Lights'): "Mr Lights, just before the toast the music and stage lights rose together, as if on a signal. Who asked you to arrange that cue?",
 ('CLUE_FFG_R3', 'Inspector Donna Reed'): "Inspector Reed, I have read the laboratory report. What does the fabric finding show about the gown?",
 ('CLUE_R3_DAKOTA_01', 'Veronica Vane'): "Veronica, from the west pillar I saw you at the private decanter during the music. I kept quiet for reasons I'm not proud of. I'd like to hear your side.",
 ('CLUE122', 'Dr. Beverly Steele'): "Dr Steele, the laboratory report says the fatal dose was in Vale's private wine. What can you tell me about the sample in the silver compact marked VV?",
 ('CLUE_LL_R3', 'Glenda Gold'): "Glenda, before the toast Veronica asked me to arrange the music-and-lights cue, calling it a surprise for Vince, and I saw her leave a deep-red envelope at Spinny's desk. I kept quiet for fear of being blamed. I think you'll understand why.",
 ('CLUE125', 'Larry Loveboat'): "Larry, everyone is deciding Rex did it because of his temper. You saw him below the guardrail: when, and did he stay?",
 ('CLUE_WW_R3', 'Leo Lights'): "Leo, who asked you for the music-and-lights cue? I've carried the blame for my own decisions; I'd like a straight answer about somebody else's.",
}
MAX_WORDS = 50


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def cross_table_cards(db):
    """(round, from_table, from, clue_id, to, to_table, card text) for every live cross-table card in Rounds 1-3."""
    plan = db.execute("SELECT plan_id FROM seating_plans WHERE status='approved'").fetchone()[0]
    seat = dict(db.execute('SELECT character_name, table_number FROM seat_assignments WHERE plan_id=? AND character_name IS NOT NULL', (plan,)))
    for name in list(seat):  # the Vincent performer plays Peter from Round 1
        if name == 'Vincent Vale / Peter Vale': seat['Peter Vale'] = seat[name]
    kinds = dict(db.execute('SELECT clue_id, record_kind FROM local_clue_record_kinds'))
    out = []
    for cid, who, rnd, tj, text in db.execute(
            "SELECT clue_id, character_name, round, targets_json, clue_content FROM clues WHERE status='active' AND round BETWEEN 1 AND 3"):
        if kinds.get(cid, 'ordinary') != 'ordinary': continue
        for to in json.loads(tj or '[]'):
            if seat.get(who) is None or seat.get(to) is None: raise SystemExit(f'{cid}: {who} or {to} has no seat')
            if seat[who] != seat[to]:
                out.append((rnd, seat[who], who, cid, to, seat[to], text))
    return sorted(out)


def audit(db):
    """Split notes into ok, stale, orphaned, and cards still missing a note."""
    cards = {(c[3], c[4]): c for c in cross_table_cards(db)}
    have = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='local_cross_table_notes'").fetchone()
    notes = {} if not have else {(r[1], r[4]): r for r in db.execute(
        "SELECT note_key, clue_id, round, from_character, to_character, from_table, to_table, clue_sha FROM local_cross_table_notes WHERE status='active'")}
    ok, stale, orphan = [], [], []
    for k, n in notes.items():
        c = cards.get(k)
        if c is None: orphan.append(n[0])
        elif (sha(c[6]), c[1], c[5], c[0]) != (n[7], n[5], n[6], n[2]): stale.append(n[0])
        else: ok.append(n[0])
    missing = [k for k in cards if k not in notes]
    return cards, notes, ok, stale, orphan, missing


def main():
    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--db', type=Path, default=root / 'data/valemeridian-event.sqlite')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--redraft', action='append', default=[], help='note key whose draft and fingerprint to refresh from DRAFTS')
    args = ap.parse_args()
    db = sqlite3.connect(args.db)
    cards, notes, ok, stale, orphan, missing = audit(db)
    print(f'{len(cards)} cross-table cards in Rounds 1-3; notes: {len(ok)} current, {len(stale)} stale, '
          f'{len(orphan)} orphaned, {len(missing)} missing')
    for k in stale: print('  stale:', k)
    for k in orphan: print('  orphaned:', k)
    bad = [f'no draft for {k}' for k in missing if k not in DRAFTS]
    # A draft whose card has been retired (a character left the cast) is simply unused.
    active = {r[0] for r in db.execute("SELECT clue_id FROM clues WHERE status='active'")}
    bad += [f'draft for {k} is not a cross-table card' for k in DRAFTS if k not in cards and k[0] in active]
    bad += [f'{k}: {len(DRAFTS[k].split())} words' for k in DRAFTS if len(DRAFTS[k].split()) > MAX_WORDS]
    redraft = {n[0]: k for k, n in notes.items() if n[0] in args.redraft}
    bad += [f'unknown note to redraft: {k}' for k in args.redraft if k not in redraft]
    if bad:
        db.close(); print('FAILED:', *bad, sep='\n  '); sys.exit(1)
    if not args.apply:
        db.close(); print('Check only. Re-run with --apply to add missing notes.'); return
    if not missing and not redraft and not orphan:
        db.close(); print('Nothing to add.'); return

    bk = root / 'data/backups' / f'valemeridian-event-before-cross-table-notes-{datetime.now():%Y-%m-%d-%H%M%S}.sqlite'
    db.close(); shutil.copy2(args.db, bk); print(f'before-database: {bk}')
    now = datetime.now(timezone.utc).isoformat(timespec='seconds')
    db = sqlite3.connect(args.db)
    try:
        with db:
            db.execute(SCHEMA)
            used = {r[0] for r in db.execute('SELECT note_key FROM local_cross_table_notes')}
            def next_key(rnd):
                n = 1
                while f'Q{rnd}-{n:02d}' in used: n += 1
                used.add(f'Q{rnd}-{n:02d}')
                return f'Q{rnd}-{n:02d}'
            for k in sorted(missing, key=lambda k: cards[k][:3]):
                rnd, ft, who, cid, to, tt, text = cards[k]
                db.execute('INSERT INTO local_cross_table_notes VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                           (next_key(rnd), cid, rnd, who, ft, to, tt, DRAFTS[k], sha(text), 'active', PLAN, now))
            for key, k in redraft.items():
                rnd, ft, who, cid, to, tt, text = cards[k]
                db.execute('UPDATE local_cross_table_notes SET draft=?, clue_sha=?, round=?, from_table=?, to_table=?, updated_at=? WHERE note_key=?',
                           (DRAFTS[k], sha(text), rnd, ft, tt, now, key))
            for key in orphan:
                db.execute("UPDATE local_cross_table_notes SET status='retired', updated_at=? WHERE note_key=?", (now, key))
        cards, notes, ok, stale, orphan, missing = audit(db)
        if stale or orphan or missing:
            print(f'VERIFY FAILED: {len(stale)} stale, {len(orphan)} orphaned, {len(missing)} missing'); sys.exit(1)
        per = {}
        for n in notes.values(): per[n[2]] = per.get(n[2], 0) + 1
        print(f'verified: {len(ok)} notes, all current; per round {dict(sorted(per.items()))}')
    finally:
        db.close()


if __name__ == '__main__':
    main()
