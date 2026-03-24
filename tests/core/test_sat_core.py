from core import generate_formulas_set, SATConfig, SolverType


def test_generate_formulas_set_basic():
    """
    GIVEN uma configuração válida de experimento
    WHEN as fórmulas são geradas
    THEN deve retornar resultados consistentes para cada combinação
    """
    config = SATConfig(
        num_formulas=2,
        num_global_variables=10,
        clauses_range=(5, 6),
        k_literals_per_clause=3,
        seed=42,
    )

    # WHEN
    results = generate_formulas_set(config)

    # THEN
    assert len(results) == 4  # (M=5,6) * 2 fórmulas
    for M, elapsed, satisf in results:
        assert isinstance(M, int)
        assert isinstance(elapsed, float)
        assert 0 <= satisf <= 1


def test_result_callback_called():
    """
    GIVEN uma função de callback de resultado
    WHEN o experimento é executado
    THEN o callback deve ser chamado para cada resultado
    """
    config = SATConfig(
        num_formulas=1,
        num_global_variables=5,
        clauses_range=(5, 5),
        k_literals_per_clause=2,
        seed=42,
    )

    collected = []

    def result_callback(res):
        collected.append(res)

    # WHEN
    generate_formulas_set(config, result_callback=result_callback)

    # THEN
    assert len(collected) == 1


def test_progress_callback_called():
    """
    GIVEN uma função de callback de progresso
    WHEN o experimento é executado
    THEN o progresso deve ser reportado corretamente
    """
    config = SATConfig(
        num_formulas=2,
        num_global_variables=5,
        clauses_range=(5, 5),
        k_literals_per_clause=2,
        seed=42,
    )

    calls = []

    def progress(done, total):
        calls.append((done, total))

    # WHEN
    generate_formulas_set(config, progress_callback=progress)

    # THEN
    assert len(calls) == 2
    assert calls[-1][0] == calls[-1][1]


def test_should_stop_interrupts():
    """
    GIVEN uma função que interrompe imediatamente a execução
    WHEN o experimento é iniciado
    THEN nenhum resultado deve ser gerado
    """
    config = SATConfig(
        num_formulas=10,
        num_global_variables=10,
        clauses_range=(5, 10),
        k_literals_per_clause=3,
        seed=42,
    )

    def should_stop():
        return True

    # WHEN
    results = generate_formulas_set(config, should_stop=should_stop)

    # THEN
    assert len(results) == 0


def test_solver_type_selection():
    """
    GIVEN um tipo de solver específico
    WHEN o experimento é executado
    THEN deve gerar resultados normalmente com o solver escolhido
    """
    config = SATConfig(
        num_formulas=1,
        num_global_variables=5,
        clauses_range=(5, 5),
        k_literals_per_clause=2,
        seed=42,
    )

    # WHEN
    result = generate_formulas_set(config, solver_type=SolverType.PARTIAL_MAXSAT)

    # THEN
    assert len(result) == 1


def test_same_seed_same_results_structure():
    """
    GIVEN uma seed fixa
    WHEN o experimento é executado múltiplas vezes
    THEN os resultados estruturais devem ser consistentes
    """
    config = SATConfig(
        num_formulas=1,
        num_global_variables=5,
        clauses_range=(5, 5),
        k_literals_per_clause=2,
        seed=42,
    )

    # WHEN
    r1 = generate_formulas_set(config)
    r2 = generate_formulas_set(config)

    # THEN
    assert len(r1) == len(r2)
    assert r1[0][0] == r2[0][0]  # M igual
    assert r1[0][2] == r2[0][2]  # satisf igual
