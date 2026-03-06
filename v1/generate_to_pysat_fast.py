import random

def generate_k_sat_formula_fast(num_vars: int, num_clauses: int, k: int):

    cnf = []

    for _ in range(num_clauses):

        clause = []
        used = set()

        while len(clause) < k:

            var = random.randrange(1, num_vars + 1)

            if var in used:
                continue

            used.add(var)

            if random.random() < 0.5:
                clause.append(var)
            else:
                clause.append(-var)

        cnf.append(clause)

    return cnf

def generate_k_sat_formula_fast_2(num_vars, num_clauses, k):

    cnf = []

    for _ in range(num_clauses):

        candidates = list(range(-num_vars, 0)) + list(range(1, num_vars + 1))

        clause = []

        for _ in range(k):

            idx = random.randrange(len(candidates))
            lit = candidates[idx]

            clause.append(lit)

            candidates.pop(idx)

        cnf.append(clause)

    return cnf