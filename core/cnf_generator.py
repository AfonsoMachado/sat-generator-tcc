import random


def generate_random_cnf(num_vars: int, num_clauses: int, k: int) -> list[list[int]]:
    """
    Gera uma fórmula CNF aleatória k-SAT.

    A implementação segue os requisitos do algoritmo descrito no texto.
    """

    # Verificação de parâmetros
    if k > num_vars:
        raise ValueError("k não pode ser maior que o número de variáveis distintas")

    cnf = []

    for _ in range(num_clauses):
        # escolhe variáveis sem repetição
        variables = random.sample(range(1, num_vars + 1), k)

        # atribui sinal aleatório
        clause = [v if random.choice([True, False]) else -v for v in variables]

        cnf.append(clause)

    return cnf
