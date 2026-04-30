import csv
from pathlib import Path

from core.models import ExperimentResult


class CSVResultWriter:
    """
    Responsável por persistir os resultados dos experimentos em formato CSV.

    Essa classe encapsula a escrita incremental dos resultados, permitindo
    que cada instância resolvida seja imediatamente registrada em disco.
    Isso é especialmente importante para experimentos longos, evitando perda
    de dados em caso de interrupções.

    Características:
    - Escrita linha a linha (streaming)
    - Flush imediato após cada registro (garante persistência)
    - Suporte a uso com context manager ('with')

    Estrutura do arquivo:
    - solver: tipo de solver utilizado
    - M: número de cláusulas
    - tempo: tempo de execução (segundos)
    - satisf: satisfazibilidade (0 a 1)
    """

    HEADER = ["solver", "M", "tempo", "satisf"]

    def __init__(self, filepath: Path) -> None:
        """
        Inicializa o writer e cria o arquivo CSV.

        Parâmetros:
        - filepath: caminho completo do arquivo de saída

        Abertura do arquivo:
        - Modo escrita ("w") → sobrescreve arquivos existentes
        - newline="" → evita linhas em branco extras no CSV
        - encoding="utf-8" → garante compatibilidade de caracteres
        """
        self.filepath = filepath
        self._file = open(filepath, "w", newline="", encoding="utf-8")
        self._writer = csv.writer(self._file)

        # Escreve o cabeçalho do arquivo
        self._writer.writerow(self.HEADER)

    def write(self, solver_type: str, result: ExperimentResult) -> None:
        """
        Escreve um resultado individual no arquivo CSV.

        Essa função é chamada tipicamente a cada instância resolvida,
        permitindo persistência incremental dos dados.

        Parâmetros:
        - solver_type: identificação do solver utilizado
        - result: objeto contendo M, tempo e satisfazibilidade

        Observação:
        O uso de 'flush()' garante que os dados sejam gravados imediatamente
        no disco, reduzindo risco de perda em execuções longas.
        """
        self._writer.writerow([solver_type, result.M, result.elapsed, result.satisf])
        self._file.flush()

    def close(self) -> None:
        """
        Fecha o arquivo CSV caso ainda esteja aberto.

        Deve ser chamado ao final do experimento para liberar recursos
        do sistema operacional e garantir integridade do arquivo.
        """
        if not self._file.closed:
            self._file.close()

    def __enter__(self) -> "CSVResultWriter":
        """
        Permite o uso da classe como context manager.

        Exemplo:
        with CSVResultWriter(path) as writer:
            writer.write(...)
        """
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """
        Garante o fechamento do arquivo ao sair do contexto,
        independentemente de sucesso ou exceção.
        """
        self.close()


def load_results_from_csv(filepath: str | Path) -> list[ExperimentResult]:
    """
    Carrega resultados previamente salvos em um arquivo CSV.

    Essa função permite reutilizar dados de experimentos já executados,
    evitando reprocessamento e possibilitando análise posterior
    (ex: geração de gráficos, cálculo de estatísticas).

    Parâmetros:
    - filepath: caminho do arquivo CSV a ser lido

    Retorno:
    - Lista de 'ExperimentResult', reconstruindo os dados originais

    Regras de leitura:
    - Ignora o cabeçalho automaticamente
    - Valida o número de colunas por linha
    - Desconsidera linhas inválidas ou mal formatadas

    Observação:
    O campo 'solver' é ignorado na reconstrução, pois o modelo atual
    ('ExperimentResult') não armazena essa informação.
    """

    results: list[ExperimentResult] = []

    with open(filepath, "r", encoding="utf-8") as file:
        reader = csv.reader(file)

        # Pula a primeira linha (cabeçalho)
        next(reader, None)

        for row in reader:
            # Garante formato esperado (solver, M, tempo, satisf)
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
