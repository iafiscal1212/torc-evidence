"""Testigos para las instancias de k-coloring binario de gbd_unknown/coloring.

Codificación reconstruida (verificado empíricamente sobre ambas instancias):

- Cada vértice tiene b bits (b=2 en 4col240, b=3 en 5col180). La relación
  "mismo color" entre dos vértices adyacentes es una biyección privada por
  arista (matching entre patrones de bits), visible en las cláusulas de
  arista: cada una prohíbe UN par (patrón_u, patrón_v) con bit=1 sii el
  literal es negativo (la cláusula es ∨ "este bit difiere del código").
  4col: 1080 varsets de 4 vars (1079 con 4 cláusulas, 1 con 3 + una
  residual len-3 encogida por preprocessing). Grafo 9-regular, 240 vértices.
  5col: 1350 varsets de 6 vars (1349 con 5 cláusulas, 1 con 4); además
  180×3 cláusulas len-3 = códigos inválidos (8-5=3 por vértice).
  Grafo 15-regular, 180 vértices.
- El naming global de colores (union-find sobre pares prohibidos = misma
  clase de color) es consistente en ambas: 4 y 5 clases. Las unidades
  precolorean un triángulo con 3 colores distintos (ruptura de simetría).
- 4col tiene además 1 cláusula len-3 residual que el naming no captura:
  el chequeo final es SIEMPRE a nivel de cláusula original.

Recuperación de vértices:
- b=3: varsets de las cláusulas len-3 (180 grupos disjuntos, cubren 540).
- b=2: compañero de a = var que más co-aparece con a en varsets len-4
  (cada arista de u repite el mismo par de bits de u; verificado: 240
  pares disjuntos, todo varset de arista = exactamente 2 vértices, y los
  patrones por vértice son distintos en las 4 cláusulas de cada arista).

Solvers (ambos sobre el k-coloring propio ya decodificado):
1. min-conflicts a nivel de color (rápido, restarts con ruido).
2. DSATUR con forward-checking (exacto, con tope de nodos) como respaldo.
El testigo se reconstruye a patrones de bits vía el naming y se valida con
validate_model contra el CNF ORIGINAL (incluye la residual len-3).

Uso: python experiments/gbd_coloring_witness.py
"""

import json
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from torc_sat.parser import parse_dimacs
from torc_sat.sat_certifier import validate_model

ROOT = Path(__file__).resolve().parent.parent
GBD = ROOT / "benchmarks" / "external" / "gbd_unknown" / "coloring"
OUT = Path(__file__).resolve().parent / "results" / "gbd_witness_results.json"

TIME_LIMIT = 120.0  # por instancia


def recover_vertices_2bit(clauses):
    """Vértices = pares de vars con máxima co-aparición en varsets len>=4."""
    cooc = Counter()
    groups = defaultdict(list)
    for c in clauses:
        if len(c) >= 4:
            vs = tuple(sorted(abs(l) for l in c))
            groups[vs].append(c)
    for vs in groups:
        if len(vs) != 4:
            continue
        for i in range(4):
            for j in range(i + 1, 4):
                cooc[(vs[i], vs[j])] += 1
    by_var = defaultdict(Counter)
    for (a, b), n in cooc.items():
        by_var[a][b] = n
        by_var[b][a] = n
    partner = {}
    for a, cnt in by_var.items():
        if a in partner:
            continue
        b = cnt.most_common(1)[0][0]
        partner[a] = b
        partner[b] = a
    assert all(partner[partner[a]] == a for a in partner), \
        "emparejamiento no simétrico"
    pairs = sorted({tuple(sorted((a, b))) for a, b in partner.items()})
    return pairs, groups


def recover_vertices_3bit(clauses):
    """Vértices = varsets de cláusulas len-3; dominios = códigos válidos."""
    vgroups = defaultdict(list)
    rest = []
    for c in clauses:
        if len(c) == 3:
            vgroups[tuple(sorted(abs(l) for l in c))].append(c)
        else:
            rest.append(c)
    vertices = sorted(vgroups)
    invalid = {}
    for vs in vertices:
        invalid[vs] = {tuple(1 if -v in c else 0 for v in vs)
                       for c in vgroups[vs]}
    return vertices, invalid, rest


