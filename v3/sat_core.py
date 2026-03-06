import random
import time
from dataclasses import dataclass
from typing import Tuple, List

from pysat.examples.rc2 import RC2
from pysat.formula import WCNF

from concurrent.futures import ProcessPoolExecutor, as_completed
import os


@dataclass
class SATConfig:
    num_formulas: int
    num_global_variables: int
    clauses_range: Tuple[int, int]
    k_literals_per_clause: int
    seed: int | None = None


# ---------------------------------------------------------
# geração da CNF
# ---------------------------------------------------------

def generate_random_cnf(num_vars: int, num_clauses: int, k: int):

    cnf = []

    for _ in range(num_clauses):

        # vetor de candidatos [-N..-1, 1..N] reconstruído a cada cláusula
        # para garantir que cada cláusula tenha literais distintos
        candidates = list(range(-num_vars, 0)) + list(range(1, num_vars + 1))

        # sorteia K literais distintos diretamente
        # impedindo repetição de átomos entre os disponíveis
        # para escolha na formação das cláusulas
        clause = random.sample(candidates, k)

        cnf.append(clause)

    return cnf


# ---------------------------------------------------------
# solver
# ---------------------------------------------------------

def solve_instance(args):

    N, M, k = args

    cnf = generate_random_cnf(N, M, k)

    wcnf = WCNF()
    wcnf.extend(cnf, weights=[1]*len(cnf))

    start = time.perf_counter()

    with RC2(wcnf) as rc2:
        rc2.compute()
        cost = rc2.cost

    elapsed = time.perf_counter() - start

    satisf = (M - cost) / M if M else 0

    return (M, elapsed, satisf)

# ---------------------------------------------------------
# solver PARTIAL MAX-SAT
# ---------------------------------------------------------

def solve_instance_partial_maxsat(args):

    N, M, k = args

    cnf = generate_random_cnf(N, M, k)

    wcnf = WCNF()

    split = int(M * 0.5)  # metade hard, metade soft

    hard = cnf[:split]
    soft = cnf[split:]

    # hard clauses
    for clause in hard:
        wcnf.append(clause)

    # soft clauses
    for clause in soft:
        wcnf.append(clause, weight=1)

    start = time.perf_counter()

    with RC2(wcnf) as rc2:
        rc2.compute()
        cost = rc2.cost

    elapsed = time.perf_counter() - start

    satisf = (M - cost) / M if M else 0

    return (M, elapsed, satisf)


# ---------------------------------------------------------
# solver WEIGHTED PARTIAL MAX-SAT
# ---------------------------------------------------------

def solve_instance_weighted_partial_maxsat(args):

    N, M, k = args

    cnf = generate_random_cnf(N, M, k)

    wcnf = WCNF()

    split = int(M * 0.5)

    hard = cnf[:split]
    soft = cnf[split:]

    # hard clauses
    for clause in hard:
        wcnf.append(clause)

    # soft clauses com pesos aleatórios
    for clause in soft:
        weight = random.randint(1, 10)
        wcnf.append(clause, weight=weight)

    start = time.perf_counter()

    with RC2(wcnf) as rc2:
        rc2.compute()
        cost = rc2.cost

    elapsed = time.perf_counter() - start

    satisf = (M - cost) / M if M else 0

    return (M, elapsed, satisf)


# ---------------------------------------------------------
# experimento paralelo
# ---------------------------------------------------------

def generate_formulas_set(config: SATConfig, progress_callback=None, solver_type="Max-SAT"):

    if config.seed is not None:
        random.seed(config.seed)

    N = config.num_global_variables
    k = config.k_literals_per_clause

    min_M, max_M = config.clauses_range

    instances = []

    for M in range(min_M, max_M + 1):
        for _ in range(config.num_formulas):
            instances.append((N, M, k))

    results = []

    with ProcessPoolExecutor() as executor:

        if solver_type == "Max-SAT":
            solver = solve_instance

        elif solver_type == "Partial Max-SAT":
            solver = solve_instance_partial_maxsat

        elif solver_type == "Weighted Partial Max-SAT":
            solver = solve_instance_weighted_partial_maxsat

        else:
            solver = solve_instance

        futures = [executor.submit(solver, inst) for inst in instances]

        for i, future in enumerate(as_completed(futures), 1):

            result = future.result()
            results.append(result)

            if progress_callback:
                progress_callback(i, len(instances))

    return results
