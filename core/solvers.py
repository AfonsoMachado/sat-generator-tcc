import random
import time

from pysat.examples.rc2 import RC2
from pysat.formula import WCNF

from core.cnf_generator import generate_random_cnf

SolverArgs = tuple[int, int, int, int]
SolverResult = tuple[int, float, float]


def solve_instance(args: SolverArgs) -> SolverResult:
    """
    Resolve uma instância do problema Max-SAT clássico.

    Nesse modelo, todas as cláusulas são tratadas como soft constraints
    com peso uniforme (1), ou seja, o objetivo do solver é maximizar
    o número total de cláusulas satisfeitas.

    Fluxo:
    - Geração de uma fórmula CNF aleatória
    - Conversão para WCNF com pesos unitários
    - Execução do solver RC2
    - Cálculo da satisfazibilidade

    Parâmetros (args):
    - N: número de variáveis
    - M: número de cláusulas
    - k: literais por cláusula
    - seed: controle de aleatoriedade

    Retorno:
    - M: número de cláusulas
    - elapsed: tempo de execução (s)
    - satisf: proporção de cláusulas satisfeitas (0 a 1)
    """
    N, M, k, seed = args

    random.seed(seed)
    cnf = generate_random_cnf(N, M, k)

    wcnf = WCNF()

    # Todas as cláusulas são soft com peso 1
    wcnf.extend(cnf, weights=[1] * len(cnf))

    total_soft_weight = len(cnf)
    elapsed, satisf = run_rc2(wcnf, total_soft_weight)

    return M, elapsed, satisf


def solve_instance_partial_maxsat(args: SolverArgs) -> SolverResult:
    """
    Resolve uma instância do problema Partial Max-SAT.

    Nesse modelo, as cláusulas são divididas em:
    - Hard: devem ser obrigatoriamente satisfeitas
    - Soft: podem ser violadas, sendo maximizadas pelo solver

    Estratégia adotada:
    - Primeira metade das cláusulas → hard
    - Segunda metade → soft com peso 1

    Essa divisão permite simular cenários com restrições obrigatórias
    e objetivos otimizáveis simultaneamente.

    Retorno:
    - M: número de cláusulas
    - elapsed: tempo de execução (s)
    - satisf: proporção de peso soft satisfeito
    """
    N, M, k, seed = args

    random.seed(seed)
    cnf = generate_random_cnf(N, M, k)

    # Divide as cláusulas em hard e soft
    split = M >> 1

    wcnf = WCNF()

    # Cláusulas obrigatórias
    for clause in cnf[:split]:
        wcnf.append(clause)

    # Cláusulas otimizáveis (peso uniforme)
    for clause in cnf[split:]:
        wcnf.append(clause, weight=1)

    total_soft_weight = len(cnf[split:])
    elapsed, satisf = run_rc2(wcnf, total_soft_weight)

    return M, elapsed, satisf


def solve_instance_weighted_partial_maxsat(args: SolverArgs) -> SolverResult:
    """
    Resolve uma instância do problema Weighted Partial Max-SAT.

    Extensão do Partial Max-SAT onde:
    - Cláusulas hard continuam obrigatórias
    - Cláusulas soft recebem pesos distintos

    Estratégia adotada:
    - Primeira metade → hard
    - Segunda metade → soft com pesos aleatórios entre 1 e 10

    Isso permite modelar cenários onde algumas cláusulas são mais
    importantes que outras na função objetivo.

    Retorno:
    - M: número de cláusulas
    - elapsed: tempo de execução (s)
    - satisf: proporção do peso total satisfeito
    """
    N, M, k, seed = args

    random.seed(seed)
    cnf = generate_random_cnf(N, M, k)

    split = M >> 1

    wcnf = WCNF()
    total_soft_weight = 0

    # Cláusulas hard
    for clause in cnf[:split]:
        wcnf.append(clause)

    # Cláusulas soft com pesos variados
    for clause in cnf[split:]:
        weight = random.randint(1, 10)
        total_soft_weight += weight
        wcnf.append(clause, weight=weight)

    elapsed, satisf = run_rc2(wcnf, total_soft_weight)

    return M, elapsed, satisf


def run_rc2(wcnf: WCNF, total_soft_weight: int) -> tuple[float, float]:
    """
    Executa o solver RC2 sobre uma fórmula WCNF e calcula métricas de desempenho.

    O RC2 (Max-SAT solver baseado em relaxação por cardinalidade) retorna
    o custo mínimo, que corresponde ao peso total das cláusulas soft não satisfeitas.

    Cálculo da satisfazibilidade:
    satisf = (peso_total - custo) / peso_total

    Ou seja, representa a proporção de peso efetivamente satisfeita.

    Parâmetros:
    - wcnf: fórmula em formato Weighted CNF
    - total_soft_weight: soma total dos pesos das cláusulas soft

    Retorno:
    - elapsed: tempo de execução (s)
    - satisf: taxa de satisfazibilidade (0 a 1)
    """
    start = time.perf_counter()

    with RC2(wcnf) as rc2:
        rc2.compute()
        cost = rc2.cost  # peso não satisfeito

    elapsed = time.perf_counter() - start

    # Evita divisão por zero caso não existam cláusulas soft
    satisf = (total_soft_weight - cost) / total_soft_weight if total_soft_weight else 0

    return elapsed, satisf
