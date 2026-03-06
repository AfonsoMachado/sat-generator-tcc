import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from sat_core import SATConfig, generate_formulas_set

import threading
import time


def run_experiment(entries, frame_graph, label_timer, label_progress, progress_bar):
    running_flag = {"running": True}
    start_time = time.perf_counter()

    start_timer(label_timer, start_time, running_flag)

    def worker():

        try:

            num_formulas = int(entries["formulas"].get())
            num_vars = int(entries["vars"].get())
            k = int(entries["k"].get())
            min_clauses = int(entries["min_clauses"].get())
            max_clauses = int(entries["max_clauses"].get())
            seed = int(entries["seed"].get()) if entries["seed"].get() else None

            config = SATConfig(
                num_formulas=num_formulas,
                num_global_variables=num_vars,
                clauses_range=(min_clauses, max_clauses),
                k_literals_per_clause=k,
                seed=seed
            )

            def progress(done, total):

                elapsed = time.perf_counter() - start_time

                frame_graph.after(0, lambda: update_ui(
                    done,
                    total,
                    elapsed,
                    label_timer,
                    label_progress,
                    progress_bar
                ))

            data = generate_formulas_set(config, progress_callback=progress)

            running_flag["running"] = False

            frame_graph.after(0, lambda: draw_graph(frame_graph, data))

        except Exception as e:
            running_flag["running"] = False
            frame_graph.after(0, lambda: messagebox.showerror("Erro", str(e)))

    threading.Thread(target=worker, daemon=True).start()


def update_ui(done, total, elapsed, label_timer, label_progress, progress_bar):

    label_timer.config(text=f"Tempo de execução: {elapsed:.2f} s")

    label_progress.config(text=f"Progresso: {done} / {total} instâncias")

    progress_bar["value"] = done / total * 100


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

    label_timer = ttk.Label(root, text="Tempo de execução: 0.00 s")
    label_timer.pack()

    label_progress = ttk.Label(root, text="Progresso: 0")
    label_progress.pack()

    progress_bar = ttk.Progressbar(root, length=400)
    progress_bar.pack(pady=5)

    frame_graph = ttk.Frame(root)
    frame_graph.pack(fill="both", expand=True)

    ttk.Button(
        root,
        text="Executar Experimento",
        command=lambda: run_experiment(
            entries,
            frame_graph,
            label_timer,
            label_progress,
            progress_bar
        )
    ).pack(pady=10)

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

    fig, ax1 = plt.subplots(figsize=(7,4))

    # -------------------------------
    # Eixo esquerdo (satisfazibilidade)
    # -------------------------------

    ax1.set_xlabel("Número de cláusulas (M)")
    ax1.set_ylabel("Satisfazibilidade (%)", color="blue")

    ax1.plot(m_values, avg_sat, color="blue", label="Satisfazibilidade")

    ax1.tick_params(axis="y", labelcolor="blue")

    ax1.yaxis.set_major_formatter(ticker.PercentFormatter())

    # -------------------------------
    # Eixo direito (tempo)
    # -------------------------------

    ax2 = ax1.twinx()

    ax2.set_ylabel("Tempo médio (s)", color="orange")

    ax2.plot(m_values, avg_times, color="orange", label="Tempo")

    ax2.tick_params(axis="y", labelcolor="orange")

    # -------------------------------
    # Ajuste automático eixo X
    # -------------------------------

    xmin = min(m_values)
    xmax = max(m_values)

    padding_x = (xmax - xmin) * 0.05

    ax1.set_xlim(xmin - padding_x, xmax + padding_x)

    # -------------------------------
    # legenda no topo
    # -------------------------------

    lines = ax1.get_lines() + ax2.get_lines()
    labels = [l.get_label() for l in lines]

    fig.legend(
        lines,
        labels,
        loc="upper center",
        ncol=2
    )

    fig.tight_layout(rect=[0, 0, 1, 0.9])

    # -------------------------------
    # limpar gráfico anterior
    # -------------------------------

    for widget in frame.winfo_children():
        widget.destroy()

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)