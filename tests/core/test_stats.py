from core import ExperimentResult, aggregate_results


def test_aggregate_results():
    """
    GIVEN múltiplos resultados com mesmo número de cláusulas
    WHEN os resultados são agregados
    THEN deve calcular corretamente a média do tempo
    """
    data = [
        ExperimentResult(10, 1.0, 1.0),
        ExperimentResult(10, 2.0, 0.5),
    ]

    # WHEN
    stats = aggregate_results(data)

    # THEN
    assert len(stats) == 1
    assert stats[0].avg_time == 1.5
