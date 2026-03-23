import random
import time

from pysat.examples.rc2 import RC2
from pysat.formula import WCNF

from core.cnf_generator import generate_random_cnf

SolverArgs = tuple[int, int, int, int]
SolverResult = tuple[int, float, float]


# ------------------------------------------------------------------
# Solver Max-SAT
# ------------------------------------------------------------------

def solve_instance(args: SolverArgs) -> SolverResult:
    N, M, k, seed = args

    random.seed(seed)
    cnf = generate_random_cnf(N, M, k)

    wcnf = WCNF()
    wcnf.extend(cnf, weights=[1] * len(cnf))

    total_soft_weight = len(cnf)
    elapsed, satisf = run_rc2(wcnf, total_soft_weight)

    return M, elapsed, satisf


# ------------------------------------------------------------------
# Solver Partial Max-SAT
# ------------------------------------------------------------------

def solve_instance_partial_maxsat(args: SolverArgs) -> SolverResult:
    N, M, k, seed = args

    random.seed(seed)
    cnf = generate_random_cnf(N, M, k)
    split = M >> 1

    wcnf = WCNF()

    for clause in cnf[:split]:
        wcnf.append(clause)  # hard

    for clause in cnf[split:]:
        wcnf.append(clause, weight=1)  # soft

    total_soft_weight = len(cnf[split:])
    elapsed, satisf = run_rc2(wcnf, total_soft_weight)

    return M, elapsed, satisf


# ------------------------------------------------------------------
# Solver Weighted Partial Max-SAT
# ------------------------------------------------------------------

def solve_instance_weighted_partial_maxsat(args: SolverArgs) -> SolverResult:
    N, M, k, seed = args

    random.seed(seed)
    cnf = generate_random_cnf(N, M, k)
    split = M >> 1

    wcnf = WCNF()
    total_soft_weight = 0

    for clause in cnf[:split]:
        wcnf.append(clause)  # hard

    for clause in cnf[split:]:
        weight = random.randint(1, 10)
        total_soft_weight += weight
        wcnf.append(clause, weight=weight)

    elapsed, satisf = run_rc2(wcnf, total_soft_weight)

    return M, elapsed, satisf


# ------------------------------------------------------------------
# Run solver RC2 and return elapsed time and satisfaction ratio
# ------------------------------------------------------------------
def run_rc2(wcnf: WCNF, total_soft_weight: int) -> tuple[float, float]:
    start = time.perf_counter()

    with RC2(wcnf) as rc2:
        rc2.compute()
        cost = rc2.cost

    elapsed = time.perf_counter() - start
    satisf = (total_soft_weight - cost) / total_soft_weight if total_soft_weight else 0

    return elapsed, satisf
