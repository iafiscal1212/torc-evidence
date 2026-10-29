# TORC evidence — 24 previously-unknown GBD instances decided

Public evidence for [Udopia/gbd issue #40](https://github.com/Udopia/gbd/issues/40).

**22 xorshift instances (SAT Competition 2026 submissions, verdict `unknown`
in the Global Benchmark Database) are SAT**, with 49 preimages (32-bit
seeds), and **2 binary-encoded coloring instances are UNSAT**, proven by
exhaustive exact search with two independent implementations.

The solver engine (TORC-SAT) remains **private**. This repository contains
only the evidence and the minimal verification code needed to check it.

## Verify it yourself

Requires Python 3.9+ and `pip install python-sat`.

```bash
git clone https://github.com/iafiscal1212/torc-evidence.git
cd torc-evidence

# All 49 preimages, second opinion (Glucose4 + clause-by-clause model
# validation against the ORIGINAL CNF):
python experiments/xorshift_independent_verify.py

# Structural report (xorshift):
cat experiments/results/xorshift_recon.md

# Coloring reconstruction and proof chain:
cat experiments/results/gbd_witness_report.md

# Full report for GBD:
cat docs/GBD_REPORT.md
```

Expected output: `49/49 seeds validate` and
`ALL 22 INSTANCES CONFIRMED SAT with independently verified witnesses`.

## Contents

- `experiments/results/xorshift_brute_results.json` — all 49 preimages
  (complete lists, exhaustive 2^32 bitsliced sweep).
- `experiments/results/xorshift_recon.md` — structural reconstruction of
  the xorshift generator (32-bit seed input, Marsaglia xorshift32
  (13,17,5) stream, ARX whitening with 32-bit ripple-carry adders).
- `experiments/results/gbd_witness_report.md` — binary color-encoding
  reconstruction and the exhaustive-search UNSAT proofs (DSATUR 725/369
  nodes + MRV DPLL 453/391 nodes, independently re-confirmed).
- `experiments/` — the verification and attack scripts.
- `benchmarks/external/gbd_unknown/` — the original CNF instances
  (downloaded from GBD; see `manifest.json` for instance hashes).

## License

All Rights Reserved — Carmen Esteban / IAFISCAL & PARTNERS
(caresment@gmail.com). Free for academic research and education;
commercial use requires a written license. Patent application pending
before the Spanish Patent and Trademark Office (OEPM).

## Update (2026-10-28): 6 more decided instances (29 total)

- 5 hamiltonian instances (`x9-11026`, `x9-11064`, `x9-11092`, `x9-12038`,
  `x9-12073`): **SAT**, witness models in
  `experiments/results/gbd_witness_x9-*.model`, all re-validated with
  `validate_model` against the original CNF.
- agile `bench_12179.smt2.cnf`: **SAT**, model with 878,946 literals
  (`experiments/results/gbd_witness_bench_12179.smt2.model`), validated.

## Update (2026-10-29): MVRoundRobin — UNSAT by pigeonhole (30 total)

`MVRoundRobin_n14_d10_v4`: full round-robin of 14 teams in only 10 days.
**UNSAT by design, not by a solver.** Two mechanically verified arguments:
91 matches in 40 slots (91 > 40), and 13 days needed vs 10 available
(13 > 10). Proof in `experiments/results/MVR_DESIGN_PROOF.md`,
verification script `experiments/gbd_mvr_decode.py` (all checks pass).
