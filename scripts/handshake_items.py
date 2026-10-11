"""Handshake items: every place a card relies on another character having something to say back.

Three kinds, all read-only:
  exchange  every card that sends its owner to somebody, Rounds 0-3: can the person
            approached answer what they are asked, from their own brief and cards so far?
  mention   a sentence that names a third person: would they recognise what is said?
  ambiguous a bare first name shared by two characters (Peter, Ronnie, Tina)

Question cards are included even where an answer contract exists: a contract proves
the answer is on the target's card in time, but only a read shows it answers what is
actually asked (Pass 8 found half-answered questions with valid contracts).
Keyword matching was tried and was too noisy, so this module only
finds the items and fingerprints both sides; a person reads them and records a verdict
with record_handshake_reviews.py. The review script then lists anything new or changed.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter

TITLES = {'Dr.', 'Sir', 'Lady', 'Miss', 'Inspector', 'Agent', 'DJ'}
# Surnames and nicknames people actually use on the cards, beyond the automatic ones.
EXTRA_ALIASES = {
    'Peter Packard': ['Packard'], 'Ronnie Redhand': ['Redhand'], 'Ronnie Reels': ['Reels'],
    'Tina Tanktop': ['Tanktop'], "Tina 'Tank' Thatcher": ['Thatcher'], "'Nev' Neville": ['Neville'],
    'Cassette Carl': ['Carl'],
}
NOT_ALIASES = {'Cassette'}
# The victim is not asked to answer anything after Round 0, and the GM is not a character.
NOT_SUBJECTS = {'Game Master'}
MENTION_SKIP = {'Vincent Vale', 'Game Master'}


def sha(text):
    return hashlib.sha256((text or '').encode('utf-8')).hexdigest()


def sentences(text):
    return [s for s in re.split(r'(?<!Dr\.)(?<=[.!?”"])\s+', re.sub(r'\s+', ' ', text or '').strip()) if s]


def alias_table(names):
    """Full name, quoted nicknames and unshared first names; shared first names are returned separately."""
    def first(n):
        toks = [t for t in n.split() if t not in TITLES]
        return toks[0].strip("'") if toks else None
    firsts = Counter(first(n) for n in names)
    table = {}
    for n in names:
        al = {n} | set(re.findall(r"'([^']+)'", n)) | set(EXTRA_ALIASES.get(n, []))
        f = first(n)
        if f and firsts[f] == 1 and f not in NOT_ALIASES:
            al.add(f)
        table[n] = sorted(al, key=len, reverse=True)
    shared = {f: sorted(n for n in names if first(n) == f) for f, c in firsts.items() if c > 1}
    return table, shared


def material(db, name, upto_round):
    """What the named person has to answer with by that round: brief plus their own cards."""
    r = db.execute('SELECT description, secret FROM characters WHERE character_name=?', (name,)).fetchone()
    parts = [r[0] or '', r[1] or ''] if r else ['', '']
    parts += [c[0] for c in db.execute(
        "SELECT clue_content FROM clues WHERE status='active' AND character_name=? AND round<=? "
        'ORDER BY round, clue_id', (name, upto_round))]
    return '\n'.join(parts)


def current_items(db):
    names = [r[0] for r in db.execute(
        "SELECT DISTINCT character_name FROM clues WHERE status='active' AND character_name IS NOT NULL")]
    names = [n for n in names if n not in NOT_SUBJECTS]
    table, shared = alias_table(names)
    contracted = {r[0] for r in db.execute(
        "SELECT DISTINCT clue_id FROM clue_answer_contracts WHERE status='source_checked'")}
    cols = ('clue_id', 'character_name', 'round', 'clue_content', 'targets_json')
    cards = [dict(zip(cols, r)) for r in db.execute(
        "SELECT c.clue_id, c.character_name, c.round, c.clue_content, c.targets_json "
        "FROM clues c JOIN local_clue_record_kinds k USING(clue_id) "
        "WHERE c.status='active' AND k.record_kind='ordinary' AND c.round BETWEEN 0 AND 3 "
        "ORDER BY c.round, c.character_name")]
    mat_cache = {}

    def mat(name, rnd):
        if (name, rnd) not in mat_cache:
            mat_cache[(name, rnd)] = sha(material(db, name, rnd))
        return mat_cache[(name, rnd)]

    items = []
    for c in cards:
        targets = json.loads(c['targets_json'] or '[]')
        for t in targets:  # every directed card; see module docstring
            items.append(dict(key=f"exchange|{c['clue_id']}|{t}", kind='exchange', clue_id=c['clue_id'],
                              owner=c['character_name'], subject=t, round=c['round'],
                              contracted=c['clue_id'] in contracted,
                              text=c['clue_content'], source_sha=sha(c['clue_content']),
                              subject_sha=mat(t, c['round'])))
        for s in sentences(c['clue_content']):
            hit = set()
            for n, al in table.items():
                if n in MENTION_SKIP or n == c['character_name'] or n in targets:
                    continue
                if any(re.search(r"(?<![\w'])" + re.escape(a) + r"(?![\w])", s) for a in al):
                    hit.add(n)
            for n in sorted(hit):
                items.append(dict(key=f"mention|{c['clue_id']}|{n}|{sha(s)[:12]}", kind='mention',
                                  clue_id=c['clue_id'], owner=c['character_name'], subject=n,
                                  round=c['round'], text=s, source_sha=sha(s), subject_sha=mat(n, c['round'])))
            for f, group in shared.items():
                bare = s
                for g in group:  # remove fully named uses, then look for the first name alone
                    bare = bare.replace(g, '')
                if re.search(r'\b' + re.escape(f) + r'\b', bare):
                    items.append(dict(key=f"ambiguous|{c['clue_id']}|{f}|{sha(s)[:12]}", kind='ambiguous',
                                      clue_id=c['clue_id'], owner=c['character_name'], subject=f,
                                      round=c['round'], text=s, source_sha=sha(s), subject_sha=''))
    return items


REGISTRY_SQL = """CREATE TABLE IF NOT EXISTS local_handshake_reviews (
  item_key TEXT PRIMARY KEY,
  kind TEXT NOT NULL CHECK (kind IN ('exchange','mention','ambiguous')),
  clue_id TEXT NOT NULL,
  subject_name TEXT NOT NULL,
  round INTEGER NOT NULL,
  source_sha TEXT NOT NULL,
  subject_sha TEXT NOT NULL,
  verdict TEXT NOT NULL CHECK (verdict IN ('ok','gap','by_design')),
  note TEXT,
  plan_id TEXT NOT NULL,
  reviewed_at TEXT NOT NULL)"""


def compare(db, items):
    """Split current items into reviewed, open gaps, and those needing a (re)read."""
    have = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='local_handshake_reviews'").fetchone()
    reg = {} if not have else {r[0]: r for r in db.execute(
        'SELECT item_key, source_sha, subject_sha, verdict, note FROM local_handshake_reviews')}
    out = dict(reviewed=[], gaps=[], by_design=[], unread=[], changed=[])
    for it in items:
        r = reg.get(it['key'])
        if r is None:
            out['unread'].append(it)
        elif (r[1], r[2]) != (it['source_sha'], it['subject_sha']):
            out['changed'].append(it)
        elif r[3] == 'gap':
            out['gaps'].append(dict(it, note=r[4]))
        elif r[3] == 'by_design':
            out['by_design'].append(dict(it, note=r[4]))
        else:
            out['reviewed'].append(it)
    out['registry_present'] = bool(have)
    out['retired'] = len(set(reg) - {it['key'] for it in items})
    return out
