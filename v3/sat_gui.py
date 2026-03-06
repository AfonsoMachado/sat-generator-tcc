import tkinter as tk
from tkinter import ttk, messagebox

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from sat_core import SATConfig, generate_formulas_set
import threading
import time


def run_experiment(entries, frame_graph, label_timer):

    start_timer(label_timer)

    def worker():

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

        data = generate_formulas_set(config)

        frame_graph.after(0, lambda: draw_graph2(frame_graph, data))

    threading.Thread(target=worker, daemon=True).start()

def start_timer(label):

    start = time.perf_counter()

    def update():
        elapsed = time.perf_counter() - start
        label.config(text=f"Tempo de execução: {elapsed:.2f} s")
        label.after(100, update)

    update()

def draw_graph(frame, data):

    from collections import defaultdict

    groups = defaultdict(list)

    for M, time_spent, sat in data:
        groups[M].append((time_spent, sat))

    M_vals = []
    avg_times = []
    avg_sat = []

    for M in sorted(groups):

        values = groups[M]

        avg_time = sum(v[0] for v in values) / len(values)
        avg_s = sum(v[1] for v in values) / len(values)

        M_vals.append(M)
        avg_times.append(avg_time)
        avg_sat.append(avg_s * 100)

    fig, ax1 = plt.subplots(figsize=(6,4))

    ax1.set_xlabel("Número de cláusulas (M)")
    ax1.set_ylabel("Satisfazibilidade (%)", color="blue")
    ax1.plot(M_vals, avg_sat, color="blue")

    ax2 = ax1.twinx()
    ax2.set_ylabel("Tempo médio (s)", color="orange")
    ax2.plot(M_vals, avg_times, color="orange")

    for widget in frame.winfo_children():
        widget.destroy()

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)


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

    ttk.Button(
        root,
        text="Executar Experimento",
        command=lambda: run_experiment(entries, frame_graph, label_timer)
    ).pack(pady=10)

    label_timer = ttk.Label(root, text="Tempo de execução: 0.00 s")
    label_timer.pack()

    frame_graph = ttk.Frame(root)
    frame_graph.pack(fill="both", expand=True)

    return root


def draw_graph2(frame, data):

    from collections import defaultdict
    import matplotlib.ticker as ticker

    groups = defaultdict(list)

    for M, time_spent, sat in data:
        groups[M].append((time_spent, sat))

    M_values = []
    avg_times = []
    avg_sat = []

    for M in sorted(groups.keys()):

        values = groups[M]

        avg_time = sum(v[0] for v in values) / len(values)
        avg_s = sum(v[1] for v in values) / len(values)

        M_values.append(M)
        avg_times.append(avg_time * 1000)   # escala visual do tempo
        avg_sat.append(avg_s * 100)

    fig, ax = plt.subplots(figsize=(7,4))

    ax.plot(M_values, avg_sat, color="blue", label="Porcentagem")
    ax.plot(M_values, avg_times, color="orange", label="Tempo")

    ax.set_xlabel("Número de cláusulas (M)")
    ax.set_ylabel("Porcentagem")

    # -------- eixo X automático --------
    xmin = min(M_values)
    xmax = max(M_values)
    padding_x = (xmax - xmin) * 0.05

    ax.set_xlim(xmin - padding_x, xmax + padding_x)

    # -------- eixo Y automático --------
    ymax = max(max(avg_times), max(avg_sat))
    padding_y = ymax * 0.10

    ax.set_ylim(0, ymax + padding_y)

    # -------- formato percentual --------
    ax.yaxis.set_major_formatter(ticker.PercentFormatter())

    ax.legend()

    # limpa gráfico anterior
    for widget in frame.winfo_children():
        widget.destroy()

    canvas = FigureCanvasTkAgg(fig, master=frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)