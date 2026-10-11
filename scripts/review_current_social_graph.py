"""Re-score the existing seats without optimising or opening the database for writing.

Roster-agnostic. Derives its expectations from the database rather than asserting
fixed 9 September counts, so it keeps working as characters and guests change.

Adds, beyond the original capture scoring:
  * per-table clue capture counted in whole clues, not just directions
  * per-table case-pillar reachability ("can this table solve it?")
  * mechanical peer-review audits: answerability, coverage/load, name collisions
  * handshakes: every introduction, tell card and third-party mention, checked against
    the recorded human reads in local_handshake_reviews (see handshake_items.py)
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import re
from pathlib import Path
import sqlite3

from graph_builder import build_interaction_graph, load_local_clue_data
from handshake_items import compare as handshake_compare, current_items as handshake_items
from cross_table_notes import audit as notes_audit


# Case pillars transcribed from the GM public conclusion (CLUE_GM_R4). Each pillar
# lists the characters who can supply it first-hand; any one of them satisfies it,
# because the conclusion treats several as independent corroboration.
CASE_PILLARS = [
    ('motive', "Veronica's threatened comeback and the fee claim",
     ['Veronica Vane', 'Brenda Blip', 'Tommy Tech', 'Peter Vale', 'Sabrina Sinclair']),
    ('means', "Beverly's warning and Scooter's sealed delivery",
     ['Dr. Beverly Steele', 'Scooter', 'Veronica Vane']),
    ('opportunity', 'Recognised at the decanter during the cue',
     ['Nikki Neon', 'Dakota Steele', 'Ronnie Reels', 'Vance Vellum']),
    ('forensic', 'Laboratory link between compact and fatal wine',
     ['Inspector Donna Reed', 'Fiona Fringe']),
    ('arrangement', 'The two envelope deliveries identified',
     ['Leo Lights', 'Glenda Gold']),
    ('payment_purpose', 'What the payments bought: distraction and silence',
     ['DJ Spinny T', 'Dakota Steele']),
    ('elimination', 'The alternative dish never reached Vale',
     ['Cassie Chase', 'Dr. Beverly Steele', 'Sheila Sparks', 'Lady Helena de Brissac']),
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percent(numerator, denominator):
    return round(100 * numerator / denominator, 4) if denominator else None


def components(names, pairs):
    adjacency = {name: set() for name in names}
    for a, b in pairs:
        adjacency[a].add(b)
        adjacency[b].add(a)
    remaining = set(names)
    sizes = []
    while remaining:
        queue, seen = [min(remaining)], set()
        while queue:
            node = queue.pop()
            if node in seen:
                continue
            seen.add(node)
            queue.extend(adjacency[node] - seen)
        remaining -= seen
        sizes.append(len(seen))
    return sorted(sizes, reverse=True)


def resolve_plan(db, requested):
    """Default to the single approved plan rather than a hard-coded id."""
    if requested:
        row = db.execute('SELECT * FROM seating_plans WHERE plan_id=?', (requested,)).fetchone()
        if row is None:
            raise SystemExit(f'No seating plan {requested!r}')
        return dict(row)
    rows = [dict(r) for r in db.execute("SELECT * FROM seating_plans WHERE status='approved'")]
    if len(rows) != 1:
        ids = ', '.join(sorted(r['plan_id'] for r in rows)) or '(none)'
        raise SystemExit(f'Expected exactly one approved plan, found {len(rows)}: {ids}. Pass --plan.')
    return rows[0]


def name_collisions(names):
    """Spoken-aloud ambiguity: shared first token, or names differing only by case/punctuation."""
    def clean(tok):
        return re.sub(r"[^a-z]", '', tok.lower())

    def homophone(tok):
        # Roxy / Roxie, Tony / Tonie: trailing y, ie and ey sound identical aloud.
        return re.sub(r"(ie|ey|y)$", '~', clean(tok))

    buckets = {'shared_first_name': defaultdict(list), 'shared_surname': defaultdict(list),
               'homophone_first_name': defaultdict(list)}
    for n in names:
        tokens = [t for t in n.split() if clean(t)]
        if not tokens:
            continue
        buckets['shared_first_name'][clean(tokens[0])].append(n)
        buckets['homophone_first_name'][homophone(tokens[0])].append(n)
        if len(tokens) > 1:
            buckets['shared_surname'][clean(tokens[-1])].append(n)
    out, seen = [], set()
    for kind in ('shared_first_name', 'shared_surname', 'homophone_first_name'):
        for key, group in sorted(buckets[kind].items()):
            if len(group) < 2:
                continue
            sig = (kind, tuple(sorted(group)))
            names_sig = tuple(sorted(group))
            # do not report a homophone group that is already an exact first-name clash
            if kind == 'homophone_first_name' and any(
                    s[1] == names_sig and s[0] == 'shared_first_name' for s in seen):
                continue
            seen.add(sig)
            out.append(dict(kind=kind, key=key, names=sorted(group)))
    return out


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, default=root / 'data/valemeridian-event.sqlite')
    parser.add_argument('--plan', default=None, help='Seating plan id. Default: the approved plan.')
    parser.add_argument('--output', type=Path, default=None,
                        help='Output directory. Default: reports/current-social-graph-<plan>.')
    parser.add_argument('--reachable-weight', type=float, default=0.6,
                        help='Credit for a pillar one planned conversation away (default 0.6).')
    args = parser.parse_args()

    before_hash = digest(args.db)
    db = sqlite3.connect(args.db.resolve().as_uri() + '?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    try:
        plan = resolve_plan(db, args.plan)
        plan_id = plan['plan_id']
        output = args.output or root / f'reports/current-social-graph-{plan_id}'
        seats = [dict(row) for row in db.execute(
            'SELECT guest_name,character_name,table_number,seat_number FROM seat_assignments '
            'WHERE plan_id=? ORDER BY table_number,seat_number', (plan_id,))]
        if not seats:
            raise SystemExit(f'Plan {plan_id!r} has no seat assignments')
        all_seats_before = [tuple(r) for r in db.execute(
            'SELECT * FROM seat_assignments ORDER BY plan_id,table_number,seat_number')]
        roles = {s['character_name']: s for s in seats}
        # One guest changes from Vincent to Peter. Do not count Peter as unseated.
        for combined, alias in [('Vincent Vale / Peter Vale', 'Peter Vale'),
                                ('Vincent Vale / Peter Vale', 'Vincent Vale')]:
            if combined in roles:
                roles.setdefault(alias, roles[combined])

        data = load_local_clue_data(args.db)
        graph = build_interaction_graph(data)
        assert not data['unresolved_target_names'], data['unresolved_target_names']
        names = [n['name'] for n in graph['nodes']]
        unseated = sorted(n for n in names if n not in roles)
        if unseated:
            raise SystemExit(f'Graph characters absent from plan {plan_id}: {unseated}')

        directions = []
        for clue in data['clues']:
            source = data['char_by_id'][clue['CharacterID']]
            for target in clue['resolved_targets']:
                st, tt = roles[source]['table_number'], roles[target['name']]['table_number']
                directions.append(dict(source=source, target=target['name'], round=clue['round_int'],
                                       clue_id=clue['clueid'], source_table=st, target_table=tt,
                                       same_table=st == tt))

        # Independent cross-check against the ordinary cards and their explicit targets.
        # Cards owned by a retired character (for example Sheila Sparks, whose guest is not
        # attending) cannot be played, so they are left out on both sides.
        ordinary = db.execute(
            "SELECT c.clue_id,c.character_name,c.round,c.targets_json FROM clues c "
            "JOIN local_clue_record_kinds k USING(clue_id) WHERE c.status='active' "
            "AND c.round IN (1,2,3) AND k.record_kind='ordinary' AND NOT EXISTS "
            "(SELECT 1 FROM characters ch WHERE ch.character_name=c.character_name AND ch.status='retired')").fetchall()
        explicit = {(r['clue_id'], r['character_name'], r['round'], t)
                    for r in ordinary for t in json.loads(r['targets_json'])}
        derived = {(d['clue_id'], d['source'], d['round'], d['target']) for d in directions}
        assert explicit == derived, dict(only_sql=sorted(explicit - derived)[:10],
                                         only_graph=sorted(derived - explicit)[:10])
        all_pair_rounds = {(min(d['source'], d['target']), max(d['source'], d['target']), d['round'])
                           for d in directions}
        assert len(all_pair_rounds) == graph['total_weight']
        rounds_present = sorted({d['round'] for d in directions})

        round_metrics, workload = [], []
        for rn in rounds_present:
            ds = [d for d in directions if d['round'] == rn]
            pairs = [(e['a'], e['b']) for e in graph['edges'] if rn in e['rounds']]
            within = sum(roles[a]['table_number'] == roles[b]['table_number'] for a, b in pairs)
            local_directions = sum(d['same_table'] for d in ds)
            for name in names:
                incoming = [d for d in ds if d['target'] == name]
                outgoing = [d for d in ds if d['source'] == name]
                partners = sorted({d['source'] for d in incoming} | {d['target'] for d in outgoing})
                cross = [p for p in partners
                         if roles[p]['table_number'] != roles[name]['table_number']]
                workload.append(dict(name=name, guest=roles[name]['guest_name'],
                                     table=roles[name]['table_number'], round=rn,
                                     incoming=len(incoming), outgoing=len(outgoing),
                                     partner_count=len(partners), partners=partners,
                                     cross_partner_count=len(cross), cross_partners=cross,
                                     clue_ids=sorted({d['clue_id'] for d in incoming + outgoing})))
            cur = [w for w in workload if w['round'] == rn]
            round_metrics.append(dict(
                round=rn, pair_rounds=len(pairs), internal_pair_rounds=within,
                cross_pair_rounds=len(pairs) - within, pair_capture_pct=percent(within, len(pairs)),
                directions=len(ds), internal_directions=local_directions,
                cross_directions=len(ds) - local_directions,
                directed_capture_pct=percent(local_directions, len(ds)),
                maximum_partners=max(w['partner_count'] for w in cur),
                maximum_incoming=max(w['incoming'] for w in cur),
                component_sizes=components(names, pairs)))

        within_total = sum(r['internal_pair_rounds'] for r in round_metrics)
        internal_directions = sum(d['same_table'] for d in directions)
        tables = sorted({s['table_number'] for s in seats})

        # ---- NEW: whole-clue capture, and case-pillar reachability, per table ----
        by_clue = defaultdict(list)
        for d in directions:
            by_clue[d['clue_id']].append(d)

        neighbours = defaultdict(set)
        for d in directions:
            neighbours[d['source']].add(d['target'])
            neighbours[d['target']].add(d['source'])

        table_metrics = []
        for table in tables:
            here = {n for n in names if roles[n]['table_number'] == table}
            ds = [d for d in directions if d['source_table'] == table]
            inbound = [d for d in directions if d['target_table'] == table and not d['same_table']]
            local = sum(d['same_table'] for d in ds)

            owned = [c for c, dl in by_clue.items() if dl[0]['source'] in here]
            full = [c for c in owned if all(d['same_table'] for d in by_clue[c])]
            part = [c for c in owned if any(d['same_table'] for d in by_clue[c]) and c not in full]

            # Reachability: tier 1 = owner seated here; tier 2 = one planned conversation away.
            pillars, score = [], 0.0
            for key, label, owners in CASE_PILLARS:
                at_table = sorted(o for o in owners if o in here)
                one_hop = sorted(o for o in owners
                                 if o not in here and (neighbours[o] & here))
                value = 1.0 if at_table else (args.reachable_weight if one_hop else 0.0)
                score += value
                pillars.append(dict(pillar=key, label=label, at_table=at_table,
                                    one_conversation_away=one_hop,
                                    tier='seated' if at_table else ('adjacent' if one_hop else 'absent'),
                                    credit=round(value, 3)))
            per_round = []
            for rn in rounds_present:
                cross = [d for d in directions if d['round'] == rn and not d['same_table']
                         and table in (d['source_table'], d['target_table'])]
                per_round.append(dict(round=rn,
                                      cross_incoming=sum(d['target_table'] == table for d in cross),
                                      cross_outgoing=sum(d['source_table'] == table for d in cross),
                                      distinct_cross_conversations=len(
                                          {tuple(sorted((d['source'], d['target']))) for d in cross})))
            table_metrics.append(dict(
                table=table, seats=sum(s['table_number'] == table for s in seats),
                investigators=len(here), directions=len(ds), internal_directions=local,
                own_card_capture_pct=percent(local, len(ds)),
                cross_outgoing=len(ds) - local, cross_incoming=len(inbound),
                clues_owned=len(owned), clues_fully_captured=len(full),
                clues_partly_captured=len(part),
                clues_not_captured=len(owned) - len(full) - len(part),
                clue_capture_pct=percent(len(full), len(owned)),
                pillars_seated=sum(p['tier'] == 'seated' for p in pillars),
                pillars_adjacent=sum(p['tier'] == 'adjacent' for p in pillars),
                pillars_absent=sum(p['tier'] == 'absent' for p in pillars),
                solve_index_pct=percent(score, len(CASE_PILLARS)),
                pillar_detail=pillars, rounds=per_round))

        # ---- NEW: mechanical peer-review audits ----
        # Contracts are versioned by review round, not by seating plan; the live set
        # is the one still marked source_checked rather than superseded.
        contracts = [dict(r) for r in db.execute(
            'SELECT contract_id,clue_id,target_name,available_by_round,essential,status '
            "FROM clue_answer_contracts WHERE status='source_checked'")]
        clue_round = {r['clue_id']: r['round'] for r in db.execute(
            "SELECT clue_id,round FROM clues WHERE status='active'")}
        late = [c for c in contracts if c['clue_id'] in clue_round
                and clue_round[c['clue_id']] is not None
                and c['available_by_round'] > clue_round[c['clue_id']]]
        # Only question cards need an answer contract. A disclosure card's speaker
        # owns the fact, so absence of a contract there is correct, not a gap.
        contracted = {c['clue_id'] for c in contracts}
        text = {r['clue_id']: r['clue_content'] for r in db.execute(
            "SELECT clue_id,clue_content FROM clues WHERE status='active'")}

        def asks(clue_id):
            tail = (text.get(clue_id) or '').strip().split('\n')[-1]
            return bool(re.search(r'\b(Ask|Find out)\b', tail))

        question_clues = sorted({d['clue_id'] for d in directions if asks(d['clue_id'])})
        disclosure_clues = sorted({d['clue_id'] for d in directions if not asks(d['clue_id'])})
        uncontracted_questions = [c for c in question_clues if c not in contracted]
        never_approached = sorted(n for n in names if not any(d['target'] == n for d in directions))
        overloaded = [w for w in workload if w['incoming'] > 3]
        silent = [dict(name=n, round=rn) for n in names for rn in rounds_present
                  if not any(d['round'] == rn and n in (d['source'], d['target']) for d in directions)]
        audit = dict(
            answerability=dict(contracts_checked=len(contracts),
                               question_clues=len(question_clues),
                               disclosure_clues=len(disclosure_clues),
                               answer_arrives_late=late,
                               question_without_contract=uncontracted_questions),
            coverage=dict(investigators=len(names), never_approached=never_approached,
                          incoming_over_three=overloaded, characters_idle_in_a_round=silent),
            consistency=dict(name_collisions=name_collisions(names),
                             unresolved_targets=data['unresolved_target_names']))
        # Handshakes can't be judged by keyword overlap (tried: far too noisy), so the
        # script only checks each item against a recorded human read of the same text.
        hs_items = handshake_items(db)
        hs = handshake_compare(db, hs_items)

        def brief(it):
            return {k: it.get(k) for k in ('key', 'kind', 'clue_id', 'owner', 'subject', 'round', 'text', 'note')}
        audit['handshake'] = dict(
            items=len(hs_items), registry_present=hs['registry_present'],
            kinds=dict(Counter(i['kind'] for i in hs_items)),
            reviewed_ok=len(hs['reviewed']), by_design=[brief(i) for i in hs['by_design']],
            open_gaps=[brief(i) for i in hs['gaps']], unread=[brief(i) for i in hs['unread']],
            changed_since_review=[brief(i) for i in hs['changed']], retired_reviews=hs['retired'])

        # Pre-printed question notes for cross-table conversations: each must match its card.
        n_cards, _, n_ok, n_stale, n_orphan, n_missing = notes_audit(db)
        audit['cross_table_notes'] = dict(cards=len(n_cards), current=len(n_ok), stale=n_stale,
                                          orphaned=n_orphan, missing=[f'{c}->{t}' for c, t in n_missing])

        assert [tuple(r) for r in db.execute(
            'SELECT * FROM seat_assignments ORDER BY plan_id,table_number,seat_number')] == all_seats_before
    finally:
        db.close()

    after_hash = digest(args.db)
    assert before_hash == after_hash, 'Database changed during read-only review'

    stored_capture = plan['clue_capture']
    totals = dict(
        investigators=len(names), seats=len(seats), tables=len(tables),
        unique_pairs=len(graph['edges']), pair_rounds=graph['total_weight'],
        internal_pair_rounds=within_total, cross_pair_rounds=graph['total_weight'] - within_total,
        pair_capture_pct=percent(within_total, graph['total_weight']),
        directions=len(directions), internal_directions=internal_directions,
        cross_directions=len(directions) - internal_directions,
        directed_capture_pct=percent(internal_directions, len(directions)),
        clues_in_graph=len(by_clue),
        clues_fully_captured=sum(t['clues_fully_captured'] for t in table_metrics),
        clue_capture_pct=percent(sum(t['clues_fully_captured'] for t in table_metrics), len(by_clue)),
        mean_solve_index_pct=round(sum(t['solve_index_pct'] for t in table_metrics) / len(table_metrics), 2),
        every_investigator_approached=not never_approached,
        all_rounds_component_sizes=components(names, [(e['a'], e['b']) for e in graph['edges']]))

    result = dict(
        database=str(args.db.resolve()), database_sha256_before=before_hash,
        database_sha256_after=after_hash, database_unchanged=True,
        plan_id=plan_id, plan_name=plan['plan_name'], plan_status=plan['status'],
        method='graph_builder.load_local_clue_data + build_interaction_graph; fixed-seat scoring, no optimiser call',
        capture_definition='One undirected pair per distinct round; two reciprocal cards in the same round count once.',
        directed_capture_definition='Each ordinary clue direction counted separately.',
        clue_capture_definition='A clue is fully captured when every target of that clue sits at its owner’s table.',
        solve_index_definition=(
            'Share of the seven CLUE_GM_R4 case pillars reachable from the table. A pillar scores 1.0 '
            'when an owner is seated there and %.2f when an owner is one planned conversation away. '
            'It measures evidence access, not a calibrated probability of solving.' % args.reachable_weight),
        reachable_weight=args.reachable_weight,
        scope='Active explicit ordinary guest directions in Rounds 1–3. Excludes arrival mingling, GM facilitation, the laboratory artifact and closing performances.',
        stored_plan_capture_pct=(100 * stored_capture) if stored_capture is not None else None,
        stored_plan_captured_weight=plan['clue_weight'],
        totals=totals, rounds=round_metrics,
        hotspots=sorted([w for w in workload if w['partner_count'] >= 4],
                        key=lambda w: (w['round'], -w['cross_partner_count'], w['name'])),
        workload=workload, tables=table_metrics, case_pillars=[
            dict(pillar=k, label=l, owners=o) for k, l, o in CASE_PILLARS],
        audit=audit, seating=seats, graph=graph, directions=directions,
        limitations=[
            'Capture is seating convenience, not the percentage of facts actually heard or understood.',
            'These are suggested conversations. Incoming/outgoing describes the named direction, not a guaranteed meeting.',
            'The solve index measures evidence access from a table, not a probability. It assumes every planned conversation is attempted and ignores unplanned mingling, which in play is a major route.',
            'Four partners is a workload flag for rehearsal, not an automatic failure.',
            'A connected graph does not guarantee that all evidence travels to every guest.'])

    output.mkdir(parents=True, exist_ok=True)
    (output / 'analysis.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')

    # ---- generated report; no hard-coded roster prose ----
    L = [f"# Vale Meridian — social graph, clue capture and table solve index",
         '',
         f"Read-only review of plan **{plan_id}** ({plan['plan_name']}, status {plan['status']}). "
         f"No optimisation, seat changes, clue changes or database writes.",
         '',
         f"**Pair capture {totals['pair_capture_pct']:.1f}%** "
         f"({within_total}/{graph['total_weight']} pair-rounds). "
         f"**Directed capture {totals['directed_capture_pct']:.1f}%** "
         f"({internal_directions}/{len(directions)} card directions). "
         f"**Whole-clue capture {totals['clue_capture_pct']:.1f}%** "
         f"({totals['clues_fully_captured']}/{totals['clues_in_graph']} clues with every target local).",
         '',
         f"{len(names)} investigators, {len(seats)} seats, {len(tables)} tables.",
         '']
    if stored_capture is None:
        L += [f"> The plan record stores no capture score (`clue_capture` is NULL), so there is no "
              f"historical figure to compare against. The scores above are computed fresh.", '']
    else:
        L += [f"> The plan record stores {100*stored_capture:.1f}% "
              f"({plan['clue_weight']} weight) from an earlier network.", '']

    L += ['## Capture by round', '',
          '| Round | Same-table pairs | Pair capture | Same-table directions | Directed capture | Cross-table |',
          '|---|---:|---:|---:|---:|---:|']
    for r in round_metrics:
        L.append(f"| {r['round']} | {r['internal_pair_rounds']}/{r['pair_rounds']} | "
                 f"{r['pair_capture_pct']:.1f}% | {r['internal_directions']}/{r['directions']} | "
                 f"{r['directed_capture_pct']:.1f}% | {r['cross_directions']} |")
    L.append(f"| **All** | **{within_total}/{graph['total_weight']}** | "
             f"**{totals['pair_capture_pct']:.1f}%** | **{internal_directions}/{len(directions)}** | "
             f"**{totals['directed_capture_pct']:.1f}%** | **{totals['cross_directions']}** |")

    L += ['', '## Clue capture per table', '',
          'A clue is *fully captured* when every target named on it sits at its owner’s table. '
          'Partly captured means some targets are local and some elsewhere.', '',
          '| Table | Seats | Clues owned | Fully captured | Partly | Not captured | Clue capture |',
          '|---|---:|---:|---:|---:|---:|---:|']
    for t in table_metrics:
        L.append(f"| {t['table']} | {t['seats']} | {t['clues_owned']} | {t['clues_fully_captured']} | "
                 f"{t['clues_partly_captured']} | {t['clues_not_captured']} | {t['clue_capture_pct']:.1f}% |")

    L += ['', '## Table solve index', '',
          f"Seven case pillars are taken from the GM public conclusion (CLUE_GM_R4). A pillar scores "
          f"1.0 when one of its owners is seated at the table and {args.reachable_weight:.2f} when an "
          f"owner is one planned conversation away. **This is evidence access, not a probability.**", '',
          '| Table | Pillars seated | One conversation away | Absent | Solve index |',
          '|---|---:|---:|---:|---:|']
    for t in sorted(table_metrics, key=lambda x: -x['solve_index_pct']):
        L.append(f"| {t['table']} | {t['pillars_seated']} | {t['pillars_adjacent']} | "
                 f"{t['pillars_absent']} | {t['solve_index_pct']:.1f}% |")
    L += ['', f"Mean across tables: **{totals['mean_solve_index_pct']:.1f}%**.", '',
          '### Pillars absent from each table', '']
    for t in table_metrics:
        missing = [p['label'] for p in t['pillar_detail'] if p['tier'] == 'absent']
        L.append(f"- **Table {t['table']}** — " + (', '.join(missing) if missing else 'none'))

    L += ['', '## Table traffic', '',
          '| Table | Seats / investigators | Own directions | Local | Own-card capture | Outgoing | Incoming |',
          '|---|---:|---:|---:|---:|---:|---:|']
    for t in table_metrics:
        L.append(f"| {t['table']} | {t['seats']} / {t['investigators']} | {t['directions']} | "
                 f"{t['internal_directions']} | {t['own_card_capture_pct']:.1f}% | "
                 f"{t['cross_outgoing']} | {t['cross_incoming']} |")

    L += ['', '## Workload hotspots', '',
          'Flag: four or more distinct conversation partners in one round.', '',
          '| Round | Character — guest | Table | Partners | Across tables |',
          '|---|---|---:|---:|---:|']
    for w in result['hotspots']:
        L.append(f"| {w['round']} | {w['name']} — {w['guest']} | {w['table']} | "
                 f"{w['partner_count']} | {w['cross_partner_count']} |")
    if not result['hotspots']:
        L.append('| — | none | | | |')

    L += ['', '## Peer-review audit', '']
    a = audit
    L.append(f"**Answerability.** {a['answerability']['contracts_checked']} live answer contracts cover "
             f"{a['answerability']['question_clues']} question cards; "
             f"{a['answerability']['disclosure_clues']} disclosure cards need none. "
             f"{len(a['answerability']['answer_arrives_late'])} answers not available by the asking round; "
             f"{len(a['answerability']['question_without_contract'])} question cards without a contract.")
    for c in a['answerability']['question_without_contract'][:20]:
        L.append(f"- question without answer contract: `{c}`")
    for c in a['answerability']['answer_arrives_late'][:20]:
        L.append(f"- `{c['clue_id']}` → {c['target_name']}: answer available round "
                 f"{c['available_by_round']}, asked round {clue_round.get(c['clue_id'])}")
    L.append('')
    L.append(f"**Coverage.** {len(a['coverage']['never_approached'])} investigators never approached; "
             f"{len(a['coverage']['incoming_over_three'])} character-rounds with more than three incoming; "
             f"{len(a['coverage']['characters_idle_in_a_round'])} character-rounds with no direction at all.")
    for n in a['coverage']['never_approached']:
        L.append(f"- never approached: {n}")
    for w in a['coverage']['incoming_over_three']:
        L.append(f"- {w['name']} round {w['round']}: {w['incoming']} incoming")
    L.append('')
    L.append(f"**Consistency.** {len(a['consistency']['name_collisions'])} spoken-name collisions; "
             f"{len(a['consistency']['unresolved_targets'])} unresolved clue targets.")
    for c in a['consistency']['name_collisions']:
        L.append(f"- {c['kind']}: {', '.join(c['names'])}")

    h = a['handshake']
    L.append('')
    L.append(f"**Handshakes.** {h['items']} items ({', '.join(f'{v} {k}' for k, v in sorted(h['kinds'].items()))}): "
             f"{h['reviewed_ok']} read and fine, {len(h['by_design'])} by design, {len(h['open_gaps'])} open gaps, "
             f"{len(h['unread'])} never read, {len(h['changed_since_review'])} changed since they were read."
             + ('' if h['registry_present'] else ' No review record exists yet.'))
    for label, rows in (('open gap', h['open_gaps']), ('changed since read', h['changed_since_review']),
                        ('never read', h['unread'])):
        for it in rows[:30]:
            L.append(f"- {label}: R{it['round']} {it['owner']} → {it['subject']} (`{it['clue_id']}`, {it['kind']})"
                     + (f" — {it['note']}" if it.get('note') else ''))
        if len(rows) > 30:
            L.append(f"- … {len(rows) - 30} more {label}")
    if h['open_gaps'] or h['unread'] or h['changed_since_review']:
        L.append('- Read these, then record verdicts with `scripts/record_handshake_reviews.py`.')

    L += ['', '## Limitations', '']
    L += [f"- {x}" for x in result['limitations']]
    L.append('')
    (output / 'review.md').write_text('\n'.join(L))
    print(f"plan            : {plan_id} ({plan['status']})")
    print(f"investigators   : {len(names)}  seats: {len(seats)}  tables: {len(tables)}")
    print(f"directions      : {len(directions)}  pair-rounds: {graph['total_weight']}")
    print(f"Pair capture    : {totals['pair_capture_pct']:.1f}%")
    print(f"directed capture: {totals['directed_capture_pct']:.1f}%")
    print(f"clue capture    : {totals['clue_capture_pct']:.1f}%")
    print(f"mean solve index: {totals['mean_solve_index_pct']:.1f}%")
    ctn = audit['cross_table_notes']
    print(f"question notes  : {ctn['current']} current, {len(ctn['stale'])} stale, {len(ctn['orphaned'])} orphaned, "
          f"{len(ctn['missing'])} missing (scripts/cross_table_notes.py)")
    print(f"wrote           : {output}")


if __name__ == '__main__':
    main()
