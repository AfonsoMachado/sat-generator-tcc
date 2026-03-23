class ExecutionState:
    """
    Controla o estado global de execução do experimento.

    Essa classe é responsável por gerenciar o ciclo de vida da execução,
    permitindo:
    - Indicar se o experimento está em andamento
    - Solicitar interrupção de forma controlada
    - Sincronizar o estado entre UI, threads e processamento paralelo

    Estados principais:
    - running: indica se o experimento está ativo
    - stop_requested: sinaliza que foi solicitada a interrupção

    Observação:
    Esse controle é essencial para permitir que a execução paralela
    seja interrompida de forma segura, sem corromper dados ou travar a interface.
    """

    def __init__(self) -> None:
        """
        Inicializa o estado como inativo e sem solicitação de parada.
        """
        self.running = False
        self.stop_requested = False

    def start(self) -> None:
        """
        Inicia o estado de execução.

        Deve ser chamado antes de iniciar o experimento, garantindo que:
        - O sistema reconheça que está em execução
        - Não exista sinal de parada pendente
        """
        self.running = True
        self.stop_requested = False

    def stop(self) -> None:
        """
        Solicita a interrupção do experimento.

        Não interrompe imediatamente a execução, mas sinaliza para que
        os loops de processamento (ex: execução paralela) encerrem
        de forma controlada.

        Esse método é tipicamente acionado por interações da UI (botão "Parar").
        """
        self.running = False
        self.stop_requested = True

    def finish(self) -> None:
        """
        Finaliza o estado de execução.

        Deve ser chamado ao término natural do experimento, garantindo
        que o sistema não permaneça marcado como "em execução".
        """
        self.running = False

    def should_stop(self) -> bool:
        """
        Indica se foi solicitada a interrupção do experimento.

        Esse método é utilizado pelos loops de execução para verificar
        periodicamente se devem encerrar o processamento.

        Retorno:
        - True: interrupção solicitada
        - False: execução continua normalmente
        """
        return self.stop_requested


# Instância global compartilhada entre UI e execução
execution_state = ExecutionState()


def stop_experiment() -> None:
    """
    Função utilitária para solicitar a parada do experimento.

    Atua como interface simplificada para a UI (ex: botão "Parar"),
    delegando a chamada para o estado global de execução.
    """
    execution_state.stop()