def forbidden_pair(clause, va, vb):
    s = set(clause)
    return (tuple(1 if -v in s else 0 for v in va),
            tuple(1 if -v in s else 0 for v in vb))


def name_colors(domains, edge_pairs):
    """Union-find de (vértice, patrón) vía pares prohibidos = mismo color."""
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for v, pats in domains.items():
        for p in pats:
            find((v, p))
    for (u, v), pairs in edge_pairs.items():
        for pu, pv in pairs:
            if pu in domains[u] and pv in domains[v]:
                ru, rv = find((u, pu)), find((v, pv))
                if ru != rv:
                    parent[ru] = rv
    color_of, classes = {}, {}
    for v, pats in domains.items():
        for p in pats:
            r = find((v, p))
            if r not in classes:
                classes[r] = len(classes)
            color_of[(v, p)] = classes[r]
    for v, pats in domains.items():
        if len({color_of[(v, p)] for p in pats}) != len(pats):
            return None, len(classes)
    return color_of, len(classes)


def min_conflicts_colors(adj, domains, precolored, deadline, seed,
                         max_steps=2_000_000, noise=0.2):
    """Min-conflicts a nivel de color con ruido; vértices precoloreados
    congelados. Devuelve dict v->color o None."""
    rng = random.Random(seed)
    n = len(adj)
    color = {}
    for v in range(n):
        color[v] = precolored[v] if v in precolored else \
            rng.choice(sorted(domains[v]))
    conf = [0] * n
    for v in range(n):
        conf[v] = sum(1 for w in adj[v] if color[w] == color[v])
    bad = {v for v in range(n)
           if conf[v] > 0 and v not in precolored}
    steps = 0
    while steps < max_steps and time.time() < deadline:
        if not bad:
            if all(conf[v] == 0 for v in range(n)):
                return color, steps
            return None, steps  # conflicto entre precoloreados
        steps += 1
        v = rng.choice(tuple(bad))
        dom = sorted(domains[v])
        if rng.random() < noise:
            c_new = rng.choice(dom)
        else:
            cnt = {c: 0 for c in dom}
            for w in adj[v]:
                if color[w] in cnt:
                    cnt[color[w]] += 1
            best = min(cnt[c] for c in dom if c != color[v]) \
                if len(dom) > 1 else cnt[color[v]]
            opts = [c for c in dom if cnt[c] == best]
            c_new = rng.choice(opts)
        c_old = color[v]
        if c_new == c_old:
            continue
        color[v] = c_new
        for w in adj[v]:
            if color[w] == c_old:
                conf[w] -= 1
                if conf[w] == 0:
                    bad.discard(w)
            if color[w] == c_new:
                conf[w] += 1
                if w not in precolored:
                    bad.add(w)
        conf[v] = sum(1 for w in adj[v] if color[w] == c_new)
        if conf[v] == 0:
            bad.discard(v)
    return (color if not bad else None), steps


def dsatur(n, adj, dom0, precolored, deadline, node_cap=2_000_000):
    """DSATUR con forward-checking; devuelve (colordict|None, nodos, agotado)."""
    color = dict(precolored)
    dom = {v: set(dom0[v]) for v in range(n)}
    deg = [len(adj[v]) for v in range(n)]
    nodes = [0]
    timed_out = [False]

    def bt():
        nodes[0] += 1
        if nodes[0] > node_cap or time.time() > deadline:
            timed_out[0] = True
            return False
        if len(color) == n:
            return True
        best, key = None, None
        for v in range(n):
            if v in color:
                continue
            sat = len({color[w] for w in adj[v] if w in color})
            k = (sat, deg[v], -len(dom[v]))
            if key is None or k > key:
                best, key = v, k
        v = best
        saved = {w: set(dom[w]) for w in adj[v] if w not in color}
        for c in sorted(dom[v]):
            color[v] = c
            for w in adj[v]:
                if w not in color:
                    dom[w].discard(c)
            if all(dom[w] for w in adj[v] if w not in color) and bt():
                return True
            for w, s in saved.items():
                dom[w] = s
            del color[v]
            if timed_out[0]:
                return False
        return False

    ok = bt()
    return (color if ok else None), nodes[0], not timed_out[0]


