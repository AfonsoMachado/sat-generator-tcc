from collections import defaultdict

import numpy as np

from core.models import ExperimentResult, AggregatedStats


def aggregate_results(data: list[ExperimentResult]) -> list[AggregatedStats]:
    """
    Agrupa os resultados das execuções por quantidade de cláusulas (M)
    e calcula estatísticas agregadas para cada grupo.

    Essa função representa a etapa de pós-processamento dos experimentos,
    sendo responsável por consolidar múltiplas execuções (amostras) em
    métricas estatísticas utilizadas na análise e visualização dos resultados.

    Para cada valor de M, são calculadas:
    - Média do tempo de execução
    - Desvio padrão do tempo de execução
    - Média da satisfazibilidade (em percentual)
    - Desvio padrão da satisfazibilidade (em percentual)

    Parâmetros:
    - data: lista de resultados individuais ('ExperimentResult'),
      onde cada elemento representa uma instância resolvida

    Retorno:
    - Lista de 'AggregatedStats', contendo métricas consolidadas por valor de M,
      ordenadas crescentemente.

    Observação:
    - O agrupamento por M permite analisar o comportamento do solver
      conforme o aumento do número de cláusulas.
    - O uso de média e desvio padrão possibilita avaliar tanto a tendência
      quanto a variabilidade dos resultados, fundamentais para identificação
      de fenômenos como transição de fase.
    """

    # Agrupa os resultados por número de cláusulas (M)
    grouped: dict[int, list[ExperimentResult]] = defaultdict(list)

    for result in data:
        grouped[result.M].append(result)

    aggregated: list[AggregatedStats] = []

    # Processa cada grupo ordenado por M
    for M in sorted(grouped):
        values = grouped[M]

        # Extrai listas de tempos e satisfazibilidade
        times = [item.elapsed for item in values]
        sats = [item.satisf for item in values]

        # Calcula métricas estatísticas
        ddof = 1 if len(values) > 1 else 0
        aggregated.append(
            AggregatedStats(
                M=M,
                avg_time=float(np.mean(times)),
                std_time=float(np.std(times, ddof=ddof)),
                avg_sat_percent=float(np.mean(sats) * 100),
                std_sat_percent=float(np.std(sats, ddof=ddof) * 100),
            )
        )

    return aggregated
