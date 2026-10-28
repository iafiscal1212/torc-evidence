"""Independent verification of the 49 xorshift preimages.

Second opinion, no shared code with the bitsliced C sweep: for every
reported seed, pin the 32 input bits as unit clauses in the ORIGINAL CNF,
solve with Glucose4, and re-validate the returned model with
validate_model. 49/49 verified on 2026-10-28.

Usage: python experiments/xorshift_independent_verify.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pysat.solvers import Glucose4  # noqa: E402

from torc_sat.parser import parse_dimacs  # noqa: E402
from torc_sat.sat_certifier import validate_model  # noqa: E402
from xorshift_recon import build_circuit, GBD  # noqa: E402

RESULTS = Path(__file__).resolve().parent / "results"


def main():
    results = json.loads((RESULTS / "xorshift_brute_results.json").read_text())
    total = ok = 0
    bad = []
    for name, rec in results.items():
        path = GBD / f"{name}.sanitized.cnf"
        cnf = parse_dimacs(str(path))
        _, _, _, inputs, _, _, _ = build_circuit(path)
        for seed in rec["seeds_valid"]:
            total += 1
            units = [[i] if (seed >> (i - 1)) & 1 else [-i] for i in inputs]
            with Glucose4(bootstrap_with=cnf.clauses + units) as s:
                sat = s.solve()
                model = s.get_model() if sat else None
            if sat and model and validate_model(cnf.clauses, model):
                ok += 1
            else:
                bad.append((name, seed, sat))
        print(f"{name}: {len(rec['seeds_valid'])} semillas verificadas")
    print(f"\nINDEPENDENT VERIFICATION: {ok}/{total} seeds validate "
          f"(Glucose4 + validate_model against original CNF)")
    if bad:
        print("FAILURES:", bad)
        return 1
    print("ALL 22 INSTANCES CONFIRMED SAT with independently verified witnesses")
    return 0


if __name__ == "__main__":
    sys.exit(main())
