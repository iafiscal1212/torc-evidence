# Report to the Global Benchmark Database: 24 previously-unknown instances decided

**Date:** 2026-10-28
**Contact:** Carmen Esteban / IAFISCAL & PARTNERS — caresment@gmail.com
**Repository (all evidence, scripts and raw data):** https://github.com/iafiscal1212/torc-evidence

## Summary

We decided **24 CNF instances that GBD lists with verdict `unknown`**:
22 xorshift instances (track `submissions_2026`, author "zhenwei",
family `xor-shifting`) are **SAT**, and 2 binary-encoded graph-coloring
instances are **UNSAT**. Every verdict is backed by independently
verifiable evidence and reproduced end-to-end.

- SAT instances: **49 preimages (32-bit seeds)**. Verified twice by
  independent code paths: (a) full-model validation against the original
  CNF, and (b) seed bits pinned as unit clauses in the ORIGINAL CNF,
  solved with Glucose4, model re-validated clause by clause.
  Second full reproduction of the entire attack returned identical
  verdicts and identical seed sets.
- UNSAT instances: exhaustive exact-search refutation with two
  independent implementations (DSATUR with forward-checking and an
  MRV DPLL), with the second implementation re-run by a different
  operator producing identical node counts.

## Method (why general-purpose solvers did not decide them)

We did not use a faster general SAT solver. We **reconstructed the
generating structure of each instance** and attacked that structure:

- **xorshift**: each instance is a clean combinational DAG with **32
  input variables = a 32-bit seed**, a classic Marsaglia **xorshift32
  (13,17,5)** linear stream, ARX whitening via 32-bit ripple-carry
  adders, and 32 observed output bits. An exhaustive 2^32 bitsliced sweep
  in C (64 seeds per uint64) found every preimage in ~830s total for all
  22 instances (~37s average). The sweep is exhaustive, so the seed lists
  below are COMPLETE (all preimages of each output).
- **coloring**: the instances use binary color encodings (2 and 3 bits
  per vertex), not one-hot. We decoded them into their underlying graphs
  (240 vertices, 9-regular, and 180 vertices, 15-regular, both with a
  precolored triangle) and refuted them by exhaustive exact search with
  two independent implementations (725/369 nodes by DSATUR; 453/391
  nodes by MRV DPLL).

General-purpose solvers timed out on these instances before our attacks:
CryptoMiniSat 5.17 returned INDETERMINATE on all 22 xorshift instances
at 600s (and at 3600s on the 5 smallest), and Cadical195 did not produce
a DRAT refutation for the coloring instances within 30 minutes.

## SAT instances and complete preimage lists

| Instance | GBD hash | Verdict | Preimages (32-bit seeds) |
|---|---|---|---|
| xorshift_r14_133 | `038abe9dd89044ee316d98dcb1c246c8` | SAT | 2165109229 |
| xorshift_r14_154 | `07597d4d25d2c3398af942046297c6b5` | SAT | 240247875, 2466046806, 3383783590 |
| xorshift_r14_158 | `078c5c775b3c2f217491da579d251262` | SAT | 208881714, 2914620559, 4016514323 |
| xorshift_r14_165 | `045f02ca093d50a6b5cbb0947024ebc6` | SAT | 1070413753, 2436577367, 4022569926 |
| xorshift_r14_176 | `02ff94614432f5b73b0343bcefe4933c` | SAT | 42347963 |
| xorshift_r15_105 | `063858bc0ecbb7e9bb59508deaa4568d` | SAT | 2559683248 |
| xorshift_r15_119 | `008c2670b0a19954d745ab938c40886c` | SAT | 750412887, 4239418319 |
| xorshift_r15_129 | `05b17ff3b26cd80d62639363464613a7` | SAT | 1049860713, 3504039205 |
| xorshift_r15_177 | `04ae66971e2b05230bf17f67f4c09d84` | SAT | 91196424 |
| xorshift_r15_37 | `016acfbf82d9d568e3c150bafc97b7bd` | SAT | 2258576795, 2310665936, 3791626360 |
| xorshift_r15_40 | `032a2aa949a2a42dca456a1a6478416d` | SAT | 3140303402, 3893670674 |
| xorshift_r15_41 | `078371daba8fb98cde69c38eb250cb8b` | SAT | 924868836, 1149946705, 2541498811 |
| xorshift_r15_47 | `05c0c9917caadf29b76fe9d176b6ca22` | SAT | 691770733, 1882277587 |
| xorshift_r16_110 | `00814867cf07384544639767652767d1` | SAT | 896596199, 1005616819 |
| xorshift_r16_136 | `021c276a57e52b34a856b22b137bf4e1` | SAT | 1841590741, 4142332179 |
| xorshift_r16_16 | `063ac4c42a259ae5b5dd3e94f41a7053` | SAT | 1234371770, 1333575779 |
| xorshift_r16_171 | `06dfed9efdde6eb19711ee62ebcf6972` | SAT | 1961083788, 2057308978, 3911442053 |
| xorshift_r16_181 | `06a594b8c0cb7eed9e6d476b2d31180b` | SAT | 3387454251 |
| xorshift_r16_188 | `01504faff9a94f9884f960b79665c70e` | SAT | 423732903, 1403025851, 1881074016 |
| xorshift_r16_21 | `025b0e5f9c13d80502929ba23cafc4af` | SAT | 808282664, 1241626961, 3975363987, 4167587133 |
| xorshift_r16_87 | `0013ea7f979ef32c464a6d59a3331748` | SAT | 1153780761, 3439866697, 3626490302, 4124735812 |
| xorshift_r16_98 | `065cddac7994dedb5bda9ca4d39aee2f` | SAT | 2175304606 |

## UNSAT instances (binary-encoded graph coloring)

| Instance | GBD hash | Graph | Verdict |
|---|---|---|---|
| `4col240_9_9.shuffled.cnf` | `0365db8065a89550e1ba73d86ec48cc2` | 240 vertices, 9-regular, 2-bit color encoding | **UNSAT** (not 4-colorable) |
| `5col180_15_3.shuffled.cnf` | `04b21b20b0f2aca4b886eb7832b6b0e8` | 180 vertices, 15-regular, 3-bit color encoding | **UNSAT** (not 5-colorable) |

Proof: exhaustive exact search with two independent implementations.
DSATUR with forward-checking exhausted the search tree at 725 and 369
nodes respectively; an independent MRV DPLL exhausted at 453 and 391
nodes. The second implementation was re-run by a different operator with
identical counts (0.03s). Both graphs have a precolored triangle (6/9
unit clauses). Z3 returns `unknown` at 120s on both. No small DRAT
certificate was produced within 30 minutes by Cadical195; the exhaustive
combinatorial refutation with independent re-confirmation is the
evidence.

## Reproduction

All instances, generators, attack scripts, raw logs and verification
scripts are public in the repository (commits `2efd570`, `6a416d0`,
`8040037`):

```bash
git clone https://github.com/iafiscal1212/torc-evidence.git
cd TORC-SOLVER

# Full structural report (xorshift):
cat experiments/results/xorshift_recon.md

# Re-verify all 49 preimages independently (Glucose4 + validate_model):
python experiments/xorshift_independent_verify.py

# Coloring structural reconstruction and proof chain:
cat experiments/results/gbd_witness_report.md
```

We are happy to provide the witness models in DIMACS `.model` format or
any other form that is useful to the database.
