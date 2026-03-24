from core import ExperimentResult, SolverType
from infra import CSVResultWriter, load_results_from_csv


def test_csv_write_and_read(tmp_path):
    """
    GIVEN um arquivo CSV e um resultado de experimento
    WHEN o resultado é escrito e posteriormente lido do arquivo
    THEN os dados devem ser recuperados corretamente
    """
    filepath = tmp_path / "test.csv"

    writer = CSVResultWriter(filepath)
    writer.write(SolverType.MAXSAT.value, ExperimentResult(10, 1.0, 0.9))
    writer.close()

    # WHEN
    data = load_results_from_csv(filepath)  # type: ignore

    # THEN
    assert len(data) == 1
    assert data[0].M == 10
