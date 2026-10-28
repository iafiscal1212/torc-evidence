"""Valida las semillas encontradas por el barrido C contra el CNF original.

Para cada experiments/results/xorshift_brute_<name>.log con líneas
"SEED <n>": evalúa el DAG reconstruido, construye la asignación de
TODAS las variables del CNF y la pasa por `validate_model` contra las
cláusulas ORIGINALES. Solo las semillas que validan se reportan como
SAT. Instancias sin semillas en el barrido completo: UNSAT por
agotamiento exhaustivo del espacio de 2^32 semillas (sin certificado
independiente — se reporta como tal, con la limitación explícita).

Uso: python experiments/xorshift_validate_seeds.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from torc_sat.sat_certifier import validate_model
from xorshift_recon import build_circuit, GBD

RESULTS = Path(__file__).resolve().parent / "results"
OUT = RESULTS / "xorshift_brute_results.json"


def main():
    report = {}
    for log in sorted(RESULTS.glob("xorshift_brute_xorshift_r*.log")):
        name = log.name.replace("xorshift_brute_", "").replace(".log", "")
        lines = log.read_text().splitlines()
        if "DONE" not in lines:
            print(f"{name}: barrido incompleto (sin DONE) — omitida")
            continue
        seeds = [int(line.split()[1]) for line in lines
                 if line.startswith("SEED ")]
        cnf, defs, units, inputs, n_and, n_or, leftover = \
            build_circuit(GBD / f"{name}.sanitized.cnf")
        rec = {"n_vars": cnf.n_vars, "n_clauses": len(cnf.clauses),
               "n_seeds_found": len(seeds), "seeds_valid": [],
               "seeds_invalid": []}
        for seed in seeds:
            vals = {i: (seed >> (i - 1)) & 1 for i in inputs}
            for v in range(33, cnf.n_vars + 1):
                op, (a, b) = defs[v]
                vals[v] = (vals[a] ^ vals[b]) if op == "xor" else \
                    (vals[a] & vals[b] if op == "and"
                     else vals[a] | vals[b])
            model = [v if vals[v] else -v
                     for v in range(1, cnf.n_vars + 1)]
            (rec["seeds_valid"] if validate_model(cnf.clauses, model)
             else rec["seeds_invalid"]).append(seed)
        if rec["seeds_valid"]:
            rec["verdict"] = "SAT"
        elif not seeds:
            rec["verdict"] = "UNSAT (agotamiento exhaustivo 2^32, " \
                             "sin certificado independiente)"
        else:
            rec["verdict"] = "ERROR: semillas encontradas pero ninguna " \
                             "valida (bug en el barrido)"
        report[name] = rec
        print(f"{name}: {rec['verdict']} | válidas: "
              f"{rec['seeds_valid'][:4]}{'...' if len(rec['seeds_valid']) > 4 else ''}")
    OUT.write_text(json.dumps(report, indent=2))
    print(f"JSON: {OUT}")


if __name__ == "__main__":
    main()
