import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from core import ExperimentInputs, ExperimentResult, generate_formulas_set, SolverType
from infra import CSVResultWriter, load_results_from_csv
from ui.components import (
    show_loading,
    reset_ui,
    hide_loading,
    start_timer,
    update_progress_ui,
)
from utils import stop_experiment, execution_state
from visualization import draw_graphs

OUTPUT_DIR = Path("./resultados")
OUTPUT_DIR.mkdir(exist_ok=True)


def parse_inputs(entries: dict[str, ttk.Entry], solver_var: tk.StringVar) -> ExperimentInputs:
    """
    Lê e valida os parâmetros informados pelo usuário na interface gráfica.

    Essa função extrai os valores dos campos de entrada (Entry widgets),
    realiza conversões de tipo e constrói um objeto `ExperimentInputs`,
    que será utilizado na execução do experimento.

    Tratamento especial:
    - A seed é opcional: caso não informada, será considerada como None,
      permitindo geração aleatória posterior.

    Parâmetros:
    - entries: dicionário contendo os campos da interface
    - solver_var: variável associada ao seletor de tipo de solver

    Retorno:
    - Objeto `ExperimentInputs` com os parâmetros do experimento
    """
    seed_raw = entries["seed"].get().strip()

    step_raw = entries["step_clauses"].get().strip()

    return ExperimentInputs(
        num_formulas=int(entries["formulas"].get()),
        num_vars=int(entries["vars"].get()),
        k=int(entries["k"].get()),
        min_clauses=int(entries["min_clauses"].get()),
        max_clauses=int(entries["max_clauses"].get()),
        step_clauses=int(step_raw) if step_raw else 1,
        seed=int(seed_raw) if seed_raw else None,
        solver_type=solver_var.get(),
    )


def run_experiment(
        entries: dict[str, ttk.Entry],
        frame_graph: ttk.Frame,
        label_timer: ttk.Label,
        label_progress: ttk.Label,
        progress_bar: ttk.Progressbar,
        solver_var: tk.StringVar,
        run_button: ttk.Button,
        loading_spinner: ttk.Progressbar,
        markers_var: tk.BooleanVar,
) -> None:
    """
    Executa o experimento em uma thread separada, mantendo a interface responsiva.

    Essa função coordena todo o fluxo de execução do experimento, incluindo:
    - Leitura dos parâmetros da interface
    - Inicialização do estado de execução
    - Persistência incremental dos resultados em CSV
    - Atualização da interface (tempo, progresso, gráficos)
    - Suporte a interrupção controlada

    Estratégia de execução:
    - O processamento ocorre em uma thread paralela (worker)
    - A interface é atualizada via `frame.after` (thread-safe no Tkinter)
    - Resultados são armazenados incrementalmente em memória e em disco

    Componentes principais:
    - `collect_result`: callback para tratamento de cada resultado individual
    - `progress`: callback de progresso (UI + controle de tempo)
    - `generate_formulas_set`: motor de execução paralela

    Tratamento de erros:
    - Interrupção controlada (STOP_REQUESTED)
    - Exibição de erros via messagebox
    - Garantia de liberação de recursos (arquivo CSV, spinner, botão)

    Observações:
    - O botão de execução é desabilitado durante o processamento
    - O gráfico é atualizado ao final ou em caso de parada antecipada
    - O spinner é exibido até o início efetivo do processamento
    """
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
                show_markers = markers_var.get()
                frame_graph.after(0, lambda m=show_markers: draw_graphs(frame_graph, partial_results, m))  # type: ignore

            frame_graph.after(0, lambda: run_button.config(state="normal"))  # type: ignore

        except RuntimeError as exc:
            execution_state.finish()

            if str(exc) == "STOP_REQUESTED":
                show_markers = markers_var.get()
                frame_graph.after(0, lambda m=show_markers: draw_graphs(frame_graph, partial_results, m))  # type: ignore
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

def load_data_and_plot(frame_graph: ttk.Frame, markers_var: tk.BooleanVar) -> None:
    """
    Permite carregar resultados previamente salvos e reconstruir os gráficos.

    Essa funcionalidade evita a necessidade de reexecutar experimentos,
    permitindo análise posterior a partir de arquivos CSV.

    Fluxo:
    - Abre um seletor de arquivos
    - Lê os dados via `load_results_from_csv`
    - Renderiza os gráficos com base nos dados carregados

    Tratamento:
    - Arquivo vazio ou inválido → aviso ao usuário
    - Erros de leitura → mensagem de erro

    Parâmetros:
    - frame_graph: área onde os gráficos serão desenhados
    """
    filepath = filedialog.askopenfilename(
        title="Selecionar arquivo de resultados",
        filetypes=[("Arquivos CSV", "*.csv")],
    )

    if not filepath:
        return

    try:
        data = load_results_from_csv(filepath)
        if data:
            draw_graphs(frame_graph, data, markers_var.get())
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
    """
    Cria um par label + campo de entrada (Entry) em uma linha do layout.

    Essa função auxilia na construção padronizada da interface,
    garantindo consistência visual e redução de código repetido.

    Parâmetros:
    - parent: container onde o componente será inserido
    - row: posição na grid
    - label_text: texto descritivo do campo

    Retorno:
    - Widget Entry criado
    """
    ttk.Label(parent, text=label_text).grid(row=row, column=0, sticky="w")
    entry = ttk.Entry(parent)
    entry.grid(row=row, column=1)
    return entry


