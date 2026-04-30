import random


def generate_random_cnf(num_vars: int, num_clauses: int, k: int) -> list[list[int]]:
    """
    Gera uma fórmula CNF aleatória do tipo k-SAT.

    Cada fórmula é composta por 'num_clauses' cláusulas, onde cada cláusula
    contém exatamente 'k' literais distintos. As variáveis são escolhidas
    aleatoriamente sem repetição dentro de cada cláusula, garantindo que
    não ocorram redundâncias como (x ∨ x).

    O sinal de cada literal (positivo ou negativo) também é definido de forma
    aleatória, permitindo a geração de instâncias variadas e estatisticamente
    relevantes para experimentos com SAT/Max-SAT.

    Parâmetros:
    - num_vars: número total de variáveis disponíveis (1 até num_vars)
    - num_clauses: quantidade de cláusulas da fórmula (M)
    - k: número de literais por cláusula

    Regras garantidas:
    - Não há repetição de variáveis numa mesma cláusula
    - Cada cláusula possui exatamente k literais
    - Literais podem ser positivos (x) ou negativos (¬x), definidos aleatoriamente

    Retorno:
    - Lista de cláusulas, onde cada cláusula é representada por uma lista de inteiros
      (ex: [[1, −3, 4], [-2, 5, −1], ...])
    """

    # Validação: não é possível selecionar k variáveis distintas se k > num_vars
    if k > num_vars:
        raise ValueError("k não pode ser maior que o número de variáveis distintas")

    cnf = []

    for _ in range(num_clauses):
        # Seleciona k variáveis distintas sem repetição
        variables = random.sample(range(1, num_vars + 1), k)

        # Atribui aleatoriamente o sinal de cada literal (positivo ou negativo)
        clause = [v if random.choice([True, False]) else -v for v in variables]

        # Adiciona a cláusula à fórmula CNF
        cnf.append(clause)

    return cnf
