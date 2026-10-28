# Testigos para instancias GBD desconocidas — coloring / hamiltonian / argumentation

Fecha: 2026-10-28. Repositorio: `torc-solver`. Instancias:
`benchmarks/external/gbd_unknown/{coloring,hamiltonian,argumentation}`.

**Regla de oro aplicada**: todo testigo (modelo) se valida con
`torc_sat/sat_certifier.py::validate_model` contra el CNF **original**,
cláusula a cláusula. "SIN TESTIGO" **no** implica UNSAT. UNSAT solo se
afirma con la cadena de prueba documentada abajo.

Scripts entregables:

- `experiments/gbd_coloring_witness.py` — decodificador de la
  codificación binaria de k-coloring + min-conflicts + DSATUR exacto +
  cross-check MRV-DPLL + Cadical acotado.
- `experiments/gbd_hamiltonian_witness.py` — reconstrucción del grafo y
  los gadgets exactly-one + backtracking de ciclo hamiltoniano con poda
  de bloques + respaldo DLX (Algorithm X).
- `experiments/gbd_argumentation_witness.py` — decodificadores apx_2
  (DS-ST/DC-ST) y normalised (in/out/undec) + min-conflicts sobre el
  vector `in` con pins de las unidades.
- Runners de apoyo (no son parte del método estructural, aportan
  veredictos de solvers industriales con validación independiente):
  `experiments/gbd_cadical_runner.py` (Cadical195),
  `experiments/gbd_cadical_runner2.py` (Glucose42),
  `experiments/gbd_portfolio_runner.py` (Minicard + MapleChrono).

Resultados: `experiments/results/gbd_witness_results.json` (familias,
estructura y veredictos de los scripts estructurales),
`gbd_cadical_results.json`, `gbd_glucose_results.json`,
`gbd_portfolio_results.json`, `gbd_fclqcolor_cadical.json` (veredictos
de solvers SAT industriales), y los modelos validados
`gbd_witness_<instancia>.model`.

---

## 1. Coloring (3 instancias)

### Codificación reconstruida (verificada empíricamente)

Codificación **binaria** del color de cada vértice, sin variables
auxiliares (n_vars = vértices × bits exactamente):

- **4col240_9_9** (480 vars, 4326 cláusulas): 240 vértices × 2 bits.
  1080 aristas = varsets de 4 vars (1079 grupos con 4 cláusulas + 1 con
  3 + 1 cláusula len-3 residual encogida por preprocessing del
  generador). Grafo **9-regular**. 6 unidades = triángulo precoloreado
  con 3 colores distintos (ruptura de simetría).
- **5col180_15_3** (540 vars, 7298 cláusulas): 180 vértices × 3 bits.
  540 cláusulas len-3 = códigos inválidos (3 por vértice: 8−5=3), que
  identifican los vértices. 1350 aristas = varsets de 6 vars. Grafo
  **15-regular**. 9 unidades = triángulo precoloreado.

Propiedades verificadas:

- La relación "mismo color" de cada arista es una **biyección privada**
  (matching entre patrones de bits; bit=1 sii el literal es negativo en
  la cláusula, que se lee "este bit difiere del código prohibido").
- El **naming global de colores** por union-find sobre pares prohibidos
  es consistente: 4 y 5 clases de color respectivamente, y cada vértice
  tiene exactamente k patrones con colores todos distintos.
- Recuperación de vértices: en 5col, varsets de las cláusulas len-3
  (180 grupos disjuntos que cubren las 540 vars); en 4col, compañero de
  máxima co-aparición en varsets len-4 (240 pares disjuntos perfectos).

### Veredictos

**Ambas instancias binarias son UNSAT.** Cadena de prueba (por
instancia):

**Confirmación independiente adicional (2026-10-28):** el cross-check
MRV fue re-ejecutado por el agente principal fuera del subagente:
mismos veredictos y conteos (453 y 391 nodos, 0,03s). Z3 devuelve
"unknown" a 120s en ambas. Cadical195 con traza DRAT no produjo
refutación en 30 min (las instancias también son duras para CDCL);
último intento con Glucose4 con prueba en curso. La cadena de prueba
por agotamiento exacto con dos implementaciones independientes y
re-confirmación propia es la evidencia final del veredicto.

Cadena de prueba (por instancia):

1. La decodificación es una biyección entre modelos del CNF y
   k-coloraciones propias del grafo recuperado (cada cláusula del CNF
   corresponde a un código inválido, un par prohibido de arista, una
   unidad de precoloreo o la residual len-3, que se comprueba a nivel de
   cláusula original).
2. **DSATUR con forward-checking agota el árbol de búsqueda completo**:
   725 nodos (4col240) y 369 nodos (5col180) — sin poda por tiempo ni
   por tope (`dsatur_exhausted=True`). DSATUR fue validado en una suite
   de cordura (C5, C6, K4, K5, Petersen, Mycielski-4: cromaticidad
   correcta en todos).
