from collections import defaultdict

def _extract_xors(clauses):
    """Grupos XOR completos -> ecuaciones GF(2); resto -> residual.

    Devuelve (equations, residual, n_absorbed). Validación estricta:
    sin cláusulas duplicadas, sin variables repetidas dentro de una
    cláusula, cardinal exacto 2^(d-1) y paridad coherente — con ello la
    ecuación es equivalente (no solo implicada) al grupo.
    """
    groups = defaultdict(list)  # varset -> índices de cláusula
    for ci, c in enumerate(clauses):
        if len(c) < 2:
            continue
        key = frozenset(abs(lit) for lit in c)
        if len(key) != len(c):
            continue  # variable repetida (tautología/dup): no es bloqueador
        groups[key].append(ci)

    equations = []
    absorbed = set()
    for varset, cis in groups.items():
        d = len(varset)
        if len(cis) != (1 << (d - 1)):
            continue
        uniq = set()
        parities = set()
        ok = True
        for ci in cis:
            t = tuple(sorted(clauses[ci]))
            if t in uniq:
                ok = False
                break
            uniq.add(t)
            parities.add(sum(1 for lit in clauses[ci] if lit > 0) % 2)
            if len(parities) > 1:
                ok = False
                break
        if not ok or len(parities) != 1:
            continue
        parity = parities.pop()
        # Para d vars, la paridad de literales positivos de cada cláusula
        # es: d impar -> paridad == carga; d par -> paridad == 1 - carga.
        charge = parity if d % 2 == 1 else 1 - parity
        equations.append((tuple(sorted(varset)), charge))
        absorbed.update(cis)

    residual = [list(c) for ci, c in enumerate(clauses) if ci not in absorbed]
    return equations, residual, len(absorbed)


class _Engine:
    def __init__(self, clauses, n_vars, deadline, ge_stride,
                 branch_policy="activity", learning=True,
                 ge_provenance=True, xor_learning=True):
        if branch_policy not in ("activity", "nonlinear_first",
                                 "xor_first", "vsids"):
            raise ValueError(f"branch_policy desconocida: {branch_policy}")
