import csv
from pathlib import Path

from core.models import ExperimentResult


class CSVResultWriter:
    """Responsável por persistir os resultados do experimento em CSV."""

    HEADER = ["solver", "M", "tempo", "satisf"]

    def __init__(self, filepath: Path) -> None:
        self.filepath = filepath
        self._file = open(filepath, "w", newline="", encoding="utf-8")
        self._writer = csv.writer(self._file)
        self._writer.writerow(self.HEADER)

    def write(self, solver_type: str, result: ExperimentResult) -> None:
        """Escreve um resultado no arquivo CSV."""
        self._writer.writerow([solver_type, result.M, result.elapsed, result.satisf])
        self._file.flush()

    def close(self) -> None:
        """Fecha o arquivo de saída."""
        if not self._file.closed:
            self._file.close()

    def __enter__(self) -> "CSVResultWriter":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def load_results_from_csv(filepath: str) -> list[ExperimentResult]:
    """Carrega resultados de um arquivo CSV."""
    results: list[ExperimentResult] = []

    with open(filepath, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader, None)  # pula cabeçalho

        for row in reader:
            if len(row) != 4:
                continue

            _, M, elapsed, satisf = row
            results.append(
                ExperimentResult(
                    M=int(M),
                    elapsed=float(elapsed),
                    satisf=float(satisf),
                )
            )

    return results
