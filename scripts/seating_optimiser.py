"""
seating_optimiser.py

Partitions characters into dinner tables by simulated annealing, maximising the number of
clue conversations that happen between people who sit together.

Public API
----------
optimise(graph, table_size, ...)     → result dict

The graph comes from graph_builder (see scripts/optimise_seating.py for a command-line wrapper).
"""
from __future__ import annotations

import logging
import math
import random
import time
from collections import defaultdict
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Alias map — target names that may appear in slightly non-canonical form
# ---------------------------------------------------------------------------
_ALIASES: dict[str, str] = {
    "Johnny Maxwell":    "Johnny 'Jet' Maxwell",
    "Marshall Monroe":   "Marshall 'Macho' Monroe",
    "Tina Thatcher":     "Tina 'Tank' Thatcher",
    "Rex Steele":        "Rex 'Razor' Steele",
    "Dr Beverly Steele": "Dr. Beverly Steele",
}

_EXCLUDED_NAMES = frozenset({"Vincent Vale", "Game Master"})
_EXCLUDED_TYPES = frozenset({"Host", "Test", "Victim"})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalise(name: str) -> str:
    return _ALIASES.get(name, name)


def _edge_key(a: str, b: str) -> tuple[str, str]:
    return (a, b) if a < b else (b, a)


# ---------------------------------------------------------------------------
# Fix 1 — extracted shared forbidden-pair repair
# ---------------------------------------------------------------------------

def _repair_forbidden(
    tables: list[list[str]],
    fixed: dict[str, int],
    forbidden_set: set[frozenset],
    table_size: int,
    num_tables: int,
) -> None:
    """Repair forbidden-pair violations in-place.

    Makes a best-effort pass: for each violating pair it tries to swap one
    member to another table that doesn't introduce new violations.
    O(attempts × tables × pairs × destinations) — practical for small
    forbidden_set (< 20 pairs); both callers share this logic.
    """
    max_attempts = max(len(tables) * table_size * 2, 20)
    for _attempt in range(max_attempts):
        violation_found = False
        for t_idx, table in enumerate(tables):
            for i in range(len(table)):
                for j in range(i + 1, len(table)):
                    a, b = table[i], table[j]
                    if frozenset([a, b]) not in forbidden_set:
                        continue
                    violation_found = True
                    mover = b if b not in fixed else (a if a not in fixed else None)
                    if mover is None:
                        continue
                    mover_pos = j if mover == b else i
                    for other_t in range(num_tables):
                        if other_t == t_idx:
                            continue
                        for other_pos, other_name in enumerate(tables[other_t]):
                            if other_name in fixed:
                                continue
                            new_bad = any(
                                frozenset([other_name, x]) in forbidden_set
                                for k, x in enumerate(tables[t_idx])
                                if k != mover_pos
                            ) or any(
                                frozenset([mover, x]) in forbidden_set
                                for k, x in enumerate(tables[other_t])
                                if k != other_pos
                            )
                            if not new_bad:
                                tables[t_idx][mover_pos], tables[other_t][other_pos] = \
                                    tables[other_t][other_pos], tables[t_idx][mover_pos]
                                break
                        else:
                            continue
                        break
        if not violation_found:
            break


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Simulated annealing
# ---------------------------------------------------------------------------