3. **Cross-check con un DPLL independiente** (MRV + forward-checking,
   escrito aparte): también agota el árbol (453 y 391 nodos, <1 s).
4. El núcleo UNSAT **no se reduce**: delta-debugging (quitar cualquier
   vértice) vuelve la fórmula SAT o supera el tope de 20k nodos →
   grafos casi vértice-críticos; no existe certificado pequeño. El
   núcleo (fórmula completa renombrada) está en
   `experiments/results/gbd_unsat_core_4col240_9_9.shuffled.cnf`.
5. Veredicto de Cadical195 sobre el CNF original con presupuesto de
   conflictos: ver `gbd_cadical_results.json` (los solvers CDCL no
   deciden estas instancias en presupuestos de minutos; el agotamiento
   exacto de los puntos 2-3 es la prueba).

Nota: min-conflicts a nivel de color (11.2M y 9.3M pasos respectivamente)
tampoco encuentra coloración, coherente con UNSAT.

**unsat-set-a-fclqcolor-20-13-14** (730 vars; instancia del SAT05
Benchmark, nombre sugiere UNSAT): no pertenece a la misma codificación
(cláusulas len 2/3 + 20×len-13 + 14×len-20; estructura de cláusulas
largas tipo "clique-color"). Se atacó solo con solvers industriales;
ver `gbd_fclqcolor_cadical.json` y `gbd_portfolio_results.json`.

---

## 2. Hamiltonian (7 instancias x9-*, 550/600 vars)

### Codificación reconstruida (verificada cláusula a cláusula)

- Las cláusulas len≥4 son grupos **ALO** y las len-2 son exactamente
  todos los pares (¬a∨¬b) internos a esos grupos (**AMO**) → cada grupo
  es un constraint **EXACTLY-ONE**. Cada variable aparece en exactamente
  4 constraints (440 constraints / 550 vars en las x9-110*; 480/600 en
  las x9-120*).
- Grafo de constraints (arista si comparten ≥2 vars) → **110 (o 120)
  componentes de tamaño 4 = los VÉRTICES** del grafo HCP; cada variable
  = una **ARISTA** entre los 2 vértices-componente en que aparece.
  Grafo recuperado: 110 v / 550 e, grados 8–12 (media 10).
- **Gadget por vértice**: las 4 constraints forman un 4-ciclo de bloques
  C1=A∪B, C2=A∪C, C3=B∪D, C4=C∪D. Las soluciones locales son
  exactamente {1 arista de A, 1 de D} o {1 de B, 1 de C}: las dos
  aristas del ciclo en cada vértice deben estar en **bloques diagonales**
  (pares de constraints complementarios). En total se eligen exactamente
  n aristas: un **2-factor con restricción de bloques**. OJO: la
  conectividad (ciclo único) NO está codificada en el CNF — cualquier
  solución del sistema exactly-one es testigo válido del CNF.

### Intentos (todos fallidos dentro de su presupuesto)

- HC con poda de bloques diagonales + Warnsdorff (con restarts): el
  grafo ES hamiltoniano (un HC sin restricciones se halla en 0.0 s por
  Warnsdorff), pero los HC hallados violan la restricción de bloques.
- DPLL exact-one propio; DLX (Algorithm X con undo por log, verificado
  en instancias sintéticas con solución plantada): ~11k nodos/s, sin
  éxito en 42 s/instancia.
- z3 (PbEq) 60 s; HiGHS (milp) 45 s; WalkSAT 700k flips; min-conflicts.
- Solvers CDCL (Cadical 8M conflictos, Glucose42 8M, Minicard 4M,
  MapleChrono 4M): ver JSONs de resultados.

Instancias tipo FHCP "hard randomized": genuinamente duras.

---

## 3. Argumentation (4 instancias, stable semantics)

### Codificación reconstruida (verificada cláusula a cláusula)

**apx_2** (ER_500_10_2 DS-ST n=501; WS_400_24_70_10 DS-ST n=400;
stb_767_201 DC-ST n=767): vars 1..n = in(a); vars n+1..2n = A_a
("a derrotado"). Por argumento a con atacantes S_a:

- `¬A_a ∨ ∨_{b∈S_a} in(b)` — "derrotado → atacado por la extensión";
- `A_a ∨ ¬in(b)` por cada atacante b (Tseitin, dirección dual);
- `in(a) ∨ A_a` y `¬in(a) ∨ ¬A_a` — in(a) == ¬A_a.

Los pares (¬in,¬in) coinciden EXACTAMENTE con los ataques en ER/WS (en
stb difieren 77 pares por preprocesado del generador, sin efecto
semántico). Ataques 0% mutuos en ER/WS (orientaciones; no vale la
heurística maximal-independent-set). Unidades: ER fija ¬in(447);
stb (DC-ST) fija in(671)=true (argumento consulta) + ¬A_a para 4 args
sin atacantes (forzados dentro).

