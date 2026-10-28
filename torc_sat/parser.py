"""DIMACS CNF parser."""

from dataclasses import dataclass, field


@dataclass
class CNFInstance:
    """Parsed CNF formula."""
    n_vars: int
    n_clauses: int
    clauses: list  # list of list[int], each literal is signed var
    comments: list = field(default_factory=list)

    @property
    def clause_lengths(self):
        return [len(c) for c in self.clauses]

    @property
    def max_clause_len(self):
        return max(self.clause_lengths) if self.clauses else 0

    @property
    def min_clause_len(self):
        return min(self.clause_lengths) if self.clauses else 0


def parse_dimacs(path: str) -> CNFInstance:
    """Parse a DIMACS CNF file.

    Format:
        c comment lines
        p cnf <n_vars> <n_clauses>
        <lit1> <lit2> ... 0
        ...
    """
    comments = []
    n_vars = 0
    n_clauses = 0
    clauses = []
    header_seen = False

    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("c"):
                comments.append(line[1:].strip())
                continue
            if line.startswith("p"):
                parts = line.split()
                if len(parts) >= 4 and parts[1] == "cnf":
                    n_vars = int(parts[2])
                    n_clauses = int(parts[3])
                    header_seen = True
                continue
            if line.startswith("%"):
                break
            # Clause line: integers terminated by 0
            lits = list(map(int, line.split()))
            # Handle multi-line clauses or multiple clauses per line
            buf = []
            for lit in lits:
                if lit == 0:
                    if buf:
                        clauses.append(buf)
                        buf = []
                else:
                    buf.append(lit)
            # Leftover lits without terminating 0 (some generators omit it)
            if buf:
                clauses.append(buf)

    if not header_seen:
        # Infer from data
        all_vars = set()
        for c in clauses:
            for lit in c:
                all_vars.add(abs(lit))
        n_vars = max(all_vars) if all_vars else 0
        n_clauses = len(clauses)

    return CNFInstance(
        n_vars=n_vars,
        n_clauses=n_clauses,
        clauses=clauses,
        comments=comments,
    )


def parse_dimacs_string(text: str) -> CNFInstance:
    """Parse DIMACS CNF from a string."""
    import tempfile
    import os
    fd, path = tempfile.mkstemp(suffix=".cnf")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text)
        return parse_dimacs(path)
    finally:
        os.unlink(path)
