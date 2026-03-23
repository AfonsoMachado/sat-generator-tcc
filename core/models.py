import time
from dataclasses import dataclass
from typing import Tuple


@dataclass
class SATConfig:
    """
    Estrutura de configuração dos experimentos SAT.
    """

    num_formulas: int
    num_global_variables: int
    clauses_range: Tuple[int, int]
    k_literals_per_clause: int
    seed: int | None = None


@dataclass(slots=True)
class ExperimentInputs:
    """Representa os parâmetros de entrada do experimento."""

    num_formulas: int
    num_vars: int
    k: int
    min_clauses: int
    max_clauses: int
    seed: int | None
    solver_type: str

    def to_sat_config(self) -> SATConfig:
        """Converte os dados de entrada para o objeto SATConfig."""
        return SATConfig(
            num_formulas=self.num_formulas,
            num_global_variables=self.num_vars,
            clauses_range=(self.min_clauses, self.max_clauses),
            k_literals_per_clause=self.k,
            seed=self.seed,
        )

    def build_output_filename(self) -> str:
        """Gera um nome padronizado para o arquivo CSV de saída."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        seed_label = self.seed if self.seed is not None else "rand"

        return (
            f"{timestamp}_{self.solver_type}"
            f"_N{self.num_vars}"
            f"_k{self.k}"
            f"_f{self.num_formulas}"
            f"_M{self.min_clauses}-{self.max_clauses}"
            f"_seed{seed_label}.csv"
        )


@dataclass(slots=True)
class ExperimentResult:
    """Representa o resultado de uma instância resolvida."""

    M: int
    elapsed: float
    satisf: float


@dataclass(slots=True)
class AggregatedStats:
    """Representa as estatísticas agregadas por quantidade de cláusulas."""

    M: int
    avg_time: float
    std_time: float
    avg_sat_percent: float
    std_sat_percent: float
