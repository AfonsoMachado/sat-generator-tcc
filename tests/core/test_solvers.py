from pysat.formula import WCNF

from core.solvers import (
    solve_instance,
    solve_instance_partial_maxsat,
    solve_instance_weighted_partial_maxsat,
    run_rc2,
)


def test_solve_instance_returns_valid_output():
    """
    GIVEN parâmetros válidos para uma instância SAT
    WHEN a instância é resolvida
    THEN deve retornar saída válida com tipos corretos e satisfazibilidade no intervalo
    """
    # WHEN
    result = solve_instance((10, 20, 3, 42))

    M, elapsed, satisf = result

    # THEN
    assert isinstance(M, int)
    assert isinstance(elapsed, float)
    assert 0 <= satisf <= 1


def test_partial_maxsat_valid_output():
    """
    GIVEN parâmetros válidos para partial Max-SAT
    WHEN a instância é resolvida
    THEN deve retornar M correto e satisfazibilidade válida
    """
    # WHEN
    result = solve_instance_partial_maxsat((10, 20, 3, 42))

    M, elapsed, satisf = result

    # THEN
    assert M == 20
    assert 0 <= satisf <= 1


def test_weighted_partial_maxsat_valid_output():
    """
    GIVEN parâmetros válidos para weighted partial Max-SAT
    WHEN a instância é resolvida
    THEN deve retornar M correto e satisfazibilidade válida
    """
    # WHEN
    result = solve_instance_weighted_partial_maxsat((10, 20, 3, 42))

    M, elapsed, satisf = result

    # THEN
    assert M == 20
    assert 0 <= satisf <= 1


def test_solve_instance_deterministic_with_seed():
    """
    GIVEN uma seed fixa
    WHEN a instância é resolvida múltiplas vezes
    THEN os resultados devem ser determinísticos
    """
    # WHEN
    m1, _, satisf1 = solve_instance((10, 20, 3, 42))
    m2, _, satisf2 = solve_instance((10, 20, 3, 42))

    # THEN
    assert m1 == m2 == 20
    assert satisf1 == satisf2


def test_run_rc2_basic():
    """
    GIVEN uma fórmula WCNF simples com peso positivo
    WHEN o solver RC2 é executado
    THEN deve retornar tempo válido e satisfazibilidade no intervalo
    """
    wcnf = WCNF()
    wcnf.append([1], weight=1)

    # WHEN
    elapsed, satisf = run_rc2(wcnf, 1)

    # THEN
    assert isinstance(elapsed, float)
    assert 0 <= satisf <= 1


def test_run_rc2_zero_weight():
    """
    GIVEN uma fórmula WCNF sem peso total
    WHEN o solver RC2 é executado
    THEN a satisfazibilidade deve ser zero
    """
    from pysat.formula import WCNF

    wcnf = WCNF()

    # WHEN
    elapsed, satisf = run_rc2(wcnf, 0)

    # THEN
    assert satisf == 0
