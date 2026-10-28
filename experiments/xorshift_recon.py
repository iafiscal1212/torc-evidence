"""Reconstrucción estructural del generador xorshift desde su CNF.

Analiza las 22 instancias `benchmarks/external/gbd_unknown/xorshift_r*`
y reconstruye el grafo del circuito:

1. Extracción estricta de ecuaciones XOR3 (torc_sat.xor_engine) —
   cada ecuación y = a ⊕ b define la variable mayor (compuerta XOR
   Tseitin; verificado: sin duplicados, toda var no de entrada tiene
   exactamente una definición).
2. El residual se clasifica en puertas AND (¬a∨¬b∨y, a∨¬y, b∨¬y) y OR
   (a∨b∨¬y, ¬a∨y, ¬b∨y) emparejando la cláusula de tamaño 3 con sus
   dos de tamaño 2. En r14_133: 504 AND + 504 OR, cero sobrantes.
3. Bloques AND/OR contiguos = sumadores ripple-carry de 32 bits
   (63 AND + 63 OR por sumador: 32 generate g_i=a_i∧b_i, 31 t_i=c_i∧h_i,
   32 h_i=a_i∨b_i, 31 carries c_{i+1}=g_i∨t_i; p_i=a_i⊕b_i y
   sum_i=p_i⊕c_i en la capa XOR adyacente).
4. Capas XOR entre sumadores = mezcla lineal (xorshift shifts).
5. Entradas = vars sin definición (el estado inicial); unidades =
   bits de salida observados.

Salida: informe por instancia en stdout + JSON de estructura en
experiments/results/xorshift_recon.json.

Uso: python experiments/xorshift_recon.py [instancia...]
"""

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from torc_sat.parser import parse_dimacs
from torc_sat.xor_extract import _extract_xors

ROOT = Path(__file__).resolve().parent.parent
GBD = ROOT / "benchmarks" / "external" / "gbd_unknown"
OUT = (Path(__file__).resolve().parent / "results" / "xorshift_recon.json")


def build_circuit(path):
    """Reconstruye el DAG: defs[y] = (op, (a, b)) + units {var: bit}.

    Devuelve (cnf, defs, units, n_and, n_or). Falla (AssertionError)
    si alguna puerta no clasifica o alguna var definida dos veces —
    la reconstrucción solo es válida si el DAG es completo.
    """
    cnf = parse_dimacs(str(path))
    eqs, residual, _ = _extract_xors(cnf.clauses)
    c2 = set(tuple(sorted(c)) for c in residual if len(c) == 2)
    defs = {}
    for vs, ch in eqs:
        y = max(vs)
        assert y not in defs
        assert ch == 0  # y = a ⊕ b (carga 1 no observada; fail-closed)
        defs[y] = ("xor", tuple(sorted(v for v in vs if v != y)))
    n_and = n_or = 0
    used2 = set()
    for c in residual:
        if len(c) != 3:
            continue
        pos = [lit for lit in c if lit > 0]
        neg = [-lit for lit in c if lit < 0]
        if len(pos) == 1 and len(neg) == 2:
            y, a, b = pos[0], neg[0], neg[1]
            if (tuple(sorted((a, -y))) in c2
                    and tuple(sorted((b, -y))) in c2):
                assert y not in defs
                defs[y] = ("and", (a, b))
                used2.add(tuple(sorted((a, -y))))
                used2.add(tuple(sorted((b, -y))))
                n_and += 1
                continue
        if len(neg) == 1 and len(pos) == 2:
            y, a, b = neg[0], pos[0], pos[1]
            if (tuple(sorted((-a, y))) in c2
                    and tuple(sorted((-b, y))) in c2):
                assert y not in defs
                defs[y] = ("or", (a, b))
                used2.add(tuple(sorted((-a, y))))
                used2.add(tuple(sorted((-b, y))))
                n_or += 1
                continue
        raise AssertionError(f"cláusula residual no clasificada: {c}")
    units = {}
    n_units = 0
    for c in residual:
        if len(c) == 1:
            units[abs(c[0])] = 1 if c[0] > 0 else 0
            n_units += 1
    # toda var es entrada o está definida exactamente una vez
    inputs = [v for v in range(1, cnf.n_vars + 1) if v not in defs]
    return cnf, defs, units, inputs, n_and, n_or, len(c2) - len(used2)


def adder_blocks(defs):
    """Bloques contiguos (gap <= 3) de puertas AND/OR = sumadores."""
    av = sorted(v for v, d in defs.items() if d[0] in ("and", "or"))
    blocks, cur = [], []
    for v in av:
        if cur and v - cur[-1] <= 3:
            cur.append(v)
        else:
            if cur:
                blocks.append(cur)
            cur = [v]
    if cur:
        blocks.append(cur)
    return blocks


def shift_signature(defs, n_vars):
    """Constantes de desplazamiento: histograma de offsets en XORs
    entre la primera capa (vars <= primer sumador) — heurística."""
    offs = Counter()
    for y in sorted(defs):
        d = defs[y]
        if d[0] == "xor":
            a, b = d[1]
            offs[b - a] += 1
    return offs


def analyze(name):
    path = GBD / f"{name}.sanitized.cnf"
    cnf, defs, units, inputs, n_and, n_or, leftover_c2 = build_circuit(path)
    blocks = adder_blocks(defs)
    outs = sorted(units)
    rec = {
        "n_vars": cnf.n_vars,
        "n_clauses": len(cnf.clauses),
        "n_inputs": len(inputs),
        "inputs_range": [inputs[0], inputs[-1]] if inputs else None,
        "n_xor_gates": sum(1 for d in defs.values() if d[0] == "xor"),
        "n_and": n_and, "n_or": n_or,
        "leftover_c2": leftover_c2,
        "n_units": len(units),
        "outputs_range": [outs[0], outs[-1]] if outs else None,
        "outputs_consecutive": outs == list(range(outs[0], outs[-1] + 1)),
        "n_adders": len(blocks),
        "adder_sizes": [sum(1 for v in b if defs[v][0] == "and")
                        for b in blocks],
        "shift_offsets_top": shift_signature(defs, cnf.n_vars).most_common(8),
    }
    return rec


def main():
    names = sys.argv[1:] or sorted(
        p.name.replace(".sanitized.cnf", "")
        for p in GBD.glob("xorshift_r*.sanitized.cnf"))
    report = {}
    for name in names:
        try:
            rec = analyze(name)
        except AssertionError as e:
            rec = {"error": f"reconstrucción incompleta: {e}"}
        report[name] = rec
        print(f"{name}: {json.dumps(rec)}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2))
    print(f"\nJSON: {OUT}")


if __name__ == "__main__":
    main()
