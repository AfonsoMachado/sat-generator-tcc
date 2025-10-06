import random


def gerar_formulas_ksat(
    n, num_vars, min_clauses, max_clauses, min_vars, max_vars, k, seed
):
    random.seed(seed)

    # universo de literais
    literals = [f"X{i}" for i in range(1, num_vars + 1)]
    # valoração global fixa
    valuation = {lit: random.choice([True, False]) for lit in literals}

    for i in range(1, n + 1):
        # número de cláusulas e máximo de variáveis dessa fórmula
        num_clauses = random.randint(min_clauses, max_clauses)
        max_vars_formula = random.randint(min_vars, max_vars)

        # escolhe variáveis para essa fórmula
        chosen_vars = random.sample(literals, max_vars_formula)

        # constrói cláusulas (k literais cada)
        formula = []
        for _ in range(num_clauses):
            clause_vars = random.sample(chosen_vars, min(k, len(chosen_vars)))
            clause = []
            for var in clause_vars:
                if random.choice([True, False]):
                    clause.append(f"¬{var}")
                else:
                    clause.append(var)
            formula.append(clause)

        # imprime fórmula
        fnc = " ∧ ".join(["(" + " ∨ ".join(clause) + ")" for clause in formula])
        print(f"\nFórmula {i}:")
        print("FNC:", fnc)
        print("Valoração usada:")
        for var in chosen_vars:
            print(f"  {var} = {valuation[var]}")


if __name__ == "__main__":
    n = 10
    num_vars = 102
    min_clauses = 2
    max_clauses = 5
    min_vars = 2
    max_vars = 5
    k = 3
    seed = 42

    gerar_formulas_ksat(
        n, num_vars, min_clauses, max_clauses, min_vars, max_vars, k, seed
    )
