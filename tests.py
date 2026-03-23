import pytest

from sat_core import (
    SATConfig,
    generate_variable_names,
    generate_global_assignment,
    generate_clause,
    generate_k_sat_formula,
    evaluate_clause,
    evaluate_formula,
    format_literal,
    format_clause,
    format_formula,
)


def test_generate_variable_names():
    assert generate_variable_names(3) == ["A", "B", "C"]


def test_global_assignment_size():
    vars = ["A", "B", "C"]
    assignment = generate_global_assignment(vars)
    assert set(assignment.keys()) == set(vars)
    assert all(isinstance(v, bool) for v in assignment.values())


def test_generate_clause_respects_k():
    vars = ["A", "B", "C"]
    clause = generate_clause(vars, k=2, strict=True)
    assert 1 <= len(clause) <= 2
    for var, neg in clause:
        assert var in vars
        assert isinstance(neg, bool)


def test_evaluate_clause_true_case():
    clause = [("A", False), ("B", True)]  # A ∨ ¬B
    assignment = {"A": False, "B": False}  # ¬B é True
    assert evaluate_clause(clause, assignment) is True


def test_evaluate_formula_counts():
    formula = [[("A", False)], [("B", True)]]  # (A) ∧ (¬B)
    assignment = {"A": True, "B": False}
    sat, total, final = evaluate_formula(formula, assignment)
    assert sat == 2
    assert total == 2
    assert final is True


def test_formatting():
    clause = [("A", False), ("B", True)]  # A ∨ ¬B
    assert format_clause(clause) in ["(A ∨ ¬B)", "(¬B ∨ A)"]
    formula = [clause]
    fstr = format_formula(formula)
    assert "A" in fstr or "¬B" in fstr
