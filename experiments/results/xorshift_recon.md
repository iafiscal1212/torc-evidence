# Reconstrucción y ataque del generador xorshift (gbd_unknown)

**Fecha:** 2026-10-28
**Instancias:** las 22 de `benchmarks/external/gbd_unknown/` (`xorshift_r{14,15,16}_*.sanitized.cnf`), veredicto UNKNOWN para la comunidad SAT.
**Scripts:** `experiments/xorshift_recon.py`, `experiments/xorshift_decode.py`, `experiments/xorshift_smt_attack.py`, `experiments/xorshift_cvc5_attack.py`, `experiments/xorshift_emit_c.py`, `experiments/xorshift_brute_all.sh`, `experiments/xorshift_validate_seeds.py`.
**Datos:** `results/xorshift_recon.json`, `results/xorshift_programs.json`, `results/xorshift_smt_attack.json`, `results/xorshift_brute_results.json`, `results/xorshift_brute_*.log`.

## 1. Estructura reconstruida (22/22 instancias)

Toda instancia es un **DAG combinacional limpio**, verificado con reconstrucción
completa (falla ruidosa si algo no clasifica):

- **32 variables de entrada (vars 1..32) = semilla de 32 bits.**
- Toda otra variable está definida **exactamente una vez** por:
  - **Puertas XOR Tseitin de 3 variables** (`y = a ⊕ b`, carga 0; `y = max(varset)`),
  - **Puertas AND/OR Tseitin** que forman **sumadores ripple-carry de 32 bits**
    (cada sumador = 63 AND + 63 OR; carry-lookahead ausente),
- **32 cláusulas unitarias** = los 32 bits de salida observados (constantes).

| instancia | vars | cláusulas | XOR | AND | OR | sumadores |
|---|---|---|---|---|---|---|
| xorshift_r14_133 | 2558 | 9128 | 1518 | 504 | 504 | 8 |
| xorshift_r14_154 | 2401 | 8626 | 1487 | 441 | 441 | 7 |
| xorshift_r14_158 | 2401 | 8626 | 1487 | 441 | 441 | 7 |
| xorshift_r14_165 | 2401 | 8626 | 1487 | 441 | 441 | 7 |
| xorshift_r14_176 | 2244 | 8124 | 1456 | 378 | 378 | 6 |
| xorshift_r15_105 | 2337 | 8496 | 1549 | 378 | 378 | 6 |
| xorshift_r15_119 | 2651 | 9500 | 1611 | 504 | 504 | 8 |
| xorshift_r15_129 | 2651 | 9500 | 1611 | 504 | 504 | 8 |
| xorshift_r15_177 | 2023 | 7492 | 1487 | 252 | 252 | 4 |
| xorshift_r15_37 | 2651 | 9500 | 1611 | 504 | 504 | 8 |
| xorshift_r15_40 | 2651 | 9500 | 1611 | 504 | 504 | 8 |
| xorshift_r15_41 | 2651 | 9500 | 1611 | 504 | 504 | 8 |
| xorshift_r15_47 | 2337 | 8496 | 1549 | 378 | 378 | 6 |
| xorshift_r16_110 | 2430 | 8868 | 1642 | 378 | 378 | 6 |
| xorshift_r16_136 | 2901 | 10374 | 1735 | 567 | 567 | 9 |
| xorshift_r16_16 | 2587 | 9370 | 1673 | 441 | 441 | 7 |
| xorshift_r16_171 | 2744 | 9872 | 1704 | 504 | 504 | 8 |
| xorshift_r16_181 | 2430 | 8868 | 1642 | 378 | 378 | 6 |
| xorshift_r16_188 | 2430 | 8868 | 1642 | 378 | 378 | 6 |
| xorshift_r16_21 | 3215 | 11378 | 1797 | 693 | 693 | 11 |
| xorshift_r16_87 | 2587 | 9370 | 1673 | 441 | 441 | 7 |
| xorshift_r16_98 | 2587 | 9370 | 1673 | 441 | 441 | 7 |

## 2. El generador: xorshift32 clásico (13, 17, 5)

El stream lineal (la parte XOR pura) fue identificado por **fuerza bruta sobre
triples de desplazamientos**: es el **xorshift32 de Marsaglia con parámetros
(13, 17, 5)**:

```
x ^= x << 13;  x ^= x >> 17;  x ^= x << 5
```

MATCH exacto bit a bit entre el stream reconstruido y el generador de referencia.

## 3. Forma funcional decodificada (r14_133, la única necesaria de exhibir)

Con `x_k = T^k(semilla)` (k-ésima iteración del xorshift32 sobre la semilla) y
`+` = suma modular de 32 bits (los sumadores ripple), la salida de r14_133 es:

```
w0 = s + x1
w1 = (w0 ⊕ x2) + x3
w2 = w1 + x4
w3 = w2 + x5
w4 = (w3 ⊕ x6) + x7
w5 = (w4 ⊕ x8 ⊕ x9) + x10
w6 = w5 + x11
w7 = w6 + x12
out = w7 ⊕ x13
```

Es decir: una cadena alternada de **sumas modulares y XORs** sobre el stream
xorshift — un "whitening" ARX que destruye la linealidad GF(2) del generador
desnudo. El decodificador (`xorshift_decode.py`) obtiene forma cerrada para
12/22 instancias; las otras 10 tienen máscaras intermedias que no reducen a
≤3 streams (documentado en `results/xorshift_programs.json`). El barrido no
necesita la forma cerrada: evalúa el DAG directamente.

