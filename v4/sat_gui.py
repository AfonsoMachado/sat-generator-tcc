import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import filedialog
import csv

from sat_core import SATConfig, generate_formulas_set

import threading
import time
import os

output_dir = "resultados"
os.makedirs(output_dir, exist_ok=True)

from v4.solver_type import SolverType

stop_flag = {"stop": False}
running_flag = {"running": False}

def run_experiment(entries, frame_graph, label_timer, label_progress, progress_bar, solver_var, run_button, loading_label, loading_spinner):
    running_flag["running"] = True
    stop_flag["stop"] = False
    run_button.config(state="disabled")
    frame_graph.after(0, lambda: show_loading(label_timer, label_progress, loading_spinner))

    reset_ui(frame_graph, label_timer, label_progress, progress_bar)

    partial_results = []
    start_time = {"value": None}

    def worker():
        try:

            num_formulas = int(entries["formulas"].get())
            num_vars = int(entries["vars"].get())
            k = int(entries["k"].get())
            min_clauses = int(entries["min_clauses"].get())
            max_clauses = int(entries["max_clauses"].get())
            seed = int(entries["seed"].get()) if entries["seed"].get() else None
            solver_type = solver_var.get()

            import time
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{solver_type}_N{num_vars}_k{k}_f{num_formulas}_M{min_clauses}-{max_clauses}_seed{seed or 'rand'}.csv"
            filepath = os.path.join(output_dir, filename)
            file = open(filepath, "w", newline="")
            writer = csv.writer(file)
            writer.writerow(["solver", "M", "tempo", "satisf"])

            def collect_result(res):
                partial_results.append(res)

                M, elapsed, satisf = res

                writer.writerow([solver_type, M, elapsed, satisf])
                file.flush()

            config = SATConfig(
                num_formulas=num_formulas,
                num_global_variables=num_vars,
                clauses_range=(min_clauses, max_clauses),
                k_literals_per_clause=k,
                seed=seed
            )

            def progress(done, total):

                if stop_flag["stop"]:
                    return False

                # inicia o timer apenas quando a primeira instância terminar
                if start_time["value"] is None:
                    start_time["value"] = time.perf_counter()
                    frame_graph.after(0, lambda: hide_loading(loading_spinner))
                    frame_graph.after(0, lambda: start_timer(label_timer, start_time["value"], running_flag))

                elapsed = time.perf_counter() - start_time["value"]

                frame_graph.after(0, lambda: update_ui(
                    done,
                    total,
                    elapsed,
                    label_timer,
                    label_progress,
                    progress_bar
                ))

                return True

            data = generate_formulas_set(
                config,
                progress_callback=progress,
                result_callback=collect_result,
                solver_type=solver_type,
                should_stop=should_stop
            )

            file.close()
            running_flag["running"] = False

            if partial_results:
                frame_graph.after(0, lambda: draw_graph(frame_graph, partial_results))

            frame_graph.after(0, lambda: run_button.config(state="normal"))

        except RuntimeError as e:
            if str(e) == "STOP_REQUESTED":
                running_flag["running"] = False
                frame_graph.after(0, lambda: draw_graph(frame_graph, partial_results))
            else:
                frame_graph.after(0, lambda err=e: messagebox.showerror("Erro", str(err)))
            frame_graph.after(0, lambda: run_button.config(state="normal"))

    threading.Thread(target=worker, daemon=True).start()

def stop_experiment():
    stop_flag["stop"] = True
    running_flag["running"] = False

def should_stop():
    return stop_flag["stop"]

def reset_ui(frame_graph, label_timer, label_progress, progress_bar):

    # resetar labels
    label_timer.config(text="Tempo de execução: 0.00 s")
    label_progress.config(text="Progresso: 0 / 0 instâncias")

    # resetar barra
    progress_bar["value"] = 0

    # limpar gráfico antigo
    for widget in frame_graph.winfo_children():
        widget.destroy()

def update_ui(done, total, elapsed, label_timer, label_progress, progress_bar):

    label_timer.config(text=f"Tempo de execução: {elapsed:.2f} s")

    label_progress.config(text=f"Progresso: {done} / {total} instâncias")

    progress_bar["value"] = done / total * 100