def mrv_unsat_check(adj, dom0, precolored, node_cap=500_000):
    """DPLL independiente (MRV + forward-checking) para confirmar UNSAT.
    Devuelve (unsat_probado, nodos)."""
    verts = sorted(dom0)
    color = dict(precolored)
    dom = {v: set(dom0[v]) for v in verts}
    nodes = [0]

    def bt():
        nodes[0] += 1
        if nodes[0] > node_cap:
            return None
        if len(color) == len(verts):
            return True
        un = [v for v in verts if v not in color]
        v = min(un, key=lambda x: (len(dom[x]), -len(adj[x])))
        saved = {w: set(dom[w]) for w in adj[v] if w not in color}
        for c in sorted(dom[v]):
            color[v] = c
            for w in adj[v]:
                if w not in color:
                    dom[w].discard(c)
            ok = all(dom[w] for w in adj[v] if w not in color)
            r = bt() if ok else False
            if r:
                return True
            for w, s in saved.items():
                dom[w] = s
            del color[v]
            if r is None:
                return None
        return False

    r = bt()
    return (r is False), nodes[0]


def cadical_check(clauses, megaconf):
    """Veredicto de Cadical sobre el CNF original con presupuesto de
    conflictos acotado. 'SAT'/'UNSAT'/'unknown'."""
    from pysat.solvers import Cadical195
    s = Cadical195(bootstrap_with=clauses)
    s.conf_budget(int(megaconf * 1_000_000))
    r = s.solve_limited()
    s.delete()
    return "SAT" if r is True else ("UNSAT" if r is False else "unknown")


