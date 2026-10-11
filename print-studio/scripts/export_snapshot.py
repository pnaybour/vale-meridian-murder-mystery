"""Build the print snapshot (lib/event.json) from the event database.

Reads data/valemeridian-event.sqlite and data/event.json without modifying them, and writes
lib/event.json, which the Print Studio and scripts/print.mjs use. Run it after changing the
database, the event details or the story files in story/:

    python3 scripts/export_snapshot.py        (or: npm run snapshot)
"""
import hashlib
import json
import math
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from preparation import load_preparation, render_preparation
from table_signs import table_guests

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parent
EVENT_ID = 'valemeridian'
db = ROOT / 'data/valemeridian-event.sqlite'
con = sqlite3.connect(f'file:{db}?mode=ro', uri=True)
con.row_factory = sqlite3.Row
event_details = json.loads((ROOT / 'data/event.json').read_text())
characters = [dict(r) for r in con.execute("select character_id, character_name from characters where status='active'")]
public_characters = json.loads((APP / 'source/character-introductions.json').read_text())['characters']
preparation = load_preparation()
local = {r['clue_id']: dict(r) for r in con.execute("select rowid as _order, * from clues where status='active' order by rowid")}
active_clues = []
for clue_id, database_clue in local.items():
    active_clues.append(dict(
        clueid=clue_id,
        clue_title=database_clue['clue_title'],
        clue_content=database_clue['clue_content'],
        who_reveals=database_clue['who_reveals'],
        CharacterID=database_clue['character_id'],
        round='TOAST' if database_clue['round'] is None else str(database_clue['round']),
    ))

plans = list(con.execute("select plan_id from seating_plans where status='approved'"))
assert len(plans) == 1, 'Expected one approved seating plan'
plan = plans[0]['plan_id']
seats = [dict(r) for r in con.execute('select person_id,guest_name,character_name,table_number,seat_number from seat_assignments where plan_id=? order by table_number,seat_number', (plan,))]
attendees = [dict(r) for r in con.execute("select p.person_id,p.display_name,eg.attendance from event_guests eg join people p on p.person_id=eg.person_id where eg.event_id='valemeridian' and eg.attendance in ('yes','provisional') order by p.display_name")]
pending_guests = [r['display_name'] for r in attendees if r['person_id'] not in {s['person_id'] for s in seats}]
menu_by_person = {
    r['person_id']: dict(r)
    for r in con.execute(
        """
        select
          eg.person_id,
          p.dietary_notes,
          mo.starter,
          mo.main,
          mo.dessert,
          mo.menu_options_missing
        from event_guests eg
        join people p on p.person_id=eg.person_id
        left join menu_orders mo on mo.event_id=eg.event_id and mo.person_id=eg.person_id
        where eg.event_id='valemeridian'
        """
    )
}
assignments = {r['character_id']: dict(r) for r in con.execute('select * from character_assignments')}
assignments['CHAR_GAME_MASTER'] = next(v for v in assignments.values() if v['game_master'])
assignments['CHAR_PETER_VALE'] = assignments['CHAR048']
seat_by_person = {s['person_id']: s for s in seats}
master_names = {r['character_id']: r['character_name'] for r in characters}
kinds = {r['clue_id']: r['record_kind'] for r in con.execute('select * from local_clue_record_kinds')}
closing = ['CLUE_DJ_R4','CLUE_GM_R3_01','CLUE_GM_R4','CLUE_VER_R4','CLUE_REED_R4','CLUE_VV_EPILOGUE']
items = []

def has_food_intolerance(note):
    value = (note or '').strip().lower()
    return bool(value) and value not in {
        'n/a',
        'na',
        'nil',
        'none',
        'normal',
        'no dietary requirements',
        'no requirements',
    }