**Significado de r14/r15/r16: NO identificado.** Los histogramas de offsets y
el número de capas difieren entre familias (a mayor r, más puertas XOR y más
sumadores de media), pero no se encontró un mapeo a parámetros del generador.
Se reporta como desconocido.

## 4. Ataques SMT: todos fallaron (reporte honesto)

Todos contra r15_177 (la instancia más pequeña: 2023 vars, 4 sumadores):

| solver / encoding | límite | resultado |
|---|---|---|
| Z3 gate-level (CNF tal cual) | 120 s | unknown (timeout) |
| Z3 word-level (sumadores como `bvadd` nativo, XORs a nivel de bit) | 180 s | unknown (timeout) |
| Z3 `TryFor(simplify + solve-eqs + bit-blast + sat)` | 550 s | canceled |
| cvc5 word-level | 300 s | unknown (TIMEOUT) |

Ningún solver SMT resuelve ni siquiera la instancia más fácil. `bitwuzla`
quedó instalado pero sin probar (bug de API en el script, no corregido a
tiempo); queda como cross-check futuro.

## 5. Ataque que funciona: barrido exhaustivo 2^32 bitsliced en C

`xorshift_emit_c.py` emite un programa C que evalúa el DAG completo con
**64 semillas por uint64** (bitslicing: cada puerta es una operación de 64 bits).
Coste: 2^32 / 64 = 67.1 M iteraciones de ~1.5–3.5 K operaciones de máquina.

**Autotest** (`--selftest 123456789`): objetivo = salida de una semilla
conocida. El barrido la encontró — junto con una colisión (2751164509),
prueba de que F no es inyectiva — en **31 s** (WSL, gcc -O2).

**Resultado del barrido de las 22 instancias:** ver tabla en §6.
Cada semilla reportada fue **validada contra el CNF original** con
`validate_model` (`torc_sat/sat_certifier.py`): evaluación del DAG →
asignación completa de las n variables → chequeo cláusula a cláusula.

## 6. Veredictos por instancia

**LAS 22 INSTANCIAS SON SAT.** 49 semillas distintas encontradas (1–4 por
instancia), **todas validadas** contra el CNF original con `validate_model`
(0 inválidas). Tiempo total del barrido: 830 s (media 37 s/instancia, WSL +
gcc -O2). Datos completos: `results/xorshift_brute_results.json`.

| instancia | veredicto | semillas válidas |
|---|---|---|
| xorshift_r14_133 | SAT | 2165109229 |
| xorshift_r14_154 | SAT | 240247875, 2466046806, 3383783590 |
| xorshift_r14_158 | SAT | 208881714, 2914620559, 4016514323 |
| xorshift_r14_165 | SAT | 1070413753, 2436577367, 4022569926 |
| xorshift_r14_176 | SAT | 42347963 |
| xorshift_r15_105 | SAT | 2559683248 |
| xorshift_r15_119 | SAT | 750412887, 4239418319 |
| xorshift_r15_129 | SAT | 1049860713, 3504039205 |
| xorshift_r15_177 | SAT | 91196424 |
| xorshift_r15_37 | SAT | 2258576795, 2310665936, 3791626360 |
| xorshift_r15_40 | SAT | 3140303402, 3893670674 |
| xorshift_r15_41 | SAT | 924868836, 1149946705, 2541498811 |
| xorshift_r15_47 | SAT | 691770733, 1882277587 |
| xorshift_r16_110 | SAT | 896596199, 1005616819 |
| xorshift_r16_136 | SAT | 1841590741, 4142332179 |
| xorshift_r16_16 | SAT | 1234371770, 1333575779 |
| xorshift_r16_171 | SAT | 1961083788, 2057308978, 3911442053 |
| xorshift_r16_181 | SAT | 3387454251 |
| xorshift_r16_188 | SAT | 423732903, 1403025851, 1881074016 |
| xorshift_r16_21 | SAT | 808282664, 1241626961, 3975363987, 4167587133 |
| xorshift_r16_87 | SAT | 1153780761, 3439866697, 3626490302, 4124735812 |
| xorshift_r16_98 | SAT | 2175304606 |

Las 22 instancias UNKNOWN de GBD quedan resueltas como SAT, con modelo
completo verificable cláusula a cláusula para cada semilla reportada.

## 7. Limitaciones

- **Completitud:** el barrido enumera las 2^32 semillas, así que las tablas
  de §6 listan TODAS las preimágenes de cada salida observada (no solo un
  testigo). Si alguna instancia hubiera agotado el espacio sin match, el
  veredicto habría sido "UNSAT por agotamiento exhaustivo" — tan fuerte como
  la reconstrucción del DAG (verificada con asserts completos) pero sin
  certificado verificable por terceros (p.ej. DRAT). No ocurrió: las 22
  son SAT.
- F no es inyectiva: varias semillas pueden dar la misma salida; el barrido
  reporta TODAS las que encuentra.
- El significado de r14/r15/r16 no fue identificado.
- 10/22 instancias no decodifican a forma cerrada ≤3 streams; no obstante el
  barrido las resuelve igualmente porque evalúa el DAG.