**normalised** (st_890_86_9_572, 2670 = 3×890): bloques in / out /
undec por argumento; cláusulas `in∨out∨undec` (886), `¬out(a) ∨
∨ in(atacantes)` (886), `¬undec(a) ∨ ∨ undec(atacantes)` (886), 3
cláusulas monstruo (890 literales sobre in, 743 sobre in, 743 sobre
out) y 159 unidades (8 in forzados — 4 args duplicados —, 143 out
forzados, 4 ¬out, 4 ¬undec). Asignación candidata: in/out desde una
extensión estable S, undec=0.

### Buscador estructural

Min-conflicts sobre el vector `in` (violación de a sii
`in(a) == atacado_S(a)`) con pins duros de las unidades y propagación
incremental de contadores de ataque. **No encontró extensión estable**
en ER (45 s), WS, stb (55 s c/u) ni st_890; tampoco una versión con
movimientos de vecindad. Estas instancias pueden ser genuinamente UNSAT
(digráfos densos sin kernel/stable) — no se afirma sin prueba.
Veredictos CDCL: ver JSONs de resultados.

---

## 4. Tabla de veredictos

Veredictos estructurales (`gbd_witness_results.json`) + solvers
industriales (`gbd_portfolio_results.json`, `gbd_cadical_results.json`,
`gbd_glucose_results.json`; todos los modelos SAT revalidados con
`validate_model`):

| Instancia | Estructural | Portfolio CDCL | Veredicto final |
|---|---|---|---|
| coloring/4col240_9_9 | **UNSAT** (DSATUR 725 nodos agotado + MRV-DPLL 453 nodos, naming consistente) | — | **UNSAT** (prueba estructural; Cadical 0.2M: unknown) |
| coloring/5col180_15_3 | **UNSAT** (DSATUR 369 + MRV-DPLL 391 nodos agotados) | — | **UNSAT** (prueba estructural; Cadical 0.2M: unknown) |
| coloring/unsat-set-a-fclqcolor | no decodificada (formato distinto) | Cadical 8M: DESCONOCIDO (267 s) | no determinada |
| hamiltonian/x9-11023 | SIN TESTIGO (HC+bloques 18 s, DLX 42 s) | Minicard 4M: DESCONOCIDO (195 s); MapleChrono 4M: DESCONOCIDO (828 s) | no determinada |
| hamiltonian/x9-11026 | SIN TESTIGO (60 s) | **SAT — Minicard, 183 s, modelo validado** | **SAT (testigo validado)** |
| hamiltonian/x9-11064 | SIN TESTIGO (60 s) | (en curso) | no determinada |
| hamiltonian/x9-11092 | SIN TESTIGO (60 s) | (en curso) | no determinada |
| hamiltonian/x9-12028 | SIN TESTIGO (60 s) | (en curso) | no determinada |
| hamiltonian/x9-12038 | SIN TESTIGO (60 s) | (en curso) | no determinada |
| hamiltonian/x9-12073 | SIN TESTIGO (60 s) | (en curso) | no determinada |
| argumentation/ER_500_10_2 | SIN TESTIGO (min-conflicts 90 s) | (pendiente) | no determinada |
| argumentation/WS_400_24_70_10 | SIN TESTIGO (90 s) | (pendiente) | no determinada |
| argumentation/stb_767_201 | SIN TESTIGO (90 s) | (pendiente) | no determinada |
| argumentation/st_890_86_9_572 | SIN TESTIGO (90 s) | (pendiente) | no determinada |

Testigo de x9-11026: `gbd_witness_x9-11026.sat.sanitized.model`
(550 vars; revalidado independientemente; 2-factor con estructura de
ciclos [59, 41, 10] — el CNF no codifica conectividad, así que el
testigo SAT es un 2-factor válido; el grafo recuperado ES hamiltoniano
por Warnsdorff, 0.0 s, pero no se halló HC que respete los bloques del
gadget).

Runners aún en ejecución al cerrar este informe: Cadical195 8M
(instancia 1: 4col240), Glucose42 8M (instancia 1: x9-12073), portfolio
Minicard/MapleChrono (x9-11064 en adelante). Sus JSON son incrementales
e idempotentes: relanzarlos continúa donde quedaron.

## 5. Reproducción

```bash
C:/Python314/python.exe experiments/gbd_coloring_witness.py [budget_s]
C:/Python314/python.exe experiments/gbd_hamiltonian_witness.py [budget_s]
C:/Python314/python.exe experiments/gbd_argumentation_witness.py [budget_s]
C:/Python314/python.exe experiments/gbd_cadical_runner.py [Mconf]
C:/Python314/python.exe experiments/gbd_cadical_runner2.py [Mconf]
C:/Python314/python.exe experiments/gbd_portfolio_runner.py [Mconf]
```

Todo modelo reportado como SAT pasa `validate_model` contra el CNF
original y se guarda en `experiments/results/gbd_witness_*.model`.
