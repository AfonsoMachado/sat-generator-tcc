import csv
import threading
import time
import tkinter as tk
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from sat_core import SATConfig, generate_formulas_set
from solver_type import SolverType

OUTPUT_DIR = Path("resultados")
OUTPUT_DIR.mkdir(exist_ok=True)


# ============================================================
# MODELOS
# ============================================================

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


class ExecutionState:
    """Controla o estado global da execução do experimento."""

    def __init__(self) -> None:
        self.running = False
        self.stop_requested = False

    def start(self) -> None:
        self.running = True
        self.stop_requested = False

    def stop(self) -> None:
        self.running = False
        self.stop_requested = True

    def finish(self) -> None:
        self.running = False

    def should_stop(self) -> bool:
        return self.stop_requested


execution_state = ExecutionState()


# ============================================================
# CSV
# ============================================================

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


# ============================================================
# ESTATÍSTICAS
# ============================================================

def aggregate_results(data: list[ExperimentResult]) -> list[AggregatedStats]:
    """Agrupa os resultados por M e calcula médias e desvios padrão."""
    grouped: dict[int, list[ExperimentResult]] = defaultdict(list)

    for result in data:
        grouped[result.M].append(result)

    aggregated: list[AggregatedStats] = []

    for M in sorted(grouped):
        values = grouped[M]

        times = [item.elapsed for item in values]
        sats = [item.satisf for item in values]

        aggregated.append(
            AggregatedStats(
                M=M,
                avg_time=float(np.mean(times)),
                std_time=float(np.std(times)),
                avg_sat_percent=float(np.mean(sats) * 100),
                std_sat_percent=float(np.std(sats) * 100),
            )
        )

    return aggregated


# ============================================================
# UI HELPERS
# ============================================================

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


def stop_experiment() -> None:
    """Solicita a interrupção do experimento em execução."""
    execution_state.stop()


# ============================================================
# INPUTS
# ============================================================

def parse_inputs(entries: dict[str, ttk.Entry], solver_var: tk.StringVar) -> ExperimentInputs:
    """Lê e valida os campos da interface."""
    seed_raw = entries["seed"].get().strip()

    return ExperimentInputs(
        num_formulas=int(entries["formulas"].get()),
        num_vars=int(entries["vars"].get()),
        k=int(entries["k"].get()),
        min_clauses=int(entries["min_clauses"].get()),
        max_clauses=int(entries["max_clauses"].get()),
        seed=int(seed_raw) if seed_raw else None,
        solver_type=solver_var.get(),
    )


# ============================================================
# GRÁFICOS
# ============================================================

def render_plot(frame: ttk.Frame, fig: plt.Figure) -> None:
    """Renderiza uma figura matplotlib dentro do frame informado."""
    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True, pady=10)


def extract_plot_series(stats: list[AggregatedStats]) -> tuple[
    list[int], list[float], list[float], list[float], list[float]]:
    """Extrai listas prontas para plotagem a partir das estatísticas agregadas."""
    m_values = [item.M for item in stats]
    avg_times = [item.avg_time for item in stats]
    std_times = [item.std_time for item in stats]
    avg_sat = [item.avg_sat_percent for item in stats]
    std_sat = [item.std_sat_percent for item in stats]
    return m_values, avg_times, std_times, avg_sat, std_sat


def calculate_x_limits(m_values: list[int]) -> tuple[float, float]:
    """Calcula os limites do eixo X com padding."""
    x_min = min(m_values)
    x_max = max(m_values)
    padding_x = (x_max - x_min) * 0.05 if x_max > x_min else 1
    return x_min - padding_x, x_max + padding_x


def create_combined_chart(frame: ttk.Frame, stats: list[AggregatedStats]) -> None:
    """Cria o gráfico combinado de satisfazibilidade e tempo médio."""
    m_values, avg_times, _, avg_sat, _ = extract_plot_series(stats)
    x_left, x_right = calculate_x_limits(m_values)

    fig, ax1 = plt.subplots(figsize=(7, 4))

    ax1.set_xlabel("Número de cláusulas (M)")
    ax1.set_ylabel("Satisfazibilidade (%)", color="blue")
    ax1.plot(m_values, avg_sat, color="blue", label="Satisfazibilidade")
    ax1.tick_params(axis="y", labelcolor="blue")
    ax1.yaxis.set_major_formatter(ticker.PercentFormatter())
    ax1.set_xlim(x_left, x_right)

    ax2 = ax1.twinx()
    ax2.set_ylabel("Tempo médio (s)", color="orange")
    ax2.plot(m_values, avg_times, color="orange", label="Tempo")
    ax2.tick_params(axis="y", labelcolor="orange")

    lines = ax1.get_lines() + ax2.get_lines()
    labels = [str(line.get_label()) for line in lines]

    fig.legend(lines, labels, loc="upper center", ncol=2)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.9))

    render_plot(frame, fig)


