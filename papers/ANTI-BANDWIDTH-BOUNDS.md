# Improved Upper Bounds for the Cyclic Anti-Bandwidth Number of Two Graphs

**Carmen Esteban — IAFISCAL & PARTNERS**
*Technical note, 30 October 2026*

## Abstract

We report improved upper bounds for the cyclic anti-bandwidth number
(CAB) of two benchmark graphs, with mechanically verified certificates.
For `can_445.mtx` we prove CAB ≤ 109 (previous interval [87, 120]), and
for `nos6.mtx` we prove CAB ≤ 330 (previous interval [328, 337]).
All bounds come with executable verification scripts in the public
evidence repository (https://github.com/iafiscal1212/torc-evidence).

## 1. Results

| Graph | Previous bound | New upper bound | Certificate |
|---|---|---|---|
| `can_445.mtx` | CAB ∈ [87, 120] | **CAB ≤ 109** | (i) k=111 UNSAT by two independent solvers; (ii) k=110 UNSAT by a complete cube-and-conquer over all 168 cubes (all UNSAT) |
| `nos6.mtx` | CAB ∈ [328, 337] | **CAB ≤ 330** | Analytic refutation of k=331/332/333 via the multiplier/folding bound |

## 2. Proof for can_445

The anti-bandwidth number of a graph with a clique of size 4 forces
4k ≤ 445, so CAB ≤ 111. A clique of size 4 is verified exhaustively in
`experiments/cabp_clique_bound.py` (Tomita + brute force over all
neighborhoods, maximum degree 12). For k=111 the encoded instance is
UNSAT by two independent solvers (Glucose3 and Cadical195). For k=110,
a complete cube-and-conquer over all 168 cubes of the gap assignments
for the 4-clique yields UNSAT in every cube (`experiments/cabp_cubes_can445.py`).

## 3. Proof for nos6

For k=337, the compatibility graph is a single 675-cycle (gcd(337,675)=1),
so any 337-labeling embeds nos6 into a degree-2 cycle, impossible because
nos6 has 560 vertices of degree 4 (`experiments/cabp_nos6_ub336.py`).
For k ≥ 331, the multiplier/folding bound gives bw_c(nos6) ≤ 675 − 2k ≤ 13,
contradicting bw_c(nos6) ≥ 15 (the L 30×30 grid minus the 15×15 quadrant
contains P15×P15 with circular bandwidth ≥ 15). Hence CAB ≤ 330
(`experiments/cabp_nos6_ub330.py`). The folding/multiplier method is
exhausted at 330 (no multiplier does better, verified by exhaustive sweep).

## 4. Verification and reproducibility

All certificates are executable and public:
https://github.com/iafiscal1212/torc-evidence

- `experiments/cabp_clique_bound.py` — clique verification and CAB(can_445) ≤ 111.
- `experiments/cabp_cubes_can445.py` — all 168 cubes UNSAT, CAB(can_445) ≤ 109.
- `experiments/cabp_nos6_ub336.py` — degree argument, CAB(nos6) ≤ 336.
- `experiments/cabp_nos6_ub330.py` — multiplier/folding, CAB(nos6) ≤ 330.

## 5. Related work

- SAT-CAB paper (arXiv:2601.04239) — the benchmark instances and the
  previous bounds [87, 120] and [328, 337].
- Urquhart (1987) and Ben-Sasson–Wigderson (2001) — resolution lower
  bounds for Tseitin formulas, the context of the TORC-SAT project.
- Harper (1966) / Chvátalová (1975) — bandwidth of grid graphs.

## 6. Notes

The `can445_is109.txt` file is not a bijection and therefore does not
yield a lower-bound improvement. All other bounds reported here are
verified by executable checks against the original instances.
