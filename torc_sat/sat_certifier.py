"""Certificador SAT verificado: CDCL propone, el validador decide.

Soundness: el veredicto SAT solo se emite junto a un modelo que satisface
TODAS las clausulas, comprobado aqui clausula a clausula en tiempo lineal.
El solver CDCL es un mero propositor: un modelo que no valida jamas
produce veredicto (fail-closed -> UNKNOWN). Es el espejo SAT de
drat_verified (alli Lingeling propone la prueba DRUP y el verificador
propio la comprueba; aqui Glucose4 propone el modelo y validate_model
lo comprueba).
"""

from pysat.solvers import Glucose4

DEFAULT_CONFLICT_BUDGET = 100_000  # el check debe seguir siendo rapido


def validate_model(clauses: list, model: list) -> bool:
    """True sii el modelo es consistente y satisface todas las clausulas.

    Consistente: sin literal 0 y sin una variable con ambos signos. Un
    "modelo" contradictorio como [1, -1] satisface [[1], [-1]] (UNSAT)
    clausula a clausula; aceptarlo seria un falso SAT — la mitad espejo
    de un falso UNSAT. El validador es la frontera de soundness: cualquier
    entrada que no sea una asignacion valida se rechaza (fail-closed).
    """
    if model is None:
        return False
    asg = set(model)
    if 0 in asg:
        return False
    if any(-lit in asg for lit in asg):
        return False
    return all(any(lit in asg for lit in clause) for clause in clauses)


def certify_sat(cnf, conflict_budget: int = DEFAULT_CONFLICT_BUDGET) -> list | None:
    """Devuelve un modelo validado de `cnf`, o None si no hay certificado.

    None significa "sin veredicto": la instancia puede ser UNSAT, o SAT
    pero fuera del presupuesto de conflictos, o (nunca deberia) el solver
    devolvio un modelo que no valida.
    """
    if not cnf.clauses:
        # Formula vacia: trivialmente SAT con cualquier asignacion.
        return [v for v in range(1, cnf.n_vars + 1)]
    with Glucose4(bootstrap_with=cnf.clauses) as s:
        s.conf_budget(conflict_budget)
        sat = s.solve_limited()
        if sat is not True:
            return None
        model = s.get_model()
    if not validate_model(cnf.clauses, model):
        return None
    return model