def show_loading(label_timer, label_progress, spinner):

    label_timer.config(text="Iniciando solver...")
    label_progress.config(text="")

    spinner.pack(pady=5)
    spinner.start(10)

def hide_loading(spinner):

    spinner.stop()
    spinner.pack_forget()

def gui_runner():

    root = tk.Tk()
    root.title("Experimento Max-SAT RC2")

    frame_inputs = ttk.Frame(root, padding=10)
    frame_inputs.pack(fill="x")

    labels = [
        ("Número de fórmulas", "formulas"),
        ("Nº variáveis", "vars"),
        ("k", "k"),
        ("Mín cláusulas", "min_clauses"),
        ("Máx cláusulas", "max_clauses"),
        ("Seed (opcional)", "seed"),
    ]

    entries = {}

    for i, (label, key) in enumerate(labels):

        ttk.Label(frame_inputs, text=label).grid(row=i, column=0, sticky="w")

        entry = ttk.Entry(frame_inputs)
        entry.grid(row=i, column=1)

        entries[key] = entry

    ttk.Label(frame_inputs, text="Tipo de solver").grid(row=len(labels), column=0, sticky="w")

    solver_var = tk.StringVar(value=SolverType.MAXSAT.value)

    solver_selector = ttk.Combobox(
        frame_inputs,
        textvariable=solver_var,
        state="readonly",
        values=[solver.value for solver in SolverType]
    )

    solver_selector.grid(row=len(labels), column=1)

    loading_frame = ttk.Frame(root)
    loading_frame.pack()

    loading_label = ttk.Label(loading_frame, text="")

    loading_spinner = ttk.Progressbar(
        loading_frame,
        mode="indeterminate",
        length=120
    )

    label_timer = ttk.Label(root, text="Tempo de execução: 0.00 s")
    label_timer.pack()

    label_progress = ttk.Label(root, text="Progresso: 0")
    label_progress.pack()

    progress_bar = ttk.Progressbar(root, length=400)
    progress_bar.pack(pady=5)

    graph_container = ttk.Frame(root)
    graph_container.pack(fill="both", expand=True)

    canvas = tk.Canvas(graph_container)
    scrollbar = ttk.Scrollbar(graph_container, orient="vertical", command=canvas.yview)

    frame_graph = ttk.Frame(canvas)

    frame_graph.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=frame_graph, anchor="nw")

    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    canvas.bind_all(
        "<MouseWheel>",
        lambda event: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    )

    button_frame = ttk.Frame(root)
    button_frame.pack(pady=10)

    ttk.Button(
        button_frame,
        text="Carregar dados",
        command=lambda: load_data_and_plot(frame_graph)
    ).pack(side="left", padx=5)

    run_button = ttk.Button(
        button_frame,
        text="Executar Experimento"
    )

    run_button.pack(side="left", padx=5)

    run_button.config(
        command=lambda: run_experiment(
            entries,
            frame_graph,
            label_timer,
            label_progress,
            progress_bar,
            solver_var,
            run_button,
            loading_label,
            loading_spinner,
        )
    )

    ttk.Button(
        button_frame,
        text="Parar",
        command=stop_experiment
    ).pack(side="left", padx=5)

    return root

def start_timer(label, start_time, running_flag):

    def update():

        if not running_flag["running"]:
            return

        elapsed = time.perf_counter() - start_time

        label.config(text=f"Tempo de execução: {elapsed:.2f} s")

        label.after(100, update)

    update()

