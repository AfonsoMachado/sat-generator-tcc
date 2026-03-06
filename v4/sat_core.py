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

import random
import time
import os
from dataclasses import dataclass
from typing import Tuple

from pysat.examples.rc2 import RC2
from pysat.formula import WCNF

from concurrent.futures import ProcessPoolExecutor, as_completed


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

    cnf = []

    for _ in range(num_clauses):

        # vetor de candidatos reconstruído a cada cláusula
        candidates = list(range(-num_vars, 0)) + list(range(1, num_vars + 1))

        # seleção sem repetição
        clause = random.sample(candidates, k)

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

    start = time.perf_counter()

    with RC2(wcnf) as rc2:
        rc2.compute()
        cost = rc2.cost

    elapsed = time.perf_counter() - start

    satisf = (M - cost) / M if M else 0

    return M, elapsed, satisf


# ------------------------------------------------------------------
# Solver Partial Max-SAT
# ------------------------------------------------------------------

def solve_instance_partial_maxsat(args):

    N, M, k = args

    cnf = generate_random_cnf(N, M, k)

    wcnf = WCNF()

    split = M >> 1

    hard = cnf[:split]
    soft = cnf[split:]

    for clause in hard:
        wcnf.append(clause)

    for clause in soft:
        wcnf.append(clause, weight=1)

    start = time.perf_counter()

    with RC2(wcnf) as rc2:
        rc2.compute()
        cost = rc2.cost

    elapsed = time.perf_counter() - start

    satisf = (M - cost) / M if M else 0

    return M, elapsed, satisf


# ------------------------------------------------------------------
# Solver Weighted Partial Max-SAT
# ------------------------------------------------------------------

def solve_instance_weighted_partial_maxsat(args):

    N, M, k = args

    cnf = generate_random_cnf(N, M, k)

    wcnf = WCNF()

    split = M >> 1

    hard = cnf[:split]
    soft = cnf[split:]

    for clause in hard:
        wcnf.append(clause)

    for clause in soft:
        wcnf.append(clause, weight=random.randint(1, 10))

    start = time.perf_counter()

    with RC2(wcnf) as rc2:
        rc2.compute()
        cost = rc2.cost

    elapsed = time.perf_counter() - start

    satisf = (M - cost) / M if M else 0

    return M, elapsed, satisf


# ------------------------------------------------------------------
# Execução do experimento
# ------------------------------------------------------------------

def generate_formulas_set(
    config: SATConfig,
    progress_callback=None,
    result_callback=None,
    solver_type="Max-SAT",
    should_stop=None
):
    """
    Executa o experimento SAT completo.

    Fluxo:

    1) Gera todas as instâncias do experimento
    2) Distribui cada instância para um processo
    3) Executa o solver selecionado
    4) Coleta métricas de tempo e satisfatibilidade
    """

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

    if solver_type == "Max-SAT":
        solver = solve_instance
    elif solver_type == "Partial Max-SAT":
        solver = solve_instance_partial_maxsat
    elif solver_type == "Weighted Partial Max-SAT":
        solver = solve_instance_weighted_partial_maxsat
    else:
        solver = solve_instance

    results = []

    cpu = os.cpu_count()

    with ProcessPoolExecutor(max_workers=cpu) as executor:

        futures = [executor.submit(solver, inst) for inst in instances]

        for i, future in enumerate(as_completed(futures), 1):

            if should_stop and should_stop():
                executor.shutdown(wait=False, cancel_futures=True)
                break

            result = future.result()
            results.append(result)

            if result_callback:
                result_callback(result)

            if progress_callback:
                progress_callback(i, len(instances))

    return results
