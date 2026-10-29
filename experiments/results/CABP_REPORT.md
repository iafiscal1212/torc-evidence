# CABP attack report: can_445 and nos6 (2026-10-29)

Mission: attack the open cyclic-antibandwidth values of `can_445` and
`nos6` (SAT-CAB benchmark, arXiv:2601.04239), instances
`cabp-P-can__445.mtx.rnd-k94/k106` and `cabp-V-nos6.mtx.rnd-k331`.
All work is in `experiments/` (no solver-core changes, no commits).

## Results summary

| Graph | Literature [LB, UB] | This attack | New bounds |
|---|---|---|---|
| can_445 | [87, 120] | omega = 4, clique counting | **CAB <= 111** |
| nos6 | [328, 337] | compatibility-cycle argument | **CAB <= 336** |
| nos6 | | diagonal-parity construction | witness 322 (< 328, honest) |

No SAT witness was found for k = 94 / 106 (can_445) or k = 331 (nos6);
no UNSAT proof for those k either. Details and budgets below.

## 1. Graph structure (verified by `cabp_constructive.py` / inline)

- `can_445`: n = 445, m = 1682, degrees 3..12 (avg 7.56), connected,
  1580 triangles, degeneracy 5, **omega = 4** (Tomita + independent
  brute force over neighborhoods; witness K4 = {314, 321, 360, 366},
  1883 K4s in total).
- `nos6`: n = 675, m = 1290, degrees 2..4, connected, bipartite
  (337/338), girth 4, degeneracy 2. It is exactly the **L-shaped grid
  30x30 minus the 15x15 quadrant** {i >= 15, j >= 15}: coordinates were
  recovered from BFS distances to the corners (0,0)=v1, (29,0), (0,29)
  and every edge verifies as a unit 4-neighbor grid edge.

## 2. CNF structure (decoded with torc_sa's `recognize_antibandwidth`)

`x_{v,p} = v + n*p` grid verified exactly (n ALO clauses of width n,
disjoint, covering 1..n^2; aux clauses of width 5 (can_445) / 3 (nos6)).
The distance constraints are NOT direct binaries between grid vars
(only 15 such exist); they are encoded as the paper's "cyclic ladder":
AMO sequences over positions encoded with sequential-counter auxiliaries
(ternary chains, e.g. `(x_{v,p} + R - R')`), plus 222 unit clauses of
symmetry breaking (contiguous var range). Total 5.0M / 5.1M / 9.0M
clauses.

## 3. New upper bound: CAB(can_445) <= 111

`experiments/cabp_clique_bound.py` (exit 0): verifies the K4, verifies
omega = 4 by exhaustive neighborhood search, and applies the counting
argument: r clique vertices on an n-cycle with pairwise cyclic distance
>= k need r*k <= n, so k <= floor(445/4) = 111. Previously reported UB
was 120. Note k = 111 forces the K4 gaps to be exactly {111,111,111,112};
an attempted strengthening to 110 via common-neighbor exclusion fails
(every K4 has at most 2 common neighbors per pair, and ~112 positions
remain available for any 3-of-4-adjacent vertex).

## 4. New upper bound: CAB(nos6) <= 336

`experiments/cabp_nos6_ub336.py` (exit 0). n = 675 odd: CAB = 337 would
force every edge to cyclic distance exactly 337. Positions at cyclic
distance 337 differ by +/-337 mod 675; since gcd(337, 675) = 1 the
compatibility graph is a single Hamiltonian cycle C_675 (verified by
stepping). A 337-labeling would embed nos6 into C_675, impossible
because nos6 has max degree 4 (560 degree-4 vertices verified).

## 5. Constructive lower bound attempt: nos6 >= 322

`experiments/cabp_constructive.py`: diagonal-parity labeling of the
L-grid (even diagonals s = i+j on positions [0,337), odd on [337,675),
ascending) achieves min cyclic distance **322**, saved as
`experiments/results/cabp_nos6_diag322.label`. All 32 natural order
variants were enumerated; 322 is the best of the family. The literature
LB is 328 (metaheuristic, hours of C code), so this is NOT an
improvement -- reported for completeness.

## 6. Negative results (witness search, all with budgets)

| Attempt | Target | Budget | Outcome |
|---|---|---|---|
| z3 direct CSP (Distinct + edge windows, symmetry broken) | can_445 k=94 | 900 s | unknown (timeout) |
| z3 direct CSP | nos6 k=331 | 900 s | unknown (timeout) |
| min-conflicts + tabu + 2-opt swaps (`cabp_local_search.py`) | can_445 k=94 | 900 s, 2.7M steps | best 58 conflicted vertices |
| same, seed 21 | can_445 k=94 | 1500 s, 4.5M steps, 43 restarts | no witness |
| same | can_445 k=88 (calibration) | 300 s | NOT found (best 124) |
| same | nos6 k=331 | 900 s, 3.2M steps | best 203 conflicted |
| same, from 322 seed | nos6 k=331/323 | 600 s | no improvement (see 7) |
| z3 rank-window (block form, difference logic) | nos6 k=325 | 60 s | unknown (timeout) |
| rank-window min-conflicts (`cabp_rank_ls.py`) | nos6 k=324 | 1500 s, 7.1M steps | no witness (seed plateau at 42 violated edges never descended) |
| difference-constraint relaxation (Bellman-Ford) | nos6 k=331..337 | seconds | feasible (too weak: ignores permutation) |

Calibration point: the local search cannot even reproduce the known
LB 87/88 for can_445 in 5-15 min, i.e. it is strictly weaker than the
literature metaheuristics (MS-GVNS / HABC-CAB). A competitive witness
hunt needs a C implementation; that is out of scope here.

## 7. Why the 322 seed does not polish upward (nos6)

In block form (E on [0,337), O on [337,675)) an edge (e,o) is satisfied
iff r_o - r_e in [k-337, 675-337-k]. The 322 construction's edge
rank-diffs span [-15,16] (width 32) but k = 323 already needs width 30
and k = 331 needs width 14. The violated edges form whole diagonal
boundaries (s = 27-30); unit-rank swaps shift the violation along the
boundary (measured delta +2 for the canonical fix), so single-swap
min-conflicts has no descent direction -- the repair is global
(redistributing diagonal sizes between blocks), which local search does
not express. The difference-logic relaxation stays feasible up to
k = 337, so no cheap refutation either.

## 8. Validation pipeline (ready, unused)

`experiments/cabp_validate.py`: fixes the n^2 grid vars of a candidate
labeling as assumptions (trying all 2n dihedral transforms against the
symmetry-breaking units first) and asks Glucose3 to extend to a full
model of the ORIGINAL CNF; on SAT writes
`experiments/results/cabp_witness_<instance>.model`. No witness reached
this stage.

## 9. Open ends

- k = 94 / 106 (can_445) and k = 331 (nos6) remain UNKNOWN.
- can_445: CAB in [87, 111]. nos6: CAB in [328, 336].
- k = 336 for nos6 = subgraph embedding of the L-grid into the
  4-regular circulant C(675; 336, 337) -- as hard as the original
  problem, but the circulant structure (CRT: 675 = 25*27) might admit a
  direct construction or refutation; not attempted.
