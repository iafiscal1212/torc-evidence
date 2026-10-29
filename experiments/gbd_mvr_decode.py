"""Decodifica y verifica la estructura de MVRoundRobin_n14_d10_v4.cnf y
comprueba, con recuentos exactos sobre el CNF, las premisas de la prueba
UNSAT por conteo (pigeonhole) documentada en
experiments/results/MVR_DESIGN_PROOF.md.

Estructura verificada (n14 = 14 equipos, d10 = 10 dias, v4 = 4 huecos/dia):
  A. El CNF contiene EXACTAMENTE 91 clausulas positivas de longitud 40 +
     349.440 binarias, todas negativas. Nada mas (total 349.531).
     Las 91 positivas son disjuntas y cubren las vars 41..7280:
     var x_{m,s} = "el partido m usa el hueco s", con m = 0..90 (los
     C(14,2) = 91 emparejamientos) y s = 0..39 (10 dias x 4 huecos; el dia
     de s es s//4 por bloques de indices consecutivos).
  B. Intra-grupo (10.920 = 91 x 60 x 2, duplicadas): pares de huecos del
     mismo dia dentro de un partido -> un partido usa a lo sumo un hueco
     por dia (no se usa en la prueba).
  C. Mismo hueco (163.800 = 40 x C(91,2)): todo par de partidos prohibe
     usar el mismo hueco -> a lo sumo un partido por hueco (tampoco se
     usa en la prueba).
  D. Equipo-dia (1092 pares de partidos x 120 binarias extra + 40 de mismo
     hueco duplicadas): los pares de partidos que comparten equipo
     prohiben TODAS las 16 combinaciones de huecos dentro de cada dia ->
     dos partidos del mismo equipo nunca juegan el mismo dia.
  E. El grafo "comparten equipo" sobre los 91 partidos es L(K14): 14
     cliques maximales K13 (equipos), cada partido en exactamente 2, cada
     par de equipos se corta en exactamente 1 partido.

Conteo: por P1 cada partido usa >=1 hueco; fijando un hueco usado por
partido, P4 implica que los 13 partidos de un equipo caen en dias
distintos -> harian falta >=13 dias, pero solo hay 10. Contradiccion:
el CNF es UNSAT.

Uso: python experiments/gbd_mvr_decode.py
Sale con codigo 1 si alguna comprobacion falla.
"""

import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CNF = (ROOT / "benchmarks" / "external" / "gbd_unknown" / "scheduling"
       / "MVRoundRobin_n14_d10_v4.cnf")

failures = []


def check(cond, msg):
    print(f"  [{'OK' if cond else 'FALLO'}] {msg}")
    if not cond:
        failures.append(msg)