def create_satisfiability_chart(frame: ttk.Frame, stats: list[AggregatedStats]) -> None:
    """Cria o gráfico apenas de satisfazibilidade média."""
    m_values, _, _, avg_sat, _ = extract_plot_series(stats)
    x_left, x_right = calculate_x_limits(m_values)

    fig, ax = plt.subplots(figsize=(7, 4))

    ax.set_title("Satisfazibilidade")
    ax.set_xlabel("Número de cláusulas (M)")
    ax.set_ylabel("Satisfazibilidade (%)", color="blue")
    ax.plot(
        m_values,
        avg_sat,
        color="blue",
        marker="o",
        markersize=3,
        label="Satisfazibilidade",
    )
    ax.tick_params(axis="y", labelcolor="blue")
    ax.yaxis.set_major_formatter(ticker.PercentFormatter())
    ax.set_xlim(x_left, x_right)
    ax.legend()

    fig.tight_layout()
    render_plot(frame, fig)


def create_time_chart(frame: ttk.Frame, stats: list[AggregatedStats]) -> None:
    """Cria o gráfico apenas de tempo médio."""
    m_values, avg_times, _, _, _ = extract_plot_series(stats)
    x_left, x_right = calculate_x_limits(m_values)

    fig, ax = plt.subplots(figsize=(7, 4))

    ax.set_title("Tempo de resolução")
    ax.set_xlabel("Número de cláusulas (M)")
    ax.set_ylabel("Tempo médio (s)", color="orange")
    ax.plot(
        m_values,
        avg_times,
        color="orange",
        marker="o",
        markersize=3,
        label="Tempo médio",
    )
    ax.tick_params(axis="y", labelcolor="orange")
    ax.set_xlim(x_left, x_right)
    ax.legend()

    fig.tight_layout()
    render_plot(frame, fig)


def create_time_std_chart(frame: ttk.Frame, stats: list[AggregatedStats]) -> None:
    """Cria o gráfico de tempo médio com desvio padrão."""
    m_values, avg_times, std_times, _, _ = extract_plot_series(stats)
    x_left, x_right = calculate_x_limits(m_values)

    fig, ax = plt.subplots(figsize=(7, 4))

    ax.set_title("Tempo médio com desvio padrão")
    ax.set_xlabel("Número de cláusulas (M)")
    ax.set_ylabel("Tempo médio (s)", color="orange")
    ax.errorbar(
        m_values,
        avg_times,
        yerr=std_times,
        fmt="-o",
        markersize=3,
        color="orange",
        ecolor="gray",
        elinewidth=1,
        capsize=3,
        label="Tempo médio ± desvio padrão",
    )
    ax.tick_params(axis="y", labelcolor="orange")
    ax.set_xlim(x_left, x_right)
    ax.legend()

    fig.tight_layout()
    render_plot(frame, fig)


def draw_graphs(frame: ttk.Frame, data: list[ExperimentResult]) -> None:
    """Limpa o container e desenha todos os gráficos a partir dos resultados."""
    if not data:
        return

    clear_frame(frame)
    stats = aggregate_results(data)

    create_combined_chart(frame, stats)
    create_satisfiability_chart(frame, stats)
    create_time_chart(frame, stats)
    create_time_std_chart(frame, stats)


# ============================================================
# EXECUÇÃO DO EXPERIMENTO
# ============================================================

