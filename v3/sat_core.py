import random
import time
from dataclasses import dataclass
from typing import List, Tuple

from pysat.examples.rc2 import RC2
from pysat.formula import WCNF


@dataclass
class SATConfig:
    num_formulas: int
    num_global_variables: int
    clauses_range: Tuple[int, int]
    k_literals_per_clause: int
    seed: int | None = None


def generate_random_cnf(num_vars: int, num_clauses: int, k: int):
    """
    Gera uma CNF aleatória k-SAT diretamente em formato PySAT.
    """
    cnf = []

    for _ in range(num_clauses):
        vars_clause = random.sample(range(1, num_vars + 1), k)
        clause = []

        for v in vars_clause:
            if random.random() < 0.5:
                clause.append(v)
            else:
                clause.append(-v)

        cnf.append(clause)

    return cnf


def solve_with_rc2(cnf):
    """
    Resolve a fórmula usando RC2 (Max-SAT puro).
    """
    wcnf = WCNF()
    wcnf.extend(cnf, weights=[1] * len(cnf))

    for clause in cnf:
        wcnf.append(clause, weight=1)

    with RC2(wcnf, adapt=True) as rc2:
        model = rc2.compute()
        cost = rc2.cost

    return cost


def generate_formulas_set(config: SATConfig):

    if config.seed is not None:
        random.seed(config.seed)

    experiment_data = []

    N = config.num_global_variables
    k = config.k_literals_per_clause

    min_M, max_M = config.clauses_range

    for M in range(min_M, max_M + 1):
        print(f"M = {M}")

        for _ in range(config.num_formulas):

            cnf = generate_random_cnf(N, M, k)

            start = time.perf_counter()
            cost = solve_with_rc2(cnf)
            elapsed = time.perf_counter() - start

            satisf = (M - cost) / M if M else 0

            experiment_data.append((M, elapsed, satisf))

    return experiment_data