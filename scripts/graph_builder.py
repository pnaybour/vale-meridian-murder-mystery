"""
graph_builder.py

Reads the clue network from the event database and builds the interaction graph the other
tools score: who is sent to whom, in which round, by which card.

Public API
----------
load_local_clue_data(path, rounds)
    → dict with keys: chars, clues, char_by_id, char_by_name,
                      char_details, unresolved_target_names

build_interaction_graph(data)
    → dict with keys: nodes, edges, total_weight
"""
from __future__ import annotations


from collections import defaultdict
from typing import Any

from seating_optimiser import _ALIASES, _EXCLUDED_NAMES, _EXCLUDED_TYPES

# Minimum character-name length used in the conservative target-inference
# heuristic.  Short names (e.g. "Ed", "Amy") are too noisy to auto-match.
_INFER_MIN_LEN = 5


def _norm(name: str) -> str:
    """Normalise a raw target string through the seating-optimiser alias table."""
    return _ALIASES.get(name, name)



def build_interaction_graph(data: dict[str, Any]) -> dict[str, Any]:
    """Build an enriched undirected weighted interaction graph.

    Richer than seating_optimiser.build_graph(): includes per-edge clueids,
    plotids, and per-node degree / weighted_degree metrics.

    Parameters
    ----------
    data : dict returned by load_clue_data()

    Returns
    -------
    dict with keys:
        nodes        – [{name, CharacterID, degree, weighted_degree}]
        edges        – [{a, b, weight, rounds, clueids, plotids}]
        total_weight – sum of all edge weights
    """
    pair_rounds:  dict[tuple, set] = defaultdict(set)
    pair_clueids: dict[tuple, set] = defaultdict(set)
    pair_plotids: dict[tuple, set] = defaultdict(set)
    char_by_id = data["char_by_id"]

    def ekey(a: str, b: str) -> tuple:
        return (a, b) if a < b else (b, a)

    for clue in data["clues"]:
        src_name = char_by_id.get(clue["CharacterID"])
        if not src_name:
            continue
        round_int = clue["round_int"]
        for tgt in clue["resolved_targets"]:
            tname = tgt["name"]
            if tname == src_name:
                continue
            key = ekey(src_name, tname)
            pair_rounds[key].add(round_int)
            if clue.get("clueid"):
                pair_clueids[key].add(clue["clueid"])
            if clue.get("plotid_corrected"):
                pair_plotids[key].add(clue["plotid_corrected"])

    wdeg: dict[str, int] = defaultdict(int)
    deg:  dict[str, int] = defaultdict(int)
    edges: list[dict]    = []

    for (a, b), rset in pair_rounds.items():
        w = len(rset)
        wdeg[a] += w
        wdeg[b] += w
        deg[a]  += 1
        deg[b]  += 1
        edges.append({
            "a": a, "b": b, "weight": w,
            "rounds":  sorted(rset),
            "clueids": sorted(pair_clueids[(a, b)]),
            "plotids": sorted(pair_plotids[(a, b)]),
        })

    nodes = [
        {
            "name":            ch["Name"],
            "CharacterID":     ch["CharacterID"],
            "degree":          deg[ch["Name"]],
            "weighted_degree": wdeg[ch["Name"]],
        }
        for ch in data["chars"]
    ]
    nodes.sort(key=lambda n: -n["weighted_degree"])

    return {
        "nodes":        nodes,
        "edges":        edges,
        "total_weight": sum(e["weight"] for e in edges),
    }


def load_local_clue_data(path, rounds=(1, 2, 3)):
    """Read-only SQLite adapter. Explicit active targets only; never infer from prose.

    Returns the original shared builder's shape. Restored supporting clues are
    included whether or not an old upstream canonical flag was populated.
    """
    import sqlite3
    import json
    conn=sqlite3.connect('file:'+str(path)+'?mode=ro',uri=True)
    conn.row_factory=sqlite3.Row
    try:
        chars=[{'CharacterID':r['character_id'],'Name':r['character_name'],'Type':r['character_type']}
               for r in conn.execute("SELECT * FROM characters WHERE status='active'")
               if r['character_name'] not in _EXCLUDED_NAMES and r['character_type'] not in _EXCLUDED_TYPES]
        byname={c['Name']:c['CharacterID'] for c in chars}
        byid={c['CharacterID']:c['Name'] for c in chars}
        clues=[];unresolved=set()
        for r in conn.execute("SELECT * FROM clues WHERE status='active' AND round IN (1,2,3) ORDER BY round,clue_id"):
            if r['round'] not in rounds or r['character_id'] not in byid:continue
            targets=[]
            for raw in json.loads(r['targets_json']):
                n=_norm(raw)
                if n in byname:targets.append({'name':n,'CharacterID':byname[n],'inferred':False})
                else:unresolved.add(n)
            clues.append({'CharacterID':r['character_id'],'round_int':r['round'],'clueid':r['clue_id'],
                          'plotid_corrected':r['plot_id'],'resolved_targets':targets})
        return {'chars':chars,'clues':clues,'char_by_id':byid,'char_by_name':byname,
                'char_details':{c['CharacterID']:c for c in chars},'unresolved_target_names':sorted(unresolved)}
    finally:conn.close()
