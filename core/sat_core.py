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
    """
    Gera e resolve um conjunto de instâncias SAT/Max-SAT de forma paralela.

    Essa função representa o núcleo da execução experimental, sendo responsável por:
    - Gerar instâncias a partir dos parâmetros definidos em 'SATConfig'
    - Distribuir a execução entre múltiplos processos (paralelismo)
    - Coletar resultados incrementalmente
    - Atualizar a interface via callbacks (progresso e resultados)
    - Permitir interrupção controlada da execução

    Fluxo geral:
    1. Geração das instâncias (combinação de M e amostras)
    2. Seleção do solver conforme o tipo (MaxSAT / Partial / Weighted)
    3. Execução paralela via 'ProcessPoolExecutor'
    4. Coleta incremental dos resultados conforme finalização das tarefas
    5. Atualização de progresso e retorno final consolidado

    Parâmetros:
    - config: configuração do experimento (N, k, intervalo de M, número de fórmulas, seed)
    - progress_callback: função opcional chamada a cada instância concluída (done, total)
    - result_callback: função opcional chamada a cada resultado individual
    - solver_type: define qual abordagem de resolução será utilizada
    - should_stop: função opcional para interrupção antecipada da execução

    Retorno:
    - Lista de resultados ('SolverResult') contendo (M, tempo, satisfazibilidade)

    Observações importantes:
    - A execução utiliza paralelismo baseado em CPU (~70% dos núcleos disponíveis)
    - Seeds são derivadas de uma seed base para garantir diversidade estatística
    - O processamento é incremental (streaming de resultados), evitando bloqueios longos
    """

    # Define seed base (fixa para reprodutibilidade ou aleatória para diversidade)
    base_seed = config.seed if config.seed is not None else random.randint(0, 10 ** 9)

    k = config.k_literals_per_clause
    min_M, max_M = config.clauses_range
    step_M = config.clauses_step

    # Geração das instâncias (cartesiano de M x num_formulas)
    # Cada instância recebe uma seed única derivada da base
    # Em modo razão, N é calculado por ponto: N = round(M / ratio)
    if config.ratio is not None:
        instances = [
            (round(M / config.ratio), M, k, base_seed + idx)
            for idx, M in enumerate(
                M for M in range(min_M, max_M + 1, step_M)
                for _ in range(config.num_formulas)
            )
        ]
    else:
        N = config.num_global_variables
        instances = [
            (N, M, k, base_seed + idx)
            for idx, M in enumerate(
                M for M in range(min_M, max_M + 1, step_M)
                for _ in range(config.num_formulas)
            )
        ]

    # Seleção dinâmica do solver conforme o tipo escolhido
    if solver_type == SolverType.MAXSAT:
        solver = solve_instance
    elif solver_type == SolverType.PARTIAL_MAXSAT:
        solver = solve_instance_partial_maxsat
    elif solver_type == SolverType.WEIGHTED_PARTIAL_MAXSAT:
        solver = solve_instance_weighted_partial_maxsat
    else:
        solver = solve_instance

    results: list[SolverResult] = []

    # Define número de workers (70% da CPU disponível)
    cpu = os.cpu_count() or 1
    max_workers = max(1, int(cpu * 0.7))

    with ProcessPoolExecutor(max_workers=max_workers) as executor:

        futures = set()
        instance_iter = iter(instances)

        # Submete as primeiras tarefas para ocupar os workers
        for _ in range(max_workers):
            try:
                inst = next(instance_iter)
                futures.add(executor.submit(solver, inst))
            except StopIteration:
                break

        done_count = 0
        total = len(instances)

        # Loop principal: processa tarefas conforme finalizam
        while futures:

            # Verifica interrupção externa (ex: botão "parar" na UI)
            if should_stop and should_stop():
                executor.shutdown(wait=False, cancel_futures=True)
                return results

            done, futures = wait(futures, return_when=FIRST_COMPLETED)

            for future in done:

                # Obtém resultado da instância concluída
                result = future.result()
                results.append(result)

                done_count += 1

                # Callback para processamento incremental de resultados
                if result_callback:
                    result_callback(result)

                # Callback de progresso (ex: atualização de UI)
                if progress_callback:
                    progress_callback(done_count, total)

                # Submete nova tarefa para manter o pool ocupado
                try:
                    inst = next(instance_iter)
                    futures.add(executor.submit(solver, inst))
                except StopIteration:
                    pass

    return results