def run_experiment(
        entries: dict[str, ttk.Entry],
        frame_graph: ttk.Frame,
        label_timer: ttk.Label,
        label_progress: ttk.Label,
        progress_bar: ttk.Progressbar,
        solver_var: tk.StringVar,
        run_button: ttk.Button,
        loading_spinner: ttk.Progressbar,
) -> None:
    """Executa o experimento em thread separada para não travar a UI."""
    execution_state.start()
    run_button.config(state="disabled")

    frame_graph.after(0, show_loading, label_timer, label_progress, loading_spinner)
    reset_ui(frame_graph, label_timer, label_progress, progress_bar)

    partial_results: list[ExperimentResult] = []
    timer_started_at: dict[str, float | None] = {"value": None}

    def worker() -> None:
        writer: CSVResultWriter | None = None

        try:
            experiment_inputs = parse_inputs(entries, solver_var)
            filepath = OUTPUT_DIR / experiment_inputs.build_output_filename()

            writer = CSVResultWriter(filepath)

            def collect_result(raw_result: tuple[int, float, float]) -> None:
                result = ExperimentResult(
                    M=raw_result[0],
                    elapsed=raw_result[1],
                    satisf=raw_result[2],
                )
                partial_results.append(result)
                writer.write(experiment_inputs.solver_type, result)

            def progress(done: int, total: int) -> bool:
                if execution_state.should_stop():
                    return False

                if timer_started_at["value"] is None:
                    timer_started_at["value"] = time.perf_counter()
                    frame_graph.after(0, hide_loading, loading_spinner)
                    frame_graph.after(
                        0,
                        start_timer,
                        label_timer,
                        timer_started_at["value"],
                        execution_state,
                    )

                elapsed = time.perf_counter() - timer_started_at["value"]  # type: ignore[operator]

                frame_graph.after(
                    0,
                    lambda: update_progress_ui(
                        done,
                        total,
                        elapsed,
                        label_timer,
                        label_progress,
                        progress_bar,
                    ),
                )  # type: ignore

                return True

            generate_formulas_set(
                experiment_inputs.to_sat_config(),
                progress_callback=progress,
                result_callback=collect_result,
                solver_type=experiment_inputs.solver_type,
                should_stop=execution_state.should_stop,
            )

            execution_state.finish()

            if partial_results:
                frame_graph.after(0, lambda: draw_graphs(frame_graph, partial_results))  # type: ignore

            frame_graph.after(0, lambda: run_button.config(state="normal"))  # type: ignore

        except RuntimeError as exc:
            execution_state.finish()

            if str(exc) == "STOP_REQUESTED":
                frame_graph.after(0, lambda: draw_graphs(frame_graph, partial_results))  # type: ignore
            else:
                frame_graph.after(0, lambda err=exc: messagebox.showerror("Erro", str(err)))  # type: ignore

            frame_graph.after(0, lambda: run_button.config(state="normal"))  # type: ignore

        except Exception as exc:
            execution_state.finish()
            frame_graph.after(
                0,
                lambda err=exc: messagebox.showerror("Erro", f"Falha ao executar experimento:\n{err}"),
            )  # type: ignore
            frame_graph.after(0, lambda: run_button.config(state="normal"))  # type: ignore

        finally:
            if writer is not None:
                writer.close()
            frame_graph.after(0, lambda: hide_loading(loading_spinner))  # type: ignore

    threading.Thread(target=worker, daemon=True).start()


# ============================================================
# CARREGAMENTO DE DADOS
# ============================================================

def load_data_and_plot(frame_graph: ttk.Frame) -> None:
    """Abre um CSV salvo anteriormente e recria os gráficos."""
    filepath = filedialog.askopenfilename(
        title="Selecionar arquivo de resultados",
        filetypes=[("Arquivos CSV", "*.csv")],
    )

    if not filepath:
        return

    try:
        data = load_results_from_csv(filepath)
        if data:
            draw_graphs(frame_graph, data)
        else:
            messagebox.showwarning("Aviso", "Nenhum dado válido foi encontrado no arquivo.")
    except Exception as exc:
        messagebox.showerror("Erro", f"Falha ao carregar arquivo:\n{exc}")


# ============================================================
# CONSTRUÇÃO DA INTERFACE
# ============================================================

def create_labeled_entry(
        parent: ttk.Frame,
        row: int,
        label_text: str,
) -> ttk.Entry:
    """Cria um label com entry associado em uma linha do grid."""
    ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky="w")
    entry = ttk.Entry(parent)
    entry.grid(row=row, column=1)
    return entry


