import time
from tkinter import ttk

from utils.execution import ExecutionState


def clear_frame(frame: ttk.Frame) -> None:
    """Remove todos os widgets filhos de um frame."""
    for widget in frame.winfo_children():
        widget.destroy()


def reset_ui(
        frame_graph: ttk.Frame,
        label_timer: ttk.Label,
        label_progress: ttk.Label,
        progress_bar: ttk.Progressbar,
) -> None:
    """Restaura a interface para o estado inicial antes da execução."""
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
    """Atualiza os componentes visuais de progresso."""
    label_timer.config(text=f"Tempo de execução: {elapsed:.2f} s")
    label_progress.config(text=f"Progresso: {done} / {total} instâncias")
    progress_bar["value"] = (done / total * 100) if total else 0


def show_loading(
        label_timer: ttk.Label,
        label_progress: ttk.Label,
        spinner: ttk.Progressbar,
) -> None:
    """Exibe o indicador visual de inicialização do solver."""
    label_timer.config(text="Iniciando solver...")
    label_progress.config(text="")
    spinner.pack(pady=5)
    spinner.start(10)


def hide_loading(spinner: ttk.Progressbar) -> None:
    """Oculta o indicador de carregamento."""
    spinner.stop()
    spinner.pack_forget()


def start_timer(
        label: ttk.Label,
        start_time: float,
        state: ExecutionState,
) -> None:
    """Atualiza continuamente o cronômetro enquanto a execução estiver ativa."""

    def update() -> None:
        if not state.running:
            return

        elapsed = time.perf_counter() - start_time
        label.config(text=f"Tempo de execução: {elapsed:.2f} s")
        label.after(100, update)  # type: ignore

    update()
