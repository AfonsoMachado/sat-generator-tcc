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
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from typing import Callable

from core.models import SATConfig
from core.solver_type import SolverType
from core.solvers import (
    SolverResult,
    solve_instance,
    solve_instance_partial_maxsat,
    solve_instance_weighted_partial_maxsat,
)

ProgressCallback = Callable[[int, int], bool | None]
ResultCallback = Callable[[SolverResult], None]
ShouldStopCallback = Callable[[], bool]


def generate_formulas_set(
        config: SATConfig,
        progress_callback: ProgressCallback | None = None,
        result_callback: ResultCallback | None = None,
        solver_type: SolverType = SolverType.MAXSAT,
        should_stop: ShouldStopCallback | None = None,
) -> list[SolverResult]:
    base_seed = config.seed if config.seed is not None else random.randint(0, 10 ** 9)

    N = config.num_global_variables
    k = config.k_literals_per_clause

    min_M, max_M = config.clauses_range

    instances = [
        (N, M, k, base_seed + idx)
        for idx, M in enumerate(
            M for M in range(min_M, max_M + 1)
            for _ in range(config.num_formulas)
        )
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

    results: list[SolverResult] = []

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