def build_inputs_section(root: tk.Tk) -> tuple[ttk.Frame, dict[str, ttk.Entry], tk.StringVar]:
    """Monta a seção de parâmetros de entrada."""
    frame_inputs = ttk.Frame(root, padding=10)
    frame_inputs.pack(fill="x")

    fields = [
        ("Número de fórmulas", "formulas"),
        ("Nº variáveis", "vars"),
        ("k", "k"),
        ("Mín cláusulas", "min_clauses"),
        ("Máx cláusulas", "max_clauses"),
        ("Seed (opcional)", "seed"),
    ]

    entries: dict[str, ttk.Entry] = {}

    for row, (label_text, key) in enumerate(fields):
        entries[key] = create_labeled_entry(frame_inputs, row, label_text)

    ttk.Label(frame_inputs, text="Tipo de solver").grid(row=len(fields), column=0, sticky="w")

    solver_var = tk.StringVar(value=SolverType.MAXSAT.value)
    solver_selector = ttk.Combobox(
        frame_inputs,
        textvariable=solver_var,
        state="readonly",
        values=[solver.value for solver in SolverType],
    )
    solver_selector.grid(row=len(fields), column=1)

    return frame_inputs, entries, solver_var


def build_status_section(root: tk.Tk) -> tuple[ttk.Progressbar, ttk.Label, ttk.Label, ttk.Progressbar]:
    """Monta a seção de status e carregamento."""
    loading_frame = ttk.Frame(root)
    loading_frame.pack()

    loading_label = ttk.Label(loading_frame, text="")
    loading_label.pack_forget()  # mantido apenas se quiser usar depois

    loading_spinner = ttk.Progressbar(
        loading_frame,
        mode="indeterminate",
        length=120,
    )

    label_timer = ttk.Label(root, text="Tempo de execução: 0.00 s")
    label_timer.pack()

    label_progress = ttk.Label(root, text="Progresso: 0 / 0 instâncias")
    label_progress.pack()

    progress_bar = ttk.Progressbar(root, length=400)
    progress_bar.pack(pady=5)

    return loading_spinner, label_timer, label_progress, progress_bar


def build_graph_section(root: tk.Tk) -> ttk.Frame:
    """Monta a área com scroll onde os gráficos serão renderizados."""
    graph_container = ttk.Frame(root)
    graph_container.pack(fill="both", expand=True)

    canvas = tk.Canvas(graph_container)
    scrollbar = ttk.Scrollbar(graph_container, orient="vertical", command=canvas.yview)

    frame_graph = ttk.Frame(canvas)

    frame_graph.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
    )

    canvas.create_window((0, 0), window=frame_graph, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    canvas.bind_all(
        "<MouseWheel>",
        lambda event: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"),
    )

    return frame_graph


def build_buttons_section(
        root: tk.Tk,
        entries: dict[str, ttk.Entry],
        frame_graph: ttk.Frame,
        label_timer: ttk.Label,
        label_progress: ttk.Label,
        progress_bar: ttk.Progressbar,
        solver_var: tk.StringVar,
        loading_spinner: ttk.Progressbar,
) -> None:
    """Monta a seção de botões de ação."""
    button_frame = ttk.Frame(root)
    button_frame.pack(pady=10)

    ttk.Button(
        button_frame,
        text="Carregar dados",
        command=lambda: load_data_and_plot(frame_graph),
    ).pack(side="left", padx=5)

    run_button = ttk.Button(button_frame, text="Executar Experimento")
    run_button.pack(side="left", padx=5)

    run_button.config(
        command=lambda: run_experiment(
            entries=entries,
            frame_graph=frame_graph,
            label_timer=label_timer,
            label_progress=label_progress,
            progress_bar=progress_bar,
            solver_var=solver_var,
            run_button=run_button,
            loading_spinner=loading_spinner,
        )
    )

    ttk.Button(
        button_frame,
        text="Parar",
        command=stop_experiment,
    ).pack(side="left", padx=5)


def gui_runner() -> tk.Tk:
    """Cria e retorna a aplicação Tkinter configurada."""
    root = tk.Tk()
    root.title("Experimento Max-SAT RC2")

    _, entries, solver_var = build_inputs_section(root)
    loading_spinner, label_timer, label_progress, progress_bar = build_status_section(root)
    frame_graph = build_graph_section(root)

    build_buttons_section(
        root=root,
        entries=entries,
        frame_graph=frame_graph,
        label_timer=label_timer,
        label_progress=label_progress,
        progress_bar=progress_bar,
        solver_var=solver_var,
        loading_spinner=loading_spinner,
    )

    return root
