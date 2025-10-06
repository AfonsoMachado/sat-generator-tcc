import random

def gerar_formulas_ksat(
        n, num_lits, min_clauses, max_clauses, min_lits, max_lits, k, seed
):
    random.seed(seed)

    # universo de literais
    literals = [f"X{i}" for i in range(1, num_lits + 1)]
    # valoração global fixa
    valuation = {lit: random.choice([True, False]) for lit in literals}

    for i in range(1, n + 1):
        # número de cláusulas e máximo de variáveis dessa fórmula
        num_clauses = random.randint(min_clauses, max_clauses)
        max_lits_formula = random.randint(min_lits, max_lits)

        # escolhe variáveis para essa fórmula
        chosen_lits = random.sample(literals, max_lits_formula)

        # constrói cláusulas (k literais cada)
        formula = []
        for _ in range(num_clauses):
            clause_lits = random.sample(chosen_lits, min(k, len(chosen_lits)))
            clause = []
            for lit in clause_lits:
                if random.choice([True, False]):
                    clause.append(f"¬{lit}")
                else:
                    clause.append(lit)
            formula.append(clause)

        # imprime fórmula
        fnc = " ∧ ".join(["(" + " ∨ ".join(clause) + ")" for clause in formula])
        print(f"\nFórmula {i}:")
        print("FNC:", fnc)
        print("Valoração usada:")
        for lit in chosen_lits:
            print(f"  {lit} = {valuation[lit]}")

        # avalia a fórmula
        formula_value = True
        for clause in formula:
            clause_value = False
            for literal in clause:
                if literal.startswith("¬"):
                    lit = literal[1:]
                    literal_value = not valuation[lit]
                else:
                    lit = literal
                    literal_value = valuation[lit]
                clause_value = clause_value or literal_value
            formula_value = formula_value and clause_value

        print(f"Valoração da fórmula: {formula_value}")

if __name__ == "__main__":
    n = 10
    num_lits = 102
    min_clauses = 2
    max_clauses = 5
    min_lits = 2
    max_lits = 5
    k = 3
    seed = 42

    gerar_formulas_ksat(
        n, num_lits, min_clauses, max_clauses, min_lits, max_lits, k, seed
    )
