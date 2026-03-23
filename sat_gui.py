import tkinter as tk
from tkinter import ttk, messagebox
from sat_core import SATConfig, generate_formulas_set


def run_generator(entries, text_details, text_summary):
    try:
        num_formulas = int(entries["formulas"].get())
        num_global_vars = int(entries["vars"].get())
        k = int(entries["k"].get())
        min_clauses = int(entries["min_clauses"].get())
        max_clauses = int(entries["max_clauses"].get())
        min_vars = int(entries["min_vars"].get())
        max_vars = int(entries["max_vars"].get())
        seed = int(entries["seed"].get()) if entries["seed"].get() else None

        config = SATConfig(
            num_formulas=num_formulas,
            num_global_variables=num_global_vars,
            clauses_range=(min_clauses, max_clauses),
            max_vars_range=(min_vars, max_vars),
            k_literals_per_clause=k,
            seed=seed,
            strict=False,
        )

        # Captura saída
        import io
        import sys

        old_stdout = sys.stdout
        sys.stdout = mystdout = io.StringIO()

        generate_formulas_set(config)

        sys.stdout = old_stdout
        full_output = mystdout.getvalue()

        # Divide saída em duas partes
        if "RESUMO FINAL:" in full_output:
            details_part, summary_part = full_output.split("RESUMO FINAL:", 1)
            summary_part = "RESUMO FINAL:" + summary_part
        else:
            details_part, summary_part = full_output, ""

        # Atualiza coluna 1 (detalhes)
        text_details.config(state="normal")
        text_details.delete("1.0", tk.END)
        text_details.insert(tk.END, details_part.strip())
        text_details.config(state="disabled")

        # Atualiza coluna 2 (resumo)
        text_summary.config(state="normal")
        text_summary.delete("1.0", tk.END)
        text_summary.insert(tk.END, summary_part.strip())
        text_summary.config(state="disabled")

    except Exception as e:
        messagebox.showerror("Erro", str(e))


def gui_runner():
    root = tk.Tk()
    root.title("Gerador de Fórmulas k-SAT")

    # Função de validação
    def only_integers(text: str) -> bool:
        return text == "" or text.isdigit()

    vcmd = (root.register(only_integers), "%P")

    # Entradas
    frame = ttk.Frame(root, padding=10)
    frame.grid(row=0, column=0, sticky="w")

    labels_defaults = [
        ("Número de fórmulas:", "10", "formulas"),
        ("Nº de variáveis globais:", "102", "vars"),
        ("k (2 ou 3):", "2", "k"),
        ("Mín cláusulas:", "2", "min_clauses"),
        ("Máx cláusulas:", "5", "max_clauses"),
        ("Mín variáveis:", "2", "min_vars"),
        ("Máx variáveis:", "5", "max_vars"),
        ("Seed (opcional):", "", "seed"),
    ]

    entries = {}
    for i, (lbl, default, key) in enumerate(labels_defaults):
        ttk.Label(frame, text=lbl).grid(row=i, column=0, sticky="w")
        e = ttk.Entry(frame, validate="key", validatecommand=vcmd)
        e.insert(0, default)
        e.grid(row=i, column=1)
        entries[key] = e

    # Área de saída em duas colunas
    output_frame = ttk.Panedwindow(root, orient="horizontal")
    output_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")

    # Coluna 1: Detalhes
    frame_left = ttk.Frame(output_frame)
    text_details = tk.Text(
        frame_left, wrap="none", width=90, height=25, state="disabled"
    )
    scrollbar_y1 = ttk.Scrollbar(
        frame_left, orient="vertical", command=text_details.yview
    )
    scrollbar_x1 = ttk.Scrollbar(
        frame_left, orient="horizontal", command=text_details.xview
    )
    text_details.configure(
        yscrollcommand=scrollbar_y1.set, xscrollcommand=scrollbar_x1.set
    )

    text_details.grid(row=0, column=0, sticky="nsew")
    scrollbar_y1.grid(row=0, column=1, sticky="ns")
    scrollbar_x1.grid(row=1, column=0, sticky="ew")
    frame_left.rowconfigure(0, weight=1)
    frame_left.columnconfigure(0, weight=1)

    # Coluna 2: Resumo
    frame_right = ttk.Frame(output_frame)
    text_summary = tk.Text(
        frame_right, wrap="none", width=60, height=25, state="disabled"
    )
    scrollbar_y2 = ttk.Scrollbar(
        frame_right, orient="vertical", command=text_summary.yview
    )
    scrollbar_x2 = ttk.Scrollbar(
        frame_right, orient="horizontal", command=text_summary.xview
    )
    text_summary.configure(
        yscrollcommand=scrollbar_y2.set, xscrollcommand=scrollbar_x2.set
    )

    text_summary.grid(row=0, column=0, sticky="nsew")
    scrollbar_y2.grid(row=0, column=1, sticky="ns")
    scrollbar_x2.grid(row=1, column=0, sticky="ew")
    frame_right.rowconfigure(0, weight=1)
    frame_right.columnconfigure(0, weight=1)

    # Adiciona colunas ao PanedWindow
    output_frame.add(frame_left, weight=3)
    output_frame.add(frame_right, weight=1)

    # Botão executar
    ttk.Button(
        root,
        text="Gerar Fórmulas",
        command=lambda: run_generator(entries, text_details, text_summary),
    ).grid(row=1, column=0, pady=10)

    # Ajustes de expansão
    root.rowconfigure(2, weight=1)
    root.columnconfigure(0, weight=1)

    return root
