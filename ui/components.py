import time
from tkinter import ttk

from utils.execution import ExecutionState


def clear_frame(frame: ttk.Frame) -> None:
    """
    Remove todos os widgets filhos de um frame.

    Essa função é utilizada principalmente para limpar áreas dinâmicas da interface,
    como gráficos ou componentes renderizados após a execução de um experimento,
    garantindo que não haja sobreposição de elementos em execuções subsequentes.
    """
    for widget in frame.winfo_children():
        widget.destroy()


def reset_ui(
        frame_graph: ttk.Frame,
        label_timer: ttk.Label,
        label_progress: ttk.Label,
        progress_bar: ttk.Progressbar,
) -> None:
    """
    Restaura a interface gráfica para o estado inicial antes da execução.

    Essa função deve ser chamada sempre que um novo experimento for iniciado,
    garantindo que os dados visuais da execução anterior sejam descartados.

    Ações realizadas:
    - Reinicia o texto do tempo de execução
    - Zera o indicador de progresso
    - Limpa o conteúdo do frame de gráficos
    """
    label_timer.config(text="Tempo de execução: 0.00 s")
    label_progress.config(text="Progresso: 0 / 0 instâncias")
    progress_bar["value"] = 0
    clear_frame(frame_graph)


def update_progress_ui(
        done: int,
        total: int,
        elapsed: float,
        label_timer: ttk.Label,
        label_progress: ttk.Label,
        progress_bar: ttk.Progressbar,
) -> None:
    """
    Atualiza os componentes visuais de progresso durante a execução.

    Essa função reflete o estado atual do processamento na interface,
    sendo chamada conforme novas instâncias são resolvidas.

    Parâmetros:
    - done: quantidade de instâncias já processadas
    - total: total de instâncias a serem processadas
    - elapsed: tempo total decorrido (em segundos)

    Atualizações realizadas:
    - Exibição do tempo de execução formatado
    - Atualização do progresso textual (done / total)
    - Atualização percentual da barra de progresso
    """
    label_timer.config(text=f"Tempo de execução: {elapsed:.2f} s")
    label_progress.config(text=f"Progresso: {done} / {total} instâncias")
    progress_bar["value"] = (done / total * 100) if total else 0


def show_loading(
        label_timer: ttk.Label,
        label_progress: ttk.Label,
        spinner: ttk.Progressbar,
) -> None:
    """
    Exibe o estado de carregamento inicial do sistema.

    Utilizado no momento anterior ao início do processamento efetivo,
    como na preparação do solver ou configuração dos dados.

    Ações realizadas:
    - Atualiza o label com mensagem de inicialização
    - Oculta temporariamente o progresso numérico
    - Exibe e inicia o spinner (indicador visual contínuo)
    """
    label_timer.config(text="Iniciando solver...")
    label_progress.config(text="")
    spinner.pack(pady=5)
    spinner.start(10)


def hide_loading(spinner: ttk.Progressbar) -> None:
    """
    Oculta o indicador de carregamento após a inicialização.

    Deve ser chamado assim que o processamento principal iniciar,
    substituindo o estado de loading pelos indicadores de progresso.
    """
    spinner.stop()
    spinner.pack_forget()


def start_timer(
        label: ttk.Label,
        start_time: float,
        state: ExecutionState,
) -> None:
    """
    Inicia a atualização contínua do tempo de execução na interface.

    Essa função implementa um loop não bloqueante utilizando o método `after`
    do Tkinter, garantindo que a interface permaneça responsiva durante
    a execução do experimento.

    O timer:
    - Calcula o tempo decorrido com base em `time.perf_counter`
    - Atualiza o label a cada 100ms
    - Interrompe automaticamente quando `state.running` for False

    Parâmetros:
    - label: componente visual onde o tempo será exibido
    - start_time: instante inicial da execução
    - state: objeto que controla o estado da execução (running/stop)
    """

    def update() -> None:
        if not state.running:
            return

        elapsed = time.perf_counter() - start_time
        label.config(text=f"Tempo de execução: {elapsed:.2f} s")

        # Agenda a próxima atualização sem bloquear a UI (loop assíncrono)
        label.after(100, update)  # type: ignore

    update()