def draw_graph(frame, data):

    from collections import defaultdict
    import matplotlib.ticker as ticker

    groups = defaultdict(list)

    for M, time_spent, sat in data:
        groups[M].append((time_spent, sat))

    m_values = []
    avg_times = []
    avg_sat = []

    for M in sorted(groups):

        values = groups[M]

        avg_time = sum(v[0] for v in values) / len(values)
        avg_s = sum(v[1] for v in values) / len(values)

        m_values.append(M)
        avg_times.append(avg_time)
        avg_sat.append(avg_s * 100)

    # limpar gráficos antigos
    for widget in frame.winfo_children():
        widget.destroy()

    # ==================================================
    # GRÁFICO 1 — COMBINADO (tempo + satisfazibilidade)
    # ==================================================

    fig1, ax1 = plt.subplots(figsize=(7,4))

    ax1.set_xlabel("Número de cláusulas (M)")
    ax1.set_ylabel("Satisfazibilidade (%)", color="blue")

    ax1.plot(m_values, avg_sat, color="blue", label="Satisfazibilidade")
    ax1.tick_params(axis="y", labelcolor="blue")
    ax1.yaxis.set_major_formatter(ticker.PercentFormatter())

    ax2 = ax1.twinx()

    ax2.set_ylabel("Tempo médio (s)", color="orange")
    ax2.plot(m_values, avg_times, color="orange", label="Tempo")
    ax2.tick_params(axis="y", labelcolor="orange")

    xmin = min(m_values)
    xmax = max(m_values)
    padding_x = (xmax - xmin) * 0.05

    ax1.set_xlim(xmin - padding_x, xmax + padding_x)

    lines = ax1.get_lines() + ax2.get_lines()
    labels = [l.get_label() for l in lines]

    fig1.legend(lines, labels, loc="upper center", ncol=2)
    fig1.tight_layout(rect=[0,0,1,0.9])

    canvas1 = FigureCanvasTkAgg(fig1, master=frame)
    canvas1.draw()
    canvas1.get_tk_widget().pack(fill="both", expand=True, pady=10)

    # ==================================================
    # GRÁFICO 2 — APENAS SATISFAZIBILIDADE
    # ==================================================

    fig2, ax = plt.subplots(figsize=(7, 4))

    ax.set_title("Satisfazibilidade")
    ax.set_xlabel("Número de cláusulas (M)")
    ax.set_ylabel("Satisfazibilidade (%)", color="blue")

    ax.plot(
        m_values,
        avg_sat,
        color="blue",
        marker="o",
        markersize=3,
        label="Satisfazibilidade"
    )

    ax.tick_params(axis="y", labelcolor="blue")
    ax.yaxis.set_major_formatter(ticker.PercentFormatter())

    ax.set_xlim(xmin - padding_x, xmax + padding_x)

    ax.legend()

    fig2.tight_layout()

    canvas2 = FigureCanvasTkAgg(fig2, master=frame)
    canvas2.draw()
    canvas2.get_tk_widget().pack(fill="both", expand=True, pady=10)

    # ==================================================
    # GRÁFICO 3 — APENAS TEMPO
    # ==================================================

    fig3, ax = plt.subplots(figsize=(7, 4))

    ax.set_title("Tempo de resolução")
    ax.set_xlabel("Número de cláusulas (M)")
    ax.set_ylabel("Tempo médio (s)", color="orange")

    ax.plot(
        m_values,
        avg_times,
        color="orange",
        marker="o",
        markersize=3,
        label="Tempo médio"
    )

    ax.tick_params(axis="y", labelcolor="orange")

    ax.set_xlim(xmin - padding_x, xmax + padding_x)

    ax.legend()

    fig3.tight_layout()

    canvas3 = FigureCanvasTkAgg(fig3, master=frame)
    canvas3.draw()
    canvas3.get_tk_widget().pack(fill="both", expand=True, pady=10)

def load_data_and_plot(frame_graph):
    filepath = filedialog.askopenfilename(
        title="Selecionar arquivo de resultados",
        filetypes=[("Arquivos CSV", "*.csv")]
    )

    if not filepath:
        return

    data = []

    try:
        with open(filepath, "r") as f:
            reader = csv.reader(f)
            next(reader)  # pula header

            for row in reader:
                if len(row) != 4:
                    continue

                _, M, elapsed, satisf = row

                data.append((
                    int(M),
                    float(elapsed),
                    float(satisf)
                ))

        if data:
            draw_graph(frame_graph, data)

    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao carregar arquivo:\n{e}")