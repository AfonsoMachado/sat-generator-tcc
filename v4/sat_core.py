"""
Gerador e executor de instâncias Max-sat / Partial Max-sat / Weighted Partial Max-sat.

Este módulo implementa:

1) Geração de fórmulas k-SAT aleatórias em forma normal conjuntiva (CNF)
2) Execução de experimentos utilizando o solver RC2 da biblioteca PySAT
3) Paralelização do experimento utilizando múltiplos processos

---------------------------------------------------------------------

REQUISITOS DO ALGORITMO DE GERAÇÃO (conforme descrição do texto):

O gerador deve garantir:

1. Impedimento da repetição de átomos numa cláusula
2. Cada cláusula deve possuir exatamente K literais
3. A cada cláusula deve ser reconstruído um vetor de candidatos
4. O vetor de candidatos deve conter todos os inteiros entre -N e N (exceto 0)
5. Um segundo vetor deve representar a cláusula em construção
6. Quando um literal é sorteado ele não pode ser escolhido novamente

Implementação em Python:

- O vetor de candidatos é reconstruído a cada cláusula
- Os literais possíveis são [-N..-1, 1..N]
- A seleção sem repetição é feita utilizando `random.sample`
- Isso reproduz o comportamento do algoritmo descrito no texto,
  onde uma "flag" era marcada no vetor de candidatos.

---------------------------------------------------------------------

FORMATO DAS FÓRMULAS

As fórmulas são geradas diretamente no formato aceito pelo PySAT:

    [[1, -3, 5], [-2, 4, -6], ...]

Cada sublista representa uma cláusula.

---------------------------------------------------------------------

EXPERIMENTOS

O módulo suporta três tipos de experimento:

- Max-sat
- Partial Max-sat
- Weighted Partial Max-sat

Os experimentos são executados em paralelo utilizando ProcessPoolExecutor.
"""

import os
import random
import time
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
from dataclasses import dataclass
from typing import Tuple

from pysat.examples.rc2 import RC2
from pysat.formula import WCNF

from solver_type import SolverType


# ------------------------------------------------------------------
# Configuração do experimento
# ------------------------------------------------------------------

@dataclass
class SATConfig:
    """
    Estrutura de configuração dos experimentos SAT.
    """

    num_formulas: int
    num_global_variables: int
    clauses_range: Tuple[int, int]
    k_literals_per_clause: int
    seed: int | None = None


# ------------------------------------------------------------------
# Geração de fórmulas CNF
# ------------------------------------------------------------------

def generate_random_cnf(num_vars: int, num_clauses: int, k: int):
    """
    Gera uma fórmula CNF aleatória k-SAT.

    A implementação segue os requisitos do algoritmo descrito no texto.
    """

    # Verificação de parâmetros
    if k > num_vars:
        raise ValueError("k não pode ser maior que o número de variáveis distintas")

    cnf = []

    for _ in range(num_clauses):

        # escolhe variáveis sem repetição
        variables = random.sample(range(1, num_vars + 1), k)

        # atribui sinal aleatório
        clause = [v if random.choice([True, False]) else -v for v in variables]

        cnf.append(clause)

    return cnf


# ------------------------------------------------------------------
# Solver Max-SAT
# ------------------------------------------------------------------

def solve_instance(args):
    N, M, k = args
    cnf = generate_random_cnf(N, M, k)

    wcnf = WCNF()
    wcnf.extend(cnf, weights=[1] * len(cnf))

    total_soft_weight = len(cnf)
    elapsed, satisf = run_rc2(wcnf, total_soft_weight)

    return M, elapsed, satisf


# ------------------------------------------------------------------
# Solver Partial Max-SAT
# ------------------------------------------------------------------

def solve_instance_partial_maxsat(args):
    N, M, k = args
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

def solve_instance_weighted_partial_maxsat(args):
    N, M, k = args
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
def run_rc2(wcnf, total_soft_weight):
    start = time.perf_counter()

    with RC2(wcnf) as rc2:
        rc2.compute()
        cost = rc2.cost

    elapsed = time.perf_counter() - start
    satisf = (total_soft_weight - cost) / total_soft_weight if total_soft_weight else 0

    return elapsed, satisf

# ------------------------------------------------------------------
# Execução do experimento
# ------------------------------------------------------------------

def generate_formulas_set(
    config: SATConfig,
    progress_callback=None,
    result_callback=None,
    solver_type=SolverType.MAXSAT,
    should_stop=None
):

    if config.seed is not None:
        random.seed(config.seed)

    N = config.num_global_variables
    k = config.k_literals_per_clause

    min_M, max_M = config.clauses_range

    instances = [
        (N, M, k)
        for M in range(min_M, max_M + 1)
        for _ in range(config.num_formulas)
    ]

    # selecionar solver
    if solver_type == SolverType.MAXSAT:
        solver = solve_instance
    elif solver_type == SolverType.PARTIAL_MAXSAT:
        solver = solve_instance_partial_maxsat
    elif solver_type == SolverType.WEIGHTED_PARTIAL_MAXSAT:
        solver = solve_instance_weighted_partial_maxsat
    else:
        solver = solve_instance

    results = []

    cpu = os.cpu_count()
    max_workers = max(1, int(cpu * 0.7))

    with ProcessPoolExecutor(max_workers=max_workers) as executor:

        futures = set()
        instance_iter = iter(instances)

        # envia primeiras tarefas
        for _ in range(max_workers):
            try:
                inst = next(instance_iter)
                futures.add(executor.submit(solver, inst))
            except StopIteration:
                break

        done_count = 0
        total = len(instances)

        while futures:

            # verifica stop
            if should_stop and should_stop():
                executor.shutdown(wait=False, cancel_futures=True)
                return results

            done, futures = wait(futures, return_when=FIRST_COMPLETED)

            for future in done:

                result = future.result()
                results.append(result)

                done_count += 1

                if result_callback:
                    result_callback(result)

                if progress_callback:
                    progress_callback(done_count, total)

                # envia nova tarefa
                try:
                    inst = next(instance_iter)
                    futures.add(executor.submit(solver, inst))
                except StopIteration:
                    pass

    return results