def solve_instance(path, deadline_s=TIME_LIMIT, cadical_megaconf=2.0):
    t0 = time.time()
    cnf = parse_dimacs(str(path))
    clauses = [list(c) for c in cnf.clauses]
    units = [c[0] for c in clauses if len(c) == 1]
    rec = {"n_vars": cnf.n_vars, "n_clauses": len(clauses),
           "units": len(units)}

    n3 = sum(1 for c in clauses if len(c) == 3)
    if n3 >= 100:  # 5col: vértices desde len-3
        vertices, invalid, rest = recover_vertices_3bit(clauses)
        b = 3
        domains = {i: [p for p in
                       [(x, y, z) for x in (0, 1) for y in (0, 1)
                        for z in (0, 1)] if p not in invalid[vt]]
                   for i, vt in enumerate(vertices)}
        edge_groups = defaultdict(list)
        for c in rest:
            if len(c) >= 4:
                edge_groups[tuple(sorted(abs(l) for l in c))].append(c)
        rec["structure"] = f"5col-style: {len(vertices)} vértices 3 bits"
    else:  # 4col: vértices por co-aparición
        pairs, edge_groups = recover_vertices_2bit(clauses)
        vertices = pairs
        b = 2
        domains = {i: [(x, y) for x in (0, 1) for y in (0, 1)]
                   for i in range(len(vertices))}
        rec["structure"] = f"4col-style: {len(vertices)} vértices 2 bits"

    var2v = {}
    for i, vt in enumerate(vertices):
        for x in vt:
            var2v[x] = i
    assert len(var2v) == cnf.n_vars
    rec["n_vertices"] = len(vertices)

    edge_pairs, edges = {}, []
    for vs, cls in edge_groups.items():
        vset = sorted({var2v[x] for x in vs})
        if len(vset) != 2:
            continue
        u, v = vset
        prs = {forbidden_pair(c, vertices[u], vertices[v])
               for c in cls if len(c) == 2 * b}
        edge_pairs[(u, v)] = prs
        edges.append((u, v))
    rec["n_edges"] = len(edges)
    adj = defaultdict(set)
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)
    degs = [len(adj[v]) for v in range(len(vertices))]
    rec["degree"] = {"min": min(degs), "max": max(degs),
                     "mean": round(sum(degs) / len(degs), 2)}

    # restricción de dominio por unidades (precoloreo)
    for u in units:
        v = var2v[abs(u)]
        idx = vertices[v].index(abs(u))
        bit = 1 if u > 0 else 0
        domains[v] = [p for p in domains[v] if p[idx] == bit]
        assert domains[v], f"unidad {u} vacía dominio de vértice {v}"
    rec["precolored_vertices"] = \
        sum(1 for v in domains if len(domains[v]) == 1)

    color_of, k = name_colors(domains, edge_pairs)
    rec["k_colors_named"] = k
    rec["naming_consistent"] = color_of is not None

    sol_colors, method = None, None
    if color_of is not None:
        domc = {v: {color_of[(v, p)] for p in domains[v]}
                for v in range(len(vertices))}
        pre = {v: next(iter(dc)) for v, dc in domc.items() if len(dc) == 1}
        # 1) min-conflicts rápido con restarts
        dline = time.time() + deadline_s
        seed, total_steps = 0, 0
        while time.time() < dline:
            sol_colors, steps = min_conflicts_colors(
                adj, domc, pre, dline, seed)
            total_steps += steps
            if sol_colors is not None:
                method = f"min_conflicts(seed={seed}, steps={total_steps})"
                break
            seed += 1
        rec["mc_steps"] = total_steps
        # 2) DSATUR exacto como respaldo / detector de UNSAT
        if sol_colors is None:
            sol_colors, nodes, exhausted = dsatur(
                len(vertices), adj, domc, pre, time.time() + deadline_s)
            rec["dsatur_nodes"] = nodes
            rec["dsatur_exhausted"] = exhausted
            if sol_colors is not None:
                method = "dsatur"
            elif exhausted:
                # DSATUR agotó el árbol: el k-coloring decodificado es
                # UNSAT. Cross-check con MRV-DPLL independiente.
                ok2, nodes2 = mrv_unsat_check(adj, domc, pre)
                rec["mrv_dpll_unsat_nodes"] = nodes2
                rec["mrv_dpll_confirms_unsat"] = ok2
                if ok2:
                    # verificación sobre el CNF ORIGINAL con Cadical
                    # (presupuesto acotado; si no termina, se reporta)
                    cad = cadical_check(clauses, cadical_megaconf)
                    rec["cadical_original_cnf"] = cad
                    if cad == "UNSAT":
                        rec["verdict"] = (
                            "UNSAT (probado: agotamiento del k-coloring "
                            "decodificado por 2 solvers exactos + Cadical "
                            "sobre el CNF original)")
                        rec["wall_s"] = round(time.time() - t0, 2)
                        return rec
                    rec["verdict"] = (
                        "UNSAT a nivel de k-coloring (agotamiento por "
                        "DSATUR+MRV-DPLL; Cadical no confirma en el "
                        "presupuesto — ver gbd_cadical_results.json)")

    rec["wall_s"] = round(time.time() - t0, 2)
    if sol_colors is None:
        rec.setdefault("verdict", "SIN TESTIGO (no implica UNSAT)")
        return rec
    # colores -> patrones de bits -> asignación completa
    bits = {}
    for v in range(len(vertices)):
        pat = next(p for p in domains[v] if color_of[(v, p)] == sol_colors[v])
        for x, bb in zip(vertices[v], pat):
            bits[x] = bb
    full = [v if bits[v] else -v for v in range(1, cnf.n_vars + 1)]
    ok = validate_model(clauses, full)
    rec["method"] = method
    rec["witness_validated"] = bool(ok)
    rec["verdict"] = "SAT (testigo validado)" if ok else \
        "ERROR: asignación construida no valida contra el CNF"
    if ok:
        rec["model_file"] = f"gbd_witness_{path.stem}.model"
        (OUT.parent / rec["model_file"]).write_text(
            " ".join(map(str, full)) + "\n")
    return rec


def main():
    budget = float(sys.argv[1]) if len(sys.argv) > 1 else TIME_LIMIT
    cad_mc = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
    results = json.loads(OUT.read_text()) if OUT.exists() else {}
    for name in ["4col240_9_9.shuffled.cnf", "5col180_15_3.shuffled.cnf"]:
        print(f"== {name}", flush=True)
        rec = solve_instance(GBD / name, deadline_s=budget,
                             cadical_megaconf=cad_mc)
        results[name] = rec
        OUT.write_text(json.dumps(results, indent=2))
        print(f"   {rec['verdict']} | {rec.get('structure')} | "
              f"método: {rec.get('method')} | {rec['wall_s']}s", flush=True)
    print(f"JSON: {OUT}")


if __name__ == "__main__":
    main()
