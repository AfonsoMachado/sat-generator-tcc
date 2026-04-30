import time
from dataclasses import dataclass


@dataclass
class SATConfig:
    """
    Estrutura de configuração base para experimentos SAT/Max-SAT.

    Essa classe centraliza os parâmetros necessários para geração das instâncias,
    sendo utilizada como configuração principal ao longo do pipeline experimental.

    Parâmetros:
    - num_formulas: quantidade de fórmulas geradas por valor de M (amostras por ponto)
    - num_global_variables: número total de variáveis disponíveis (N)
    - clauses_range: intervalo de cláusulas (M_min, M_max)
    - k_literals_per_clause: quantidade de literais por cláusula (k)
    - seed: valor opcional para controle de reprodutibilidade

    Observação:
    Quando a seed é definida, os experimentos tornam-se determinísticos.
    Caso contrário, diferentes execuções produzirão instâncias distintas.
    """

    num_formulas: int
    clauses_range: tuple[int, int]
    k_literals_per_clause: int
    num_global_variables: int = 0
    seed: int | None = None
    clauses_step: int = 1
    ratio: float | None = None


@dataclass(slots=True)
class ExperimentInputs:
    """
    Representa os parâmetros de entrada fornecidos pelo usuário para execução do experimento.

    Essa classe funciona como uma camada intermediária entre a interface (UI)
    e a configuração interna (`SATConfig`), além de fornecer utilitários auxiliares
    como geração de nomes de arquivos.

    Parâmetros:
    - num_formulas: número de fórmulas por amostra
    - num_vars: número de variáveis fixo (N); None quando modo razão está ativo
    - ratio: razão M/N fixa; None quando modo N fixo está ativo
    - k: literais por cláusula
    - min_clauses: valor mínimo de cláusulas (M inicial)
    - max_clauses: valor máximo de cláusulas (M final)
    - step_clauses: passo de incremento entre valores de M (default: 1)
    - seed: seed opcional para controle de aleatoriedade
    - solver_type: tipo de solver utilizado (ex: MaxSAT, Partial MaxSAT)
    """

    num_formulas: int
    num_vars: int | None
    ratio: float | None
    k: int
    min_clauses: int
    max_clauses: int
    step_clauses: int
    seed: int | None
    solver_type: str

    def to_sat_config(self) -> SATConfig:
        """
        Converte os parâmetros de entrada em um objeto `SATConfig`.

        Essa conversão padroniza os dados para consumo pelas camadas internas
        do sistema, desacoplando a entrada do usuário da lógica de execução.
        """
        return SATConfig(
            num_formulas=self.num_formulas,
            num_global_variables=self.num_vars or 0,
            clauses_range=(self.min_clauses, self.max_clauses),
            k_literals_per_clause=self.k,
            seed=self.seed,
            clauses_step=self.step_clauses,
            ratio=self.ratio,
        )

    def build_output_filename(self) -> str:
        """
        Gera um nome de arquivo padronizado para armazenamento dos resultados.

        O nome é composto por:
        - timestamp da execução (garante unicidade)
        - tipo de solver utilizado
        - parâmetros principais do experimento (N, k, número de fórmulas, intervalo de M)
        - seed utilizada (ou 'rand' caso não definida)

        Esse padrão facilita:
        - rastreabilidade dos experimentos
        - organização dos arquivos gerados
        - reprodutibilidade e comparação entre execuções

        Exemplo:
        20260323_153000_MaxSAT_N100_k3_f10_M100-500_seed42.csv
        """
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        seed_label = self.seed if self.seed is not None else "rand"

        n_part = (
            f"_N{self.num_vars}" if self.num_vars is not None
            else f"_ratio{self.ratio}"
        )
        return (
                f"{timestamp}_{self.solver_type}"
                + n_part
                + f"_k{self.k}"
                + f"_f{self.num_formulas}"
                + f"_M{self.min_clauses}-{self.max_clauses}"
                + (f"_step{self.step_clauses}" if self.step_clauses != 1 else "")
                + f"_seed{seed_label}.csv"
        )


@dataclass(slots=True)
class ExperimentResult:
    """
    Representa o resultado individual de uma instância resolvida.

    Cada objeto dessa classe corresponde a uma execução do solver
    para uma fórmula específica, permitindo posterior agregação estatística.

    Atributos:
    - M: número de cláusulas da instância
    - elapsed: tempo de execução do solver (em segundos)
    - satisf: valor de satisfazibilidade obtido (ex: proporção de cláusulas satisfeitas)
    """

    M: int
    elapsed: float
    satisf: float


@dataclass(slots=True)
class AggregatedStats:
    """
    Representa estatísticas agregadas para um determinado valor de M.

    Essa estrutura é utilizada na etapa de pós-processamento dos dados,
    consolidando múltiplas execuções em métricas médias e de dispersão,
    fundamentais para análise experimental e geração de gráficos.

    Atributos:
    - M: número de cláusulas considerado
    - avg_time: tempo médio de execução
    - std_time: desvio padrão do tempo de execução
    - avg_sat_percent: satisfazibilidade média (em percentual)
    - std_sat_percent: desvio padrão da satisfazibilidade (em percentual)

    Observação:
    Essas métricas permitem analisar:
    - crescimento do custo computacional
    - comportamento da transição de fase
    - variabilidade dos resultados entre diferentes instâncias
    """

    M: int
    avg_time: float
    std_time: float
    avg_sat_percent: float
    std_sat_percent: float