def optimise(
    graph: dict[str, Any],
    table_size: int = 6,
    num_tables: int | None = None,
    fixed_seats: dict[str, int] | None = None,
    forbidden_pairs: list[list[str]] | None = None,
    placeholder_names: list[str] | None = None,
    adjacency_pairs: list[list[int]] | None = None,
    adjacency_factor: float = 0.6,
    seed: int | None = None,
    restarts: int = 3,
    steps_per_restart: int = 10_000,
    T0: float = 3.0,
    T_end: float = 0.01,
    time_limit_s: float | None = None,
) -> dict[str, Any]:
    """
    Partition characters into tables maximising total in-table edge weight.

    Parameters
    ----------
    fixed_seats       : {character_name: table_number} — 1-based table indices
    forbidden_pairs   : [[name_a, name_b], ...] — must not share a table
    placeholder_names : additional non-character names to pad to capacity
    adjacency_pairs   : [[table_a, table_b], ...] — 1-based table numbers whose
                        physical positions are adjacent; guests at these tables
                        earn partial credit (adjacency_factor × edge_weight) in
                        the SA objective, so the solver favours placing connected
                        characters at neighbouring tables when they cannot share
                        one.  Enables the +5-8% capture gain from back-to-back
                        table layouts (e.g. T2/T8 adjacent).
    adjacency_factor  : partial-credit multiplier for adjacent-table pairs
                        (default 0.6)
    time_limit_s      : wall-clock budget in seconds; SA exits early if exceeded
    """
    t_start = time.perf_counter()
    deadline: float | None = (t_start + time_limit_s) if time_limit_s else None

    adj: dict[tuple[str, str], int] = graph["_adj"]
    unresolved: list[str] = graph["unresolved_target_names"]
    # graph["nodes"] is already sorted by weighted_degree descending (hub-first)
    seatable_names: list[str] = [n["name"] for n in graph["nodes"]]
    placeholders: list[str] = list(placeholder_names or [])

    all_names: list[str] = seatable_names + placeholders
    N = len(all_names)

    if num_tables is None:
        num_tables = math.ceil(N / table_size)

    capacity = num_tables * table_size
    if capacity < N:
        raise ValueError(
            f"num_tables×table_size ({capacity}) < number of guests ({N})"
        )

    # Pad with unnamed dummies so every table is exactly table_size
    dummy_pad: list[str] = [f"__dummy_{i}__" for i in range(capacity - N)]
    all_names = all_names + dummy_pad
    # Fix 4a — pre-computed set for O(1) dummy membership test in hot loop
    dummy_set: set[str] = set(dummy_pad)

    roster_set = set(all_names)
    fixed: dict[str, int] = {}
    if fixed_seats:
        for name, tbl in fixed_seats.items():
            if name not in roster_set:
                raise ValueError(
                    f"fixed_seats name {name!r} not found in character roster"
                )
            idx = tbl - 1
            if idx < 0 or idx >= num_tables:
                raise ValueError(f"fixed_seats table {tbl} out of range [1,{num_tables}]")
            fixed[name] = idx
        from collections import Counter
        pins_per_table = Counter(fixed.values())
        for t_idx, count in pins_per_table.items():
            if count > table_size:
                raise ValueError(
                    f"Table {t_idx + 1} has {count} fixed seats but table_size is {table_size}"
                )

    forbidden_set: set[frozenset] = set()
    if forbidden_pairs:
        for pair in forbidden_pairs:
            if len(pair) == 2:
                forbidden_set.add(frozenset(pair))

    # Fix 5 — adjacency setup: convert 1-based table pairs to 0-based lookup
    adjacency: dict[int, set[int]] = defaultdict(set)
    adjacency_frozensets: set[frozenset] = set()
    if adjacency_pairs:
        for ta, tb in adjacency_pairs:
            a0, b0 = ta - 1, tb - 1
            if 0 <= a0 < num_tables and 0 <= b0 < num_tables and a0 != b0:
                adjacency[a0].add(b0)
                adjacency[b0].add(a0)
                adjacency_frozensets.add(frozenset([a0, b0]))
    use_adjacency = bool(adjacency_frozensets)

    # ------------------------------------------------------------------
    # Inner helpers (closures over adj, dummy_set, adjacency, ...)
    # ------------------------------------------------------------------

    def aw(a: str, b: str) -> int:
        # Fix 4a — set lookup instead of str.startswith on every hot-loop call
        if a in dummy_set or b in dummy_set:
            return 0
        return adj.get(_edge_key(a, b), 0)

    def table_score(table: list[str]) -> int:
        s = 0
        for i in range(len(table)):
            for j in range(i + 1, len(table)):
                s += aw(table[i], table[j])
        return s

    def adjacent_score(tables: list[list[str]]) -> float:
        """Score contribution from physically adjacent table pairs."""
        if not use_adjacency:
            return 0.0
        s = 0.0
        for fs in adjacency_frozensets:
            ta, tb = tuple(fs)
            for x in tables[ta]:
                for y in tables[tb]:
                    s += adjacency_factor * aw(x, y)
        return s

    def total_score(tables: list[list[str]]) -> float:
        return float(sum(table_score(t) for t in tables)) + adjacent_score(tables)

    def swap_delta(
        tables: list[list[str]], t1: int, p1: int, t2: int, p2: int
    ) -> float:
        """O(table_size) same-table delta + O(adj_tables × table_size) adjacency delta."""
        n1, n2 = tables[t1][p1], tables[t2][p2]
        # Fix 4b — cache others lists once; each is read four times below
        others_t1 = [x for j, x in enumerate(tables[t1]) if j != p1]
        others_t2 = [x for j, x in enumerate(tables[t2]) if j != p2]

        lost1 = sum(aw(n1, x) for x in others_t1)
        gain1 = sum(aw(n2, x) for x in others_t1)
        lost2 = sum(aw(n2, x) for x in others_t2)
        gain2 = sum(aw(n1, x) for x in others_t2)
        delta: float = float((gain1 + gain2) - (lost1 + lost2))

        # Fix 5 — adjacency contribution to the delta
        if use_adjacency:
            # n1 leaves t1 → tables adjacent to t1 (excluding t2) swap n1→n2
            for adj_t in adjacency[t1] - {t2}:
                for y in tables[adj_t]:
                    delta += adjacency_factor * (aw(n2, y) - aw(n1, y))
            # n2 leaves t2 → tables adjacent to t2 (excluding t1) swap n2→n1
            for adj_t in adjacency[t2] - {t1}:
                for y in tables[adj_t]:
                    delta += adjacency_factor * (aw(n1, y) - aw(n2, y))
            # If t1 and t2 are adjacent, handle their mutual cross-table edge changes
            if frozenset([t1, t2]) in adjacency_frozensets:
                for y in others_t2:
                    delta += adjacency_factor * (aw(n2, y) - aw(n1, y))
                for x in others_t1:
                    delta += adjacency_factor * (aw(n1, x) - aw(n2, x))

        return delta

    def violates_forbidden(
        tables: list[list[str]], t1: int, p1: int, t2: int, p2: int
    ) -> bool:
        n1, n2 = tables[t1][p1], tables[t2][p2]
        # After swap: n2 lands at t1, n1 lands at t2
        for j, x in enumerate(tables[t1]):
            if j == p1:
                continue
            if frozenset([n2, x]) in forbidden_set:
                return True
        for j, x in enumerate(tables[t2]):
            if j == p2:
                continue
            if frozenset([n1, x]) in forbidden_set:
                return True
        return False

    def greedy_assignment() -> list[list[str]]:
        """Seed tables by placing highest-degree nodes first at the table
        that gives the greatest marginal weight gain. O(N × T) — fast."""
        tables: list[list[str]] = [[] for _ in range(num_tables)]
        fixed_keys = set(fixed.keys())
        for name, t_idx in fixed.items():
            tables[t_idx].append(name)
        for name in all_names:
            if name in fixed_keys:
                continue
            best_t, best_gain = 0, -1
            for t_idx, table in enumerate(tables):
                if len(table) >= table_size:
                    continue
                gain = sum(aw(name, x) for x in table)
                if gain > best_gain:
                    best_gain, best_t = gain, t_idx
            tables[best_t].append(name)
        # Fix 1 — shared repair helper instead of duplicated inline block
        if forbidden_set:
            _repair_forbidden(tables, fixed, forbidden_set, table_size, num_tables)
        return tables

    def random_assignment(rng: random.Random) -> list[list[str]]:
        """Random shuffle for diversity in later restarts."""
        tables: list[list[str]] = [[] for _ in range(num_tables)]
        fixed_keys = set(fixed.keys())
        for name, t_idx in fixed.items():
            tables[t_idx].append(name)
        free = [n for n in all_names if n not in fixed_keys]
        rng.shuffle(free)
        slots: list[int] = []
        for t_idx in range(num_tables):
            slots.extend([t_idx] * (table_size - len(tables[t_idx])))
        rng.shuffle(slots)
        for name, t_idx in zip(free, slots):
            tables[t_idx].append(name)
        # Fix 1 — shared repair helper
        if forbidden_set:
            _repair_forbidden(tables, fixed, forbidden_set, table_size, num_tables)
        return tables

    # ------------------------------------------------------------------
    rng = random.Random(seed)
    best_tables: list[list[str]] | None = None
    best_score: float = -1.0
    plateau_limit = max(steps_per_restart // 3, 200)

    # Trivial case: single table — no annealing needed
    if num_tables == 1:
        tables = greedy_assignment()
        best_tables = tables
        best_score = total_score(tables)
    else:
        cooling = math.pow(T_end / T0, 1.0 / max(steps_per_restart, 1))
        time_exhausted = False

        for restart_idx in range(restarts):
            # Fix 2 (bonus) — log restart progress so caller can detect hung runs
            logger.info(
                "Restart %d/%d  global_best=%.1f",
                restart_idx + 1, restarts, best_score,
            )
            if restart_idx == 0:
                tables = greedy_assignment()
            else:
                tables = random_assignment(rng)

            score = total_score(tables)
            local_best_score = score
            local_best_tables = [list(t) for t in tables]
            T = T0
            steps_no_improve = 0

            for _step in range(steps_per_restart):
                # Time-aware stopping: check clock every 200 steps
                if deadline is not None and _step % 200 == 0:
                    if time.perf_counter() >= deadline:
                        time_exhausted = True
                        break

                t1 = rng.randrange(num_tables)
                t2 = rng.randrange(num_tables - 1)
                if t2 >= t1:
                    t2 += 1
                p1 = rng.randrange(table_size)
                p2 = rng.randrange(table_size)

                n1, n2 = tables[t1][p1], tables[t2][p2]
                # Fix 3 — don't consume cooling budget on skipped pairs
                if n1 in fixed or n2 in fixed:
                    continue
                if forbidden_set and violates_forbidden(tables, t1, p1, t2, p2):
                    continue

                delta = swap_delta(tables, t1, p1, t2, p2)
                if delta > 0 or rng.random() < math.exp(delta / T):
                    tables[t1][p1], tables[t2][p2] = n2, n1
                    score += delta
                    # Fix 2 — unified plateau / local-best tracking:
                    # "no improve" = no new local peak, regardless of delta sign
                    if score > local_best_score:
                        local_best_score = score
                        local_best_tables = [list(t) for t in tables]
                        steps_no_improve = 0
                    else:
                        steps_no_improve += 1
                else:
                    steps_no_improve += 1

                T *= cooling

                # Plateau early-exit
                if steps_no_improve >= plateau_limit:
                    break

            if local_best_score > best_score:
                best_score = local_best_score
                best_tables = local_best_tables

            if time_exhausted:
                break

    assert best_tables is not None

    # ------------------------------------------------------------------
    # Build response
    # ------------------------------------------------------------------
    total_possible = graph["total_weight"]

    name_to_table: dict[str, int] = {}
    for t_idx, table in enumerate(best_tables):
        for name in table:
            name_to_table[name] = t_idx

    table_results = []
    for t_idx, table in enumerate(best_tables):
        internal_edges = []
        for i in range(len(table)):
            for j in range(i + 1, len(table)):
                a, b = table[i], table[j]
                w = aw(a, b)
                if w > 0:
                    internal_edges.append({"a": a, "b": b, "weight": w})
        internal_edges.sort(key=lambda e: -e["weight"])
        in_w = sum(e["weight"] for e in internal_edges)
        guests = [n for n in table if n not in dummy_set]
        real_pairs = len(guests) * (len(guests) - 1) // 2
        table_results.append({
            "table_number": t_idx + 1,
            "guests": guests,
            "in_table_weight": in_w,
            # Bonus fix — density metric so dummy-padded tables aren't unfairly penalised
            "in_table_weight_per_guest_pair": round(in_w / real_pairs, 3) if real_pairs > 0 else 0.0,
            "internal_edges": internal_edges,
        })

    pair_clues: dict = graph.get("_pair_clues", {})
    cross: list[dict] = []
    for edge in graph["edges"]:
        a, b, w = edge["a"], edge["b"], edge["weight"]
        ta = name_to_table.get(a, -1)
        tb = name_to_table.get(b, -1)
        if ta != tb:
            clues = pair_clues.get(_edge_key(a, b), [])
            cross.append({
                "a": a, "b": b, "weight": w,
                "table_a": ta + 1, "table_b": tb + 1,
                "clues": clues,
            })
    cross.sort(key=lambda e: -e["weight"])

    compute_ms = int((time.perf_counter() - t_start) * 1000)
    total_in = sum(t["in_table_weight"] for t in table_results)
    capture = round(100 * total_in / total_possible, 1) if total_possible > 0 else 0.0
    total_adj = round(adjacent_score(best_tables), 1) if use_adjacency else None

    result: dict[str, Any] = {
        "total_in_table_weight": total_in,
        "total_possible_weight": total_possible,
        "capture_rate_pct": capture,
        "tables": table_results,
        "cross_table_edges": cross,
        "unresolved_target_names": unresolved,
        "compute_time_ms": compute_ms,
    }
    if total_adj is not None:
        result["total_adjacent_weight"] = total_adj
    return result


def optimise_groups(graph, groups, initial, capacities, *, fixed=None,
                    forbidden_pairs=(), original=None, movement_cost=0.35,
                    minimum_occupancy=5, restarts=16, steps=25000, seed=90853):
    """Local extension: indivisible real booking groups, variable capacities and fixed roles.

    Reuses the supplied graph format / edge normalisation. Unlike the original
    single-character swap solver, a couple can never be split by a candidate move.
    Scores the two affected tables, making each step independent of event size.
    Initial state must be feasible; invalid candidates are rejected, not repaired
    after scoring. No physical-adjacency bonus is assumed without a venue layout.
    """
    rng=random.Random(seed)
    fixed=fixed or {}
    original=original or {}
    adj=graph['_adj']
    group_of={n:i for i,g in enumerate(groups) for n in g}
    size=[len(g) for g in groups]
    forb={frozenset((group_of[a],group_of[b])) for a,b in forbidden_pairs}
    if any(len(p)!=2 for p in forb):
        raise ValueError('A required group contains a forbidden pair')
    pins={group_of[n]:t for n,t in fixed.items()}
    if any(pins[group_of[n]]!=t for n,t in fixed.items()):
        raise ValueError('Conflicting fixed seats in a group')
    weights={}
    for (a,b),v in adj.items():
        i,j=group_of[a],group_of[b]
        if i!=j: weights[tuple(sorted((i,j)))]=weights.get(tuple(sorted((i,j))),0)+v
    def members(state,t):return [i for i,x in enumerate(state) if x==t]
    def valid(state,ts):
        for t in ts:
            gs=members(state,t)
            count=sum(size[i] for i in gs)
            if not minimum_occupancy<=count<=capacities[t]:return False
            if any(p.issubset(gs) for p in forb):return False
        return all(state[i]==t for i,t in pins.items())
    def score_table(state,t):
        gs=members(state,t)
        return sum(weights.get(tuple(sorted((i,j))),0) for k,i in enumerate(gs) for j in gs[k+1:])-movement_cost*sum(n in original and original[n]!=t for i in gs for n in groups[i])
    if not valid(initial,range(len(capacities))):raise ValueError('Infeasible initial grouped seating')
    best=list(initial);best_score=sum(score_table(best,t) for t in range(len(capacities)))
    free=[i for i in range(len(groups)) if i not in pins]
    accepted=0
    for restart in range(restarts):
        state=list(best if restart%3 else initial)
        score=sum(score_table(state,t) for t in range(len(capacities)))
        for step in range(steps):
            i,j=rng.sample(free,2)
            t1=state[i]
            t2=state[j] if rng.random()<0.7 else rng.randrange(len(capacities))
            if t1==t2:continue
            before=score_table(state,t1)+score_table(state,t2)
            swap=state[j]==t2 and rng.random()<0.75
            state[i]=t2
            if swap:state[j]=t1
            if not valid(state,(t1,t2)):
                state[i]=t1
                if swap:state[j]=t2
                continue
            delta=score_table(state,t1)+score_table(state,t2)-before
            temp=3.0*(0.015/3.0)**(step/steps)
            if delta>=0 or rng.random()<math.exp(delta/temp):
                score+=delta;accepted+=1
                if score>best_score+1e-8:best=list(state);best_score=score
            else:
                state[i]=t1
                if swap:state[j]=t2
    assert valid(best,range(len(capacities)))
    return {'group_tables':best,'objective':best_score,'accepted_moves':accepted,
            'tables':[[n for i in members(best,t) for n in groups[i]] for t in range(len(capacities))],
            'seed':seed,'restarts':restarts,'steps_per_restart':steps}
