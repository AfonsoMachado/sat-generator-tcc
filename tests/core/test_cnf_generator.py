import pytest

from core.cnf_generator import generate_random_cnf


def test_generate_random_cnf_structure():
    """
    GIVEN parâmetros válidos para geração de CNF
    WHEN a função é executada
    THEN deve gerar exatamente M cláusulas com k literais cada
    """
    # WHEN
    cnf = generate_random_cnf(10, 5, 3)

    # THEN
    assert len(cnf) == 5
    assert all(len(clause) == 3 for clause in cnf)


def test_no_repeated_variables_in_clause():
    """
    GIVEN uma CNF gerada aleatoriamente
    WHEN analisamos cada cláusula
    THEN não deve haver variáveis repetidas na mesma cláusula
    """
    # WHEN
    cnf = generate_random_cnf(10, 20, 3)

    for clause in cnf:
        # THEN
        abs_vars = [abs(v) for v in clause]
        assert len(abs_vars) == len(set(abs_vars))


def test_k_greater_than_vars_raises():
    """
    GIVEN k maior que o número de variáveis disponíveis
    WHEN a função é chamada
    THEN deve lançar um erro de validação
    """
    # WHEN
    with pytest.raises(ValueError):
        # THEN
        generate_random_cnf(2, 5, 3)