def main():
    longs, bins, other = [], [], 0
    n_vars = 0
    with open(CNF, "rb") as f:
        for raw in f:
            if raw[:1] == b"p":
                n_vars = int(raw.split()[2])
                continue
            if raw[:1] in (b"c", b"%"):
                continue
            cl = [int(t) for t in raw.split() if t != b"0"]
            if len(cl) == 40 and all(l > 0 for l in cl):
                longs.append(sorted(cl))
            elif len(cl) == 2 and all(l < 0 for l in cl):
                bins.append((-cl[0], -cl[1]))
            else:
                other += 1

    print("A. Inventario del CNF")
    check(n_vars == 7280, f"header n_vars = {n_vars} (esperados 7280)")
    check(len(longs) == 91, "91 clausulas positivas de longitud 40")
    check(len(bins) == 349_440, "349.440 binarias negativas")
    check(other == 0, f"ninguna otra clausula (halladas {other})")
    check(len(longs) + len(bins) + other == 349_531, "total = 349.531")
    check(len({tuple(g) for g in longs}) == 91, "grupos sin duplicados")
    allg = sorted({v for g in longs for v in g})
    check(len(allg) == 3640 and allg[0] == 41 and allg[-1] == 7280,
          "grupos disjuntos cubriendo vars 41..7280")
    gid = {v: i for i, g in enumerate(longs) for v in g}
    pos = {v: k for i, g in enumerate(longs) for k, v in enumerate(g)}

    intra = [(a, b) for a, b in bins if gid[a] == gid[b]]
    inter = [(a, b) for a, b in bins if gid[a] != gid[b]]
    print("B. Binarias intra-grupo (a lo sumo un hueco por dia y partido)")
    check(len(intra) == 10_920, f"intra = {len(intra)} (10.920)")
    ikeys = Counter((min(pos[a], pos[b]), max(pos[a], pos[b]))
                    for a, b in intra)
    check(len(ikeys) == 60 and set(ikeys.values()) == {182},
          "60 pares de huecos distintos por grupo, cada uno duplicado "
          "(182 = 91 grupos x 2)")
    check(all(pa // 4 == pb // 4 and pa != pb for pa, pb in ikeys),
          "los 60 pares son exactamente los C(4,2)x10 pares de huecos "
          "del mismo dia")

    print("C/D. Binarias inter-grupo")
    pair_rels: dict = defaultdict(list)
    for a, b in inter:
        ga, gb = gid[a], gid[b]
        pa, pb = pos[a], pos[b]
        if ga > gb:
            ga, gb, pa, pb = gb, ga, pb, pa
        pair_rels[(ga, gb)].append((pa, pb))
    check(len(pair_rels) == 4095, "los 4095 = C(91,2) pares de partidos "
                                  "estan relacionados")
    ss = Counter(sum(1 for r in rels if r[0] == r[1])
                 for rels in pair_rels.values())
    check(ss == Counter({40: 3003, 80: 1092}),
          f"mismo hueco: 40 por par (3003 pares) y 80 duplicadas en los "
          f"1092 pares de mismo equipo (hallado {dict(ss)})")
    check(sum(k * v for k, v in ss.items()) == 207_480,
          "total mismo hueco = 207.480 (3003x40 + 1092x80)")
    extra = {p: [r for r in rels if r[0] != r[1]]
             for p, rels in pair_rels.items()}
    ex = Counter(len(v) for v in extra.values())
    check(ex == Counter({0: 3003, 120: 1092}),
          f"extras: 120 por par de mismo equipo, 0 en el resto "
          f"(hallado {dict(ex)})")
    ok_extra = all(pa // 4 == pb // 4
                   for rels in extra.values() for pa, pb in rels)
    check(ok_extra, "toda binaria extra es intra-dia")
    # cobertura completa equipo-dia: 16 combinaciones por dia
    full = True
    for p, rels in pair_rels.items():
        if not extra[p]:
            continue
        s = {(pa, pb) for pa, pb in rels}
        for d in range(10):
            block = range(4 * d, 4 * d + 4)
            if any((pa, pb) not in s for pa in block for pb in block):
                full = False
    check(full, "P4: cada par de partidos del mismo equipo prohibe las 16 "
                "combinaciones de huecos de cada dia (x10 dias)")

    print("E. Estructura de equipos (grafo 'comparten equipo')")
    adj: dict = defaultdict(set)
    for (ga, gb), rels in extra.items():
        if rels:
            adj[ga].add(gb)
            adj[gb].add(ga)
    check(len(adj) == 91 and all(len(adj[g]) == 24 for g in adj),
          "91 partidos, cada uno comparte equipo con 24 (L(K14))")
    maximal = []

    def bk(R, P, X):
        if not P and not X:
            maximal.append(R)
            return
        if len(R) + len(P) < 13:
            return
        u = max(P | X, key=lambda v: len(adj[v]))
        for v in list(P - adj[u]):
            bk(R | {v}, P & adj[v], X & adj[v])
            P.discard(v)
            X.add(v)

    bk(set(), set(adj), set())
    teams = [c for c in maximal if len(c) == 13]
    check(len(teams) == 14, f"14 cliques maximales K13 (halladas "
                            f"{len(teams)}; maximales de cualquier talla: "
                            f"{Counter(len(c) for c in maximal)})")
    memb = Counter(v for c in teams for v in c)
    check(len(memb) == 91 and set(memb.values()) == {2},
          "cada partido pertenece a exactamente 2 equipos")
    inter1 = all(len(a & b) == 1 for a, b in combinations(teams, 2))
    check(inter1, "cada par de equipos comparte exactamente 1 partido "
                  "(los 91 partidos = los C(14,2) emparejamientos)")

    print("F. Pigeonhole")
    check(True, "P1: cada partido usa >=1 hueco (91 clausulas positivas)")
    check(True, "P2: 40 huecos = 10 dias x 4, dia(s) = indice//4")
    check(full, "P4: mismo equipo => dias distintos (verificado arriba)")
    print("  Argumento 1 (inyeccion): 91 partidos se inyectan en 40 "
          "huecos (P1 + mismo-hueco, C2). 91 > 40: contradiccion.")
    print("  Argumento 2 (equipo-dias): los 13 partidos de un equipo "
          "necesitan 13 dias distintos (P1 + equipo-dia). 13 > 10: "
          "contradiccion.")
    print("  => el CNF es INSATISFACTIBLE por conteo.")

    print()
    if failures:
        print(f"FALLOS: {len(failures)}")
        sys.exit(1)
    print("TODAS LAS COMPROBACIONES SUPERADAS: estructura verificada y "
          "premisas del conteo confirmadas sobre el CNF")


if __name__ == "__main__":
    main()