def add(id, category, title, content='', **kw):
    item = dict(id=id, category=category, title=title, content=content, character='', guest='', table=None, round=None, quantity=1, private=False, source='Event stationery', **{})
    item.update(kw)
    item['revision'] = hashlib.sha256(json.dumps(item, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]
    items.append(item)

for r in active_clues:
    kind = kinds[r['clueid']]
    category = 'clues' if kind == 'ordinary' else 'evidence' if kind == 'artifact' else 'private'
    a = assignments.get(r['CharacterID'])
    s = seat_by_person.get(a['person_id']) if a else None
    name = master_names.get(r['CharacterID'], a['character_name'] if a else '')
    if r['CharacterID'] == 'CHAR048':
        name = 'Vincent Vale' if r['clueid'] in ('CLUE_VV_R0', 'CLUE_VV_ARRIVAL') else 'Peter Vale'
    round_number = 0 if r['round'] == 'TOAST' else int(r['round'])
    order = closing.index(r['clueid']) + 1 if r['clueid'] in closing else 0
    add(r['clueid'], category, r['clue_title'], r['clue_content'], character=name, guest=s['guest_name'] if s else 'Unallocated', table=s['table_number'] if s else None, round=round_number, private=category=='private', source='Local database', order=order, template='report' if kind=='artifact' else 'card', cue='Immediately before the toast' if r['clueid'] in ['CLUE_VV_R0','CLUE_SPINNY_TOAST_01'] else '')

# Pre-printed question notes for cross-table conversations (Rounds 1-3). The key goes on the
# card after its revision is computed, so adding a note never unsettles a card's review.
has_notes = con.execute("select 1 from sqlite_master where type='table' and name='local_cross_table_notes'").fetchone()
cross_notes = [dict(r) for r in con.execute(
    "select * from local_cross_table_notes where status='active' order by round, note_key")] if has_notes else []
keys_by_clue = {}
for n in cross_notes:
    keys_by_clue.setdefault(n['clue_id'], []).append(n['note_key'])
for item in items:
    if item['id'] in keys_by_clue:
        item['noteKey'] = ', '.join(keys_by_clue[item['id']])
# A footnote on each card whose envelope carries something with it (owner, 9 October 2026): what is
# enclosed, and whether it is the guest's own (PRIVATE) or for the table or the room (SHARED). Added
# after the revision, like the note key, so it does not unsettle a card's review. The envelope
# itself still shows only a neutral code; this is on the card, which only its owner reads.
FOOTNOTES = {
    'CLUE_SPINNY_R0': "IN YOUR ENVELOPE · Item A: deep-red envelope E1 (dummy money and the music slip) · PRIVATE",
    'CLUE170': "IN YOUR ENVELOPE · Item B: taxi-driver journey note · PRIVATE",
    'CLUE037': "IN YOUR ENVELOPE · Item C: deep-red envelope E2 (dummy money and the silence slip) · PRIVATE",
    'CLUE009': "IN YOUR ENVELOPE · Item D: passport in Tina's former identity · PRIVATE",
    'CLUE_VVL_R2': "IN YOUR ENVELOPE · Item E: 9 photograph packs, one for each table and one for you · SHARED: take them round",
    'CLUE122': "IN YOUR ENVELOPE · Item F: 8 laboratory reports, one for each table · SHARED: hand one to every table",
}
LAB_REPORT = "ON YOUR TABLE · The laboratory report, handed to your table by Inspector Donna Reed · SHARED"
for item in items:
    if item['id'] in FOOTNOTES:
        item['footnote'] = FOOTNOTES[item['id']]
    elif item['category'] == 'clues' and item.get('round') == 3 and 'laboratory report' in item.get('content', ''):
        item['footnote'] = LAB_REPORT
seat_by_character = {s['character_name']: s for s in seats}
seat_by_character['Peter Vale'] = seat_by_character.get('Vincent Vale / Peter Vale')
for n in cross_notes:
    asker = seat_by_character.get(n['from_character'])
    add('note-' + n['note_key'], 'stationery', n['note_key'], n['draft'], character=n['from_character'],
        guest=asker['guest_name'] if asker else 'Unallocated', table=n['from_table'], round=n['round'],
        template='qnote', toCharacter=n['to_character'], toTable=n['to_table'], clueId=n['clue_id'],
        order=int(n['note_key'].split('-')[1]), source='Cross-table question note (local database)')

public_tables = [dict(
    number=number,
    seats=[dict(
        seat=s['seat_number'],
        guest=s['guest_name'],
        character='Vincent Vale' if s['character_name']=='Vincent Vale / Peter Vale' else s['character_name'],
    ) for s in seats if s['table_number']==number],
) for number in sorted({s['table_number'] for s in seats})]
# The laboratory report goes on every table in Round 3 (owner, 2 October 2026), so it prints once per table.
for item in items:
    if item['id'] == 'CLUE_VV_R2':
        item['quantity'] = len(public_tables)
        item['revision'] = hashlib.sha256(json.dumps({k: v for k, v in item.items() if k != 'revision'}, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]
# Room layout and per-table seating diagrams, for the venue and the GM. Drawn from the recorded
# layout and seat angles so they follow the seating plan instead of drifting from it.
seat_angles = {r['person_id']: dict(r) for r in con.execute(
    'select * from local_seat_positions')} if con.execute(
    "select 1 from sqlite_master where type='table' and name='local_seat_positions'").fetchone() else {}

# The guest "Find your table" sheet: names and rooms only, no characters and no seat numbers,
# drawn from the recorded room layout so it cannot drift away from the seating plan.
layout_rows = [dict(r) for r in con.execute(
    'select * from local_room_layout order by table_number')] if con.execute(
    "select 1 from sqlite_master where type='table' and name='local_room_layout'").fetchone() else []
if layout_rows:
    room_plan = dict(con.execute('select * from local_room_plan').fetchone())
    rooms = json.loads(room_plan['rooms_json'])
    plan_tables = [dict(
        number=r['table_number'], room=r['room'], x=r['x'], y=r['y'],
        guests=[s['guest_name'] for s in seats if s['table_number'] == r['table_number']],
    ) for r in layout_rows]
    missing = [t['number'] for t in plan_tables if not t['guests']]
    assert not missing, f'Positioned tables with no guests: {missing}'
    by_room = {}
    for t in plan_tables: by_room.setdefault(t['room'], []).append(t['number'])
    add('table-plan', 'seating', 'Find your table',
        '\n\n'.join(f"Table {t['number']} — {rooms[t['room']]['name']}\n" + '\n'.join(t['guests'])
                     for t in plan_tables),
        template='table-plan', order=-1, quantity=4, source='Approved local seating and room layout',
        tablePlan=dict(date=event_details['date'], venue=event_details['venue'],
                       hosts=event_details['hosts'],
                       outline=json.loads(room_plan['outline_json']), rooms=rooms,
                       roomTables=by_room, tables=plan_tables))

if layout_rows and seat_angles:
    def seats_of(number):
        return sorted(
            (dict(guest=s['guest_name'], seat=s['seat_number'],
                  character='Vincent Vale' if s['character_name'] == 'Vincent Vale / Peter Vale'
                            else s['character_name'],
                  angle=seat_angles[s['person_id']]['angle_deg'])
             for s in seats if s['table_number'] == number and s['person_id'] in seat_angles),
            key=lambda s: s['seat'])
    room_tables = [dict(
        number=r['table_number'], room=r['room'], x=r['x'], y=r['y'],
        diameter=r['diameter_m'], seats=seats_of(r['table_number']),
    ) for r in layout_rows]
    assert all(len(t['seats']) for t in room_tables), 'A positioned table has no seat angles'
    geometry = dict(outline=json.loads(room_plan['outline_json']), rooms=rooms,
                    chairAllowance=0.55,
                    date=event_details['date'], venue=event_details['venue'])
    add('room-plan', 'seating', 'Proposed room layout and seating',
        '\n'.join(
            [f"{rooms[key]['name']}: tables "
             + ', '.join(str(t['number']) for t in room_tables if t['room'] == key)
             for key in rooms if any(t['room'] == key for t in room_tables)]
            + ['']
            + [f"Table {t['number']}: {t['diameter']:.1f} m, {len(t['seats'])} guests"
               for t in room_tables]),
        template='room-plan', order=-1, private=True,
        source='Approved local seating and room layout',
        roomPlan=dict(**geometry, tables=room_tables))
add(
    'seating-plan', 'seating', 'Seating plan',
    '\n\n'.join(f"Table {t['number']}\n" + '\n'.join(
        f"{s['seat']}. {s['guest']} — {s['character']}" for s in t['seats']
    ) for t in public_tables),
    template='seating-plan', order=-1, source='Approved local seating',
    seatingPlan=dict(date=event_details['date'], venue=event_details['venue'],
                     hosts=event_details['hosts'], tables=public_tables),
)

for s in seats:
    for name in (['Vincent Vale','Peter Vale'] if s['character_name']=='Vincent Vale / Peter Vale' else [s['character_name']]):
        if name in ('Vincent Vale', 'Peter Vale'):
            # The public website combines the twins. Keep the arrival badge's
            # introduction separate from the later role-change information.
            introduction, replacement = public_characters['Vincent Vale / Peter Vale']['description'].split('. ', 1)
            description = introduction + '.' if name == 'Vincent Vale' else replacement
        elif name == 'Helicopter Pilot':
            # This child role is not listed on the website; don't invent a bio.
            description = ''
        else:
            description = public_characters[name]['description']
        introduction_source = 'character introduction'
        add('badge-'+s['person_id']+'-'+name.split()[0], 'badges', name, character=name, description=description, guest=s['guest_name'], table=s['table_number'], template='badge', private=name=='Peter Vale', cue='Keep private until the Round 1 role change' if name=='Peter Vale' else '', source='Approved local seating; '+introduction_source if description else 'Approved local seating')
    # The second identity must not be disclosed at arrival on a place card.
    name = 'Vincent Vale' if s['character_name']=='Vincent Vale / Peter Vale' else s['character_name']
    menu = menu_by_person.get(s['person_id'], {})
    dietary_note = (menu.get('dietary_notes') or '').strip()
    add(
        'place-'+s['person_id'],
        'seating',
        name,
        character=name,
        guest=s['guest_name'],
        table=s['table_number'],
        template='place',
        menu=dict(
            starter=menu.get('starter') or '',
            main=menu.get('main') or '',
            dessert=menu.get('dessert') or '',
            missing=bool(menu.get('menu_options_missing')),
        ),
        dietaryNote=dietary_note,
        hasFoodIntolerance=has_food_intolerance(dietary_note),
    )
for table in sorted({s['table_number'] for s in seats}):
    guests = table_guests(table, seats, items)
    content = '\n'.join(f"{g['character']} ({g['guest']})" +
                        (" - " + ', '.join(g['flags']) if g['flags'] else '') for g in guests)
    add(f'table-{table}', 'seating', f'Table {table}', content, table=table, template='table', tableGuests=guests)

# Photographic evidence, described in the database (local_evidence_photos). The pictures
# themselves are generated by scripts/build_photos.py and are not kept in the repository.
photo_rows = list(con.execute(
    "select * from local_evidence_photos where status='active' order by round, photo_id"
)) if con.execute(
    "select 1 from sqlite_master where type='table' and name='local_evidence_photos'"
).fetchone() else []
for photo in photo_rows:
    add(photo['photo_id'], 'evidence', photo['title'], photo['caption'], character=photo['holder_character'],
        round=photo['round'], template='photo', image=f"/evidence/{photo['photo_id']}.jpg",
        imageWidth=photo['pixel_width'], imageHeight=photo['pixel_height'], photoSize=photo['print_size'],
        source=f"Artwork: data/artwork/{photo['source_file']}", description=photo['description'],
        private=bool(photo['private']), cue=photo['cue'], quantity=photo['copies'], proof=True)

# Prop money for the two deep-red envelopes: two bundles of 12 notes. The picture is built from
# data/artwork/valemeridian-prop-money.png by scripts/build_photos.py and printed at 130 mm wide.
add('prop-money', 'evidence', 'Prop money: Vale Meridian Glamour Pounds',
    'Prop banknote. Cut along the marks; put 12 notes in each deep-red envelope.',
    template='money', image='/evidence/prop-money.jpg', imageWidth=1836, imageHeight=857,
    quantity=24, source='Artwork: data/artwork/valemeridian-prop-money.png', proof=True)
add('evidence-music', 'evidence', 'Anonymous music slip', 'At the toast cue, raise the music for twenty seconds. No delays.', character='DJ Spinny T', round=0, template='slip', source='Approved prop specification')
add('evidence-taxi', 'evidence', 'Taxi-driver journey note', '10 October 1986\n\nPassenger: Peter Vale\nCollected outside the solicitor’s office, Cheltenham, at 19:30.\nArrived at the gala at 19:55.', character='Peter Vale', round=1, template='taxi', source='Typeset from the approved prop specification', proof=True)
add('evidence-silence', 'evidence', 'Anonymous silence slip', 'Say nothing about what you saw near the drinks.', character='Dakota Steele', round=2, template='slip', source='Approved prop specification')
# One envelope per card: every character gets their own clue in their own envelope, each round.
# The label is read across a table, so the guest's name leads and the character confirms it.
# Avery J8161, 18 per sheet; a new sheet starts at each round, which keeps the sorting honest.
# Physical items go inside the clue envelope with the card they belong to, so the GM hands out
# envelopes and nothing else. The compact is the exception: the GM hands it over in person.
# Each envelope prints what it must contain, and the inclusion checklist below lists them all.
# Guests can read the envelope, so props print only as a neutral code; the checklist says what
# each code is. Question notes print by their key, as everybody receives notes.
ENCLOSURES = {
    'CLUE_SPINNY_R0': [('Item A', 'Deep-red envelope E1: dummy money and the music slip')],
    'CLUE170': [('Item B', 'Taxi-driver journey note')],
    'CLUE037': [('Item C', 'Deep-red envelope E2: dummy money and the silence slip')],
    'CLUE009': [('Item D', "Passport in Tina's former identity")],
    'CLUE_VVL_R2': [('Item E', '9 photograph packs, one for each table and one for Vance')],
    'CLUE122': [('Item F', '8 laboratory reports, one for each table')],
}
def enclosures(card, coded=False):
    notes = [f'Question note {k}' for k in card['noteKey'].split(', ')] if card.get('noteKey') else []
    return notes + [code if coded else f'{code}: {what}' for code, what in ENCLOSURES.get(card['id'], [])]
for card in sorted((i for i in items if i['category'] == 'clues' and i['round'] is not None),
                   key=lambda i: (i['round'], i['table'] or 0, i['guest'])):
    extra = {'enclosures': enclosures(card, coded=True)} if enclosures(card) else {}
    add(f"label-r{card['round']}-{card['id']}", 'labels',
        f"Envelope label · {card['guest']}, round {card['round']}", card['character'],
        round=card['round'], table=card['table'], template='label', labelKind='guest',
        guest=card['guest'], character=card['character'],
        source='Approved local seating and release order', **extra)
missing = set(ENCLOSURES) - {i['id'] for i in items if i['category'] == 'clues'}
assert not missing, f'enclosures for cards that no longer exist: {missing}'

# Rounds 2 and 3 go out as one A4 (C4) envelope per table (Round 1 envelopes sit at each place setting), holding that table's clue envelopes,
# placed on the table in the eating area in advance. The front is printed on A4 and stuck on: most office printers cannot
# feed a C4 envelope. The laboratory report is not in them: Donna carries the eight copies in her own
# Round 3 envelope (Item F) and hands one to every table.
for rnd in (2, 3):
    for tbl in sorted({c['table'] for c in items if c['category'] == 'clues' and c['round'] == rnd}):
        inside = sorted((c for c in items if c['category'] == 'clues' and c['round'] == rnd and c['table'] == tbl),
                        key=lambda c: (c['character'], c['id']))
        add(f'table-envelope-r{rnd}-t{tbl}', 'labels', f'Table envelope · table {tbl}, round {rnd}',
            f'{len(inside)} clue envelopes', round=rnd, table=tbl, template='table-envelope',
            contents=[{'character': c['character'], 'guest': c['guest']} for c in inside],
            source='Approved clue cards and seating')

# The inclusion checklist: every envelope with something to put in it, round by round, in the
# order the envelopes print (table, then character), with a box to tick.
from functools import cmp_to_key
lines = ['# Clue envelope inclusions', '',
         'Everything that goes **inside** a clue envelope with its card, in the order the envelopes '
         'print (table, then character). Tick each box as the envelope is sealed.', '',
         '**Not in any envelope:** the silver compact (the GM hands it over: Scooter at arrival, '
         'Dakota with her Round 1 card) and the photograph of Vale at the microphone (GM, Round 4). '
         'The laboratory report is in Donna\'s Round 3 envelope (Item F).', '',
         '**Round 1:** put each clue envelope at its guest\'s place setting before the meal. **Table envelopes (A4), Rounds 2 and 3:** each table\'s clue envelopes for the round go '
         'into its A4 envelope. **Round 3:** the eight laboratory reports go in Donna\'s own envelope '
         '(Item F); she hands one to every table.', '']
for rnd in range(4):
    rows = sorted((c for c in items if c['category'] == 'clues' and c['round'] == rnd and enclosures(c)),
                  key=lambda c: (c['table'] or 99, c['character'], c['id']))
    lines += ['---', '', f"## Round {rnd} · {len(rows)} envelope{'' if len(rows) == 1 else 's'}", '',
              '| Done | Table | Character | Guest | Put in the envelope |', '|---|---|---|---|---|']
    lines += [f"| [   ] | {c['table']} | {c['character']} | {c['guest']} | {'; '.join(enclosures(c))} |" for c in rows]
    lines.append('')
add('reference-envelope-inclusions', 'gm', 'Clue envelope inclusions', '\n'.join(lines).rstrip(),
    private=True, template='reference', source='Approved clue cards, question notes and props')

add('ballot', 'stationery', 'Accusation slip', 'Who do you think did the murder? What was the motive, means and opportunity? Discuss on your table, then fill in one each.\n\nI accuse:\n\nMotive: why they wanted him dead\n\nMeans: what they used, and how they got it\n\nOpportunity: how they could have done it: were they near?', round=4, quantity=56, template='ballot')
add('notes', 'stationery', 'A private note', 'To:\n\nFrom:\n\nMessage:', quantity=12, template='note')
steps = [dict(r) for r in con.execute('select round,release_order,description from local_clue_release_steps order by round,release_order')]
for step in steps:
    add(f"divider-{step['round']}-{step['release_order']}", 'gm', f"Round {step['round']} · Step {step['release_order']}", step['description'], round=step['round'], private=True, template='divider', source='Local release instructions', order=step['release_order'])
for filename, title in [('gm-run-sheet.md','GM running order'), ('physical-props.md','Physical preparation checklist'),
                        ('round0-spinny-running-order.md','Round 0 — DJ Spinny T running order'),
                        ('round4-closing-sequence.md','Round 4 — the closing sequence'),
                        ('round4-murderer-speech.md','The closing speech (handed over once)')]:
    raw=render_preparation(preparation) if filename=='physical-props.md' else (ROOT/'story'/filename).read_text()
    # The PDF renderer understands Markdown (headings, tables, bullets, quotes, bold), so the
    # prose is passed through intact. Only links are resolved, to their readable label, and
    # backticks dropped; everything else is formatting the renderer draws rather than prints.
    text=re.sub(r'\[([^\]]+)\]\([^\n]+?\)',r'\1',raw).replace('`','')
    # The Round 4 script is handed to Spinny and Donna, so their copies must not name the
    # murderer. Passages between <!-- GM --> and <!-- /GM --> print on the GM's copy alone, and
    # those between <!-- SHARED --> and <!-- /SHARED --> on Spinny's and Donna's alone. The GM
    # reads one continuous script with every name in place, and the shared copies can be
    # rehearsed without learning it. One source file, so the two cannot drift apart.
    if '<!-- GM -->' in text:
        def copy_for(own, other):
            t = re.sub(rf'^<!-- {other} -->\n.*?^<!-- /{other} -->\n?', '', text, flags=re.S | re.M)
            t = re.sub(rf'^<!-- /?{own} -->\n?', '', t, flags=re.M)
            return re.sub(r'\n{3,}', '\n\n', t).strip()
        add('reference-'+filename[:-3], 'gm', title, copy_for('SHARED', 'GM'), private=True,
            template='reference', source='Local approved reference', quantity=2)
        add('reference-'+filename[:-3]+'-gm', 'gm', title + ' (GM copy)', copy_for('GM', 'SHARED'),
            private=True, template='reference', source='Local approved reference', quantity=1)
    else:
        add('reference-'+filename[:-3], 'gm', title, text, private=True, template='reference',
            source='Local approved reference', quantity=1)
lookup='\n\n'.join(f"Table {s['table_number']} · Seat {s['seat_number']}\n{s['guest_name']} — {s['character_name']}" for s in seats)
if pending_guests:
    lookup += '\n\nAwaiting character and seat:\n' + '\n'.join(pending_guests)
unallocated = sorted({i['character'] for i in items if i['guest']=='Unallocated'})
if unallocated:
    lookup += '\n\nCharacters awaiting a player:\n' + '\n'.join(unallocated)
add('guest-lookup','gm','Guest, character & table lookup',lookup,private=True,template='reference',source='Approved local seating')
captured = datetime.now(timezone.utc).isoformat()
snapshot = dict(event=event_details, source=dict(capturedAt=captured, databaseHash=hashlib.sha256(db.read_bytes()).hexdigest(), seatingPlan=plan, clueCount=len(active_clues), description=f'{len(active_clues)} active clue records loaded from the event database.', refresh='A saved print snapshot generated from the local event database.'), items=items, seats=seats, pendingGuests=pending_guests, preparation=preparation['items'], preparationNote=preparation['statusNote'], unallocatedCharacters=sorted({i['character'] for i in items if i['guest']=='Unallocated'}), validation=dict(guests=len(attendees),provisional=sum(g['attendance']=='provisional' for g in attendees),ordinaryCards=sum(i['category']=='clues' for i in items),privateCards=sum(i['category']=='private' for i in items),laboratoryReports=sum(i['template']=='report' for i in items),badges=sum(i['template']=='badge' for i in items),seats=len(seats),tables=len({s['table_number'] for s in seats})))
(APP/'lib/event.json').write_text(json.dumps(snapshot, ensure_ascii=False, indent=2)+'\n')
print(f'Exported {len(items)} printable entries from {len(active_clues)} database clue records; database unchanged.')
