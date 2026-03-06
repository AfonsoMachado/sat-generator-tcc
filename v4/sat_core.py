"""
Gerador e executor de instâncias Max-SAT / Partial Max-SAT / Weighted Partial Max-SAT.

Este módulo implementa:

1) Geração de fórmulas k-SAT aleatórias em forma normal conjuntiva (CNF)
2) Execução de experimentos utilizando o solver RC2 da biblioteca PySAT
3) Paralelização do experimento utilizando múltiplos processos

---------------------------------------------------------------------

REQUISITOS DO ALGORITMO DE GERAÇÃO (conforme descrição do texto):

O gerador deve garantir:

1. Impedimento da repetição de átomos dentro de uma cláusula
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

- Max-SAT
- Partial Max-SAT
- Weighted Partial Max-SAT

Os experimentos são executados em paralelo utilizando ProcessPoolExecutor.
"""

import random
import time
import os
from dataclasses import dataclass
from typing import Tuple

from pysat.examples.rc2 import RC2
from pysat.formula import WCNF

from concurrent.futures import ProcessPoolExecutor


# ------------------------------------------------------------------
# Configuração do experimento
# ------------------------------------------------------------------

@dataclass
class SATConfig:
    """
    Estrutura de configuração dos experimentos SAT.

    Attributes
    ----------
    num_formulas : int
        Número de fórmulas geradas para cada valor de M.

    num_global_variables : int
        Número total de variáveis proposicionais (N).

    clauses_range : Tuple[int, int]
        Intervalo de número de cláusulas M.

    k_literals_per_clause : int
        Número de literais por cláusula (k-SAT).

    seed : int | None
        Seed opcional para reprodutibilidade.
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

    A implementação segue os requisitos do algoritmo descrito no texto:

    1) A cada cláusula é criado um vetor de candidatos
    2) O vetor contém todos os literais possíveis [-N..-1, 1..N]
    3) Os literais são selecionados sem repetição
    4) Cada cláusula contém exatamente K literais
    5) Um vetor separado representa a cláusula em construção

    Parameters
    ----------
    num_vars : int
        Número de variáveis proposicionais (N).

    num_clauses : int
        Número de cláusulas da fórmula (M).

    k : int
        Número de literais por cláusula.

    Returns
    -------
    List[List[int]]
        Fórmula CNF no formato aceito pelo PySAT.
    """

    cnf = []

    for _ in range(num_clauses):

        # ---------------------------------------------------------
        # Vetor de candidatos
        #
        # Representa todos os literais possíveis:
        #   [-N .. -1, 1 .. N]
        #
        # Este vetor é reconstruído a cada cláusula conforme
        # descrito no algoritmo original.
        # ---------------------------------------------------------

        candidates = list(range(-num_vars, 0)) + list(range(1, num_vars + 1))

        # ---------------------------------------------------------
        # Seleção de K literais distintos
        #
        # random.sample garante:
        #  - ausência de repetição
        #  - comportamento equivalente à "flag" mencionada
        #    no algoritmo original.
        # ---------------------------------------------------------

        clause = random.sample(candidates, k)

        cnf.append(clause)

    return cnf


# ------------------------------------------------------------------
# Solver Max-SAT
# ------------------------------------------------------------------

def solve_instance(args):
    """
    Resolve uma instância Max-SAT utilizando RC2.
    """

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
    """
    Resolve uma instância Partial Max-SAT.

    Metade das cláusulas são tratadas como hard e metade como soft.
    """

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
    """
    Resolve uma instância Weighted Partial Max-SAT.

    As cláusulas soft recebem pesos aleatórios.
    """

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
# Processamento em lote (otimização de paralelismo)
# ------------------------------------------------------------------

def solve_batch(batch_args):
    """
    Resolve um lote de instâncias em sequência.

    Esta estratégia reduz o overhead de criação de tarefas
    no multiprocessing quando há muitas instâncias.
    """

    solver, batch = batch_args

    results = []

    for args in batch:
        results.append(solver(args))

    return results


# ------------------------------------------------------------------
# Execução do experimento
# ------------------------------------------------------------------

def generate_formulas_set(config: SATConfig, progress_callback=None, solver_type="Max-SAT"):
    """
    Executa o experimento SAT completo.

    A função:

    1) Gera todas as instâncias do experimento
    2) Distribui o trabalho entre múltiplos processos
    3) Executa os solvers selecionados
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

    batch_size = max(
        50,
        len(instances) // (cpu * 8)
    )

    batches = [
        instances[i:i + batch_size]
        for i in range(0, len(instances), batch_size)
    ]

    total_instances = len(instances)

    with ProcessPoolExecutor(max_workers=cpu) as executor:

        futures = executor.map(
            solve_batch,
            [(solver, batch) for batch in batches]
        )

        completed = 0

        for batch_result in futures:

            results.extend(batch_result)

            completed += len(batch_result)

            if progress_callback:
                progress_callback(completed, total_instances)

    return results