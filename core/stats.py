from collections import defaultdict

import numpy as np

from core.models import ExperimentResult, AggregatedStats


def aggregate_results(data: list[ExperimentResult]) -> list[AggregatedStats]:
    """Agrupa os resultados por M e calcula médias e desvios padrão."""
    grouped: dict[int, list[ExperimentResult]] = defaultdict(list)

    for result in data:
        grouped[result.M].append(result)

    aggregated: list[AggregatedStats] = []

    for M in sorted(grouped):
        values = grouped[M]

        times = [item.elapsed for item in values]
        sats = [item.satisf for item in values]

        aggregated.append(
            AggregatedStats(
                M=M,
                avg_time=float(np.mean(times)),
                std_time=float(np.std(times)),
                avg_sat_percent=float(np.mean(sats) * 100),
                std_sat_percent=float(np.std(sats) * 100),
            )
        )

    return aggregated
