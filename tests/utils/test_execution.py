from utils.execution import ExecutionState


def test_execution_state_lifecycle():
    """
    GIVEN um estado recém inicializado
    WHEN o ciclo de execução é realizado (start → stop → finish)
    THEN os estados devem ser atualizados corretamente em cada etapa
    """
    state = ExecutionState()

    # THEN estado inicial
    assert not state.running
    assert not state.stop_requested

    # WHEN inicia execução
    state.start()
    # THEN
    assert state.running
    assert not state.stop_requested

    # WHEN solicita parada
    state.stop()
    # THEN
    assert not state.running
    assert state.stop_requested
    assert state.should_stop()

    # WHEN finaliza execução
    state.finish()
    # THEN
    assert not state.running
