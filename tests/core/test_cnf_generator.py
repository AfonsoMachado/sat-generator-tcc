import pytest

from core.cnf_generator import generate_random_cnf


def test_generate_random_cnf_structure():
    cnf = generate_random_cnf(10, 5, 3)

    assert len(cnf) == 5
    assert all(len(clause) == 3 for clause in cnf)


def test_no_repeated_variables_in_clause():
    cnf = generate_random_cnf(10, 20, 3)

    for clause in cnf:
        abs_vars = [abs(v) for v in clause]
        assert len(abs_vars) == len(set(abs_vars))


def test_k_greater_than_vars_raises():
    with pytest.raises(ValueError):
        generate_random_cnf(2, 5, 3)
