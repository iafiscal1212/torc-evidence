# MVRoundRobin_n14_d10_v4 — UNSAT por diseño combinatorio (prueba por conteo)

**Veredicto: INSATISFACTIBLE**, por un argumento de pigeonhole verificado
mecánicamente contra el CNF. No hace falta solver: la instancia codifica un
calendario round-robin de 14 equipos en 10 días, y 14 equipos no pueden
jugar todos contra todos en menos de 13 días.

Verificación ejecutable (recuentos exactos sobre el CNF, ~1,5 s):

```
python experiments/gbd_mvr_decode.py     # exit 0, todas las comprobaciones OK
```

## 1. Correspondencia exacta cláusula ↔ restricción

El CNF (`benchmarks/external/gbd_unknown/scheduling/MVRoundRobin_n14_d10_v4.cnf`,
`p cnf 7280 349531`) contiene **exactamente** dos tipos de cláusulas y nada
más (recuento verificado: 91 + 349.440 = 349.531, 0 otras):

**(C1) 91 cláusulas positivas de longitud 40**, disjuntas, sobre las
variables 41..7280. Cada una es un *partido*: los 91 grupos corresponden a
los C(14,2) = 91 emparejamientos de 14 equipos. Si el grupo m cubre las
variables v+1..v+40, la variable de índice s ∈ {0..39} dentro del grupo es

> x_{m,s} = «el partido m usa el hueco s», donde el **día** de s es
> ⌊s/4⌋ ∈ {0..9} (10 días × 4 huecos por día).

La cláusula (x_{m,0} ∨ … ∨ x_{m,39}) dice: *el partido m usa al menos un
hueco*. (La partición de los 40 índices en 10 días de 4 no se supone: la
infiere el propio verificador por union-find a partir de las cláusulas
equipo-día, y resulta ser exactamente los bloques consecutivos de 4.)

**(C2) 349.440 clausulas binarias, todas negativas**, en tres subclases
(recuentos exactos verificados):

| Subclase | Recuento | Significado |
|---|---|---|
| intra-grupo | 10.920 = 91 × 60 × 2 (duplicadas) | un partido usa **a lo sumo un hueco por día** (los 60 = C(4,2)×10 pares de huecos del mismo día, dentro del mismo partido) |
| mismo hueco | 207.480 = 3.003×40 + 1.092×80 | **a lo sumo un partido por hueco**: todo par de partidos distintos prohíbe (¬x_{m,s} ∨ ¬x_{m',s}) para los 40 s; en los pares del mismo equipo aparecen duplicadas (80) |
| equipo-día | 131.040 = 1.092 × 120 | **dos partidos que comparten equipo no juegan el mismo día**: para cada uno de los 1.092 = 14×C(13,2) pares de partidos con equipo común, y cada día, se prohíben las 12 combinaciones de huecos distintos del día (con las 4 de hueco igual duplicadas de la fila anterior son las 16 = 4×4 completas) |

La **estructura de equipos** no se supone tampoco: el grafo «comparten
equipo» sobre los 91 partidos (arista si el par tiene cláusulas equipo-día)
es 24-regular con 1.092 aristas, y el verificador extrae sus cliques
maximales por Bron–Kerbosch: **exactamente 14 cliques K13** (los equipos),
cada partido pertenece a **exactamente 2**, y cada par de equipos se corta
en **exactamente 1** partido — es decir, los 91 partidos son precisamente
los 91 emparejamientos de un round-robin de 14 equipos (el grafo es L(K14)).

La subclase intra-grupo documenta la codificación pero no se usa en la
prueba; el argumento 1 usa (C1) + mismo-hueco y el argumento 2 usa (C1) +
equipo-día.

## 2. Prueba (pigeonhole)

**Argumento 1 — inyección partidos ↪ huecos (el más corto).** Supongamos
que existe una asignación satisfactoria.

1. Por (C1), cada uno de los 91 partidos tiene al menos una variable
   verdadera; para cada partido m **fijamos una**, x_{m,s(m)}.
2. Por la subclase mismo-hueco de (C2) — que el verificador confirma para
   **los 4.095 = C(91,2) pares de partidos y los 40 huecos** — ningún par
   de partidos distintos puede tener verdadera la misma variable de hueco.
   Por tanto la elección m ↦ s(m) es **inyectiva**: 91 partidos se inyectan
   en 40 huecos.
3. 91 > 40. Contradicción (principio del palomar). ∎

**Argumento 2 — equipo-días (la lectura de diseño del calendario).** Con la
misma elección de un hueco por partido, sea d(m) = ⌊s(m)/4⌋ su día. Por la
subclase equipo-día de (C2), dos partidos que comparten equipo tienen
d(m) ≠ d(m'). Fijado un equipo T, sus 13 partidos (clique K13) necesitan
13 días distintos, pero solo hay 10. 13 > 10: contradicción. ∎

(Forma global equivalente del argumento 2: en cada día los partidos son dos
a dos sin equipo común, luego como mucho ⌊14/2⌋ = 7 partidos por día;
10 días × 7 = 70 < 91 partidos.)

Ambos argumentos son válidos de forma independiente; el primero usa solo
(C1) + mismo-hueco, el segundo solo (C1) + equipo-día. El segundo es el que
«explica» la instancia: un round-robin completo de 14 equipos exige 13
jornadas y el calendario ofrece 10.

## 3. Por qué esto es un certificado

- Las premisas (C1), (C2)-equipo-día y la estructura de 14 equipos × 13
  partidos no se afirman: las **recuenta y comprueba** sobre el CNF, cláusula
  a cláusula, `experiments/gbd_mvr_decode.py` (exit 0 solo si todos los
  recuentos y la cobertura completa de las 16 combinaciones por día y par
  de equipo son exactos).
- El paso lógico de las premisas al veredicto es el palomar finito de
  arriba: 13 partidos de un equipo, 10 días, a lo sumo uno por día.
- Es el certificado que un CDCL no produce: la instancia es un CSP de
  tipo aleatorio duro para resolución (z3 la declara UNSAT en ~12 s sobre
  la decodificación, pero cadical195/minisat22 no refutan ni el núcleo
  mínimo de 11 grupos / 12.331 cláusulas en >15 min, y el trace DRUP
  superó 3,3 GB antes de abortar). El argumento de conteo la cierra en
  tiempo de lectura del fichero.

Consistente con: z3 UNSAT sobre la decodificación exacta 1:1 (fase 2) y con
el nombre de la instancia (n14 equipos, d10 días, v4 huecos/día: un
round-robin completo de 14 equipos exige 13 jornadas; 10 no bastan).