def build_inputs_section(root: tk.Tk) -> tuple[ttk.Frame, dict[str, ttk.Entry], tk.StringVar, tk.BooleanVar]:
    """
    Constrói a seção de entrada de parâmetros do experimento.

    Essa área permite ao usuário configurar:
    - Número de fórmulas
    - Número de variáveis (N)
    - Literais por cláusula (k)
    - Intervalo de cláusulas (M)
    - Seed opcional
    - Tipo de solver

    Componentes:
    - Campos de entrada (Entry)
    - Combobox para seleção do solver

    Retorno:
    - Frame da seção
    - Dicionário de entries
    - Variável associada ao solver selecionado
    """
    frame_inputs = ttk.Frame(root, padding=10)
    frame_inputs.pack(fill="x")

    fields = [
        ("Número de fórmulas", "formulas"),
        ("Nº variáveis (N)", "vars"),
        ("Literais por cláusula (k)", "k"),
        ("Mín cláusulas (M)", "min_clauses"),
        ("Máx cláusulas (M)", "max_clauses"),
        ("Passo de M", "step_clauses"),
        ("Seed (opcional)", "seed"),
    ]

    entries: dict[str, ttk.Entry] = {}

    for row, (label_text, key) in enumerate(fields):
        entries[key] = create_labeled_entry(frame_inputs, row, label_text)

    entries["step_clauses"].insert(0, "1")

    ttk.Label(frame_inputs, text="Tipo de solver").grid(row=len(fields), column=0, sticky="w")

    solver_var = tk.StringVar(value=SolverType.MAXSAT.value)
    solver_selector = ttk.Combobox(
        frame_inputs,
        textvariable=solver_var,
        state="readonly",
        values=[solver.value for solver in SolverType],
    )
    solver_selector.grid(row=len(fields), column=1)

    markers_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(
        frame_inputs,
        text="Marcadores nos pontos",
        variable=markers_var,
    ).grid(row=len(fields) + 1, column=0, columnspan=2, sticky="w")

    return frame_inputs, entries, solver_var, markers_var


def build_status_section(root: tk.Tk) -> tuple[ttk.Progressbar, ttk.Label, ttk.Label, ttk.Progressbar]:
    """
    Constrói a seção de status da execução.

    Essa área fornece feedback visual ao usuário durante o experimento,
    incluindo:
    - Tempo de execução (cronômetro)
    - Progresso textual (instâncias concluídas)
    - Barra de progresso percentual
    - Spinner de carregamento inicial

    Retorno:
    - Spinner de loading
    - Label de tempo
    - Label de progresso
    - Barra de progresso
    """
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
    """
    Constrói a área de visualização dos gráficos com suporte a rolagem.

    Estrutura:
    - Canvas (container principal)
    - Frame interno (onde os gráficos são renderizados)
    - Scroll vertical

    Funcionalidades:
    - Scroll automático conforme crescimento do conteúdo
    - Suporte a scroll com mouse
    - Layout expansível

    Retorno:
    - Frame interno onde os gráficos serão desenhados
    """
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
        markers_var: tk.BooleanVar,
) -> None:
    """
    Constrói a seção de botões de controle da aplicação.

    Botões disponíveis:
    - "Carregar dados": abre CSV e renderiza gráficos
    - "Executar Experimento": inicia execução completa
    - "Parar": interrompe execução em andamento

    Observações:
    - O botão de execução é desabilitado durante o processamento
    - O botão "Parar" utiliza controle via estado global (`execution_state`)
    """
    button_frame = ttk.Frame(root)
    button_frame.pack(pady=10)

    ttk.Button(
        button_frame,
        text="Carregar dados",
        command=lambda: load_data_and_plot(frame_graph, markers_var),
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
            markers_var=markers_var,
        )
    )

    ttk.Button(
        button_frame,
        text="Parar",
        command=stop_experiment,
    ).pack(side="left", padx=5)


def gui_runner() -> tk.Tk:
    """
    Inicializa e configura a aplicação gráfica completa.

    Essa função centraliza a montagem de todos os componentes da interface:
    - Seção de inputs
    - Seção de status
    - Área de gráficos
    - Botões de controle

    Também define:
    - Título da janela
    - Estrutura principal da aplicação

    Retorno:
    - Instância configurada do Tkinter (`Tk`), pronta para execução
    """
    root = tk.Tk()
    root.title("Experimento Max-SAT RC2")

    _, entries, solver_var, markers_var = build_inputs_section(root)
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
        markers_var=markers_var,
    )

    return root
