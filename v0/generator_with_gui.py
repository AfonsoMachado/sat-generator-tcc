# -*- coding: utf-8 -*-
"""
Gerador de fórmulas k-SAT (2-SAT ou 3-SAT) em FNC com valoração GLOBAL única por execução.

Você pode escolher:
- k = 2 -> 2-SAT
- k = 3 -> 3-SAT

Perfis prontos:
- 2-SAT: N=10 fórmulas, universo=102 variáveis, K em [2,5], máx. vars/fórmula em [2,5]
- 3-SAT: N=50 fórmulas, universo=103 variáveis, K em [1,10], máx. vars/fórmula em [1,100]

Impressão:
- Fórmula em FNC (uso de ∨, ∧, ¬)
- Valoração apenas das variáveis usadas na fórmula
- Nº de cláusulas satisfeitas e valor lógico final (conjunção)

Observação importante:
- Para evitar duplicidade da MESMA variável dentro de uma cláusula, escolhemos variáveis distintas por cláusula.
- Em 3-SAT, se o número de variáveis disponíveis na fórmula for menor que 3, a cláusula pode ficar com 2 ou 1 literal
  (degradação suave). Se quiser proibir isso, veja o comentário “ESTRITO” abaixo.
"""
import tkinter as tk
from tkinter import ttk, messagebox
import random
from dataclasses import dataclass
from typing import List, Tuple, Dict, Iterable

# ---------- Tipos auxiliares ----------
Literal = Tuple[str, bool]   # (nome_da_variavel, negado?)
Clause  = List[Literal]
Formula = List[Clause]

# ---------- Configuração por dataclass ----------
@dataclass
class SATConfig:
    # Número total de fórmulas a gerar
    num_formulas: int
    # Tamanho do universo global de variáveis (uma valoração para cada, fixada por execução)
    num_global_variables: int
    # Intervalo de sorteio para o número de cláusulas K por fórmula (min, max)
    clauses_range: Tuple[int, int]
    # Intervalo de sorteio para o número MÁXIMO de variáveis distintas permitidas em cada fórmula (min, max)
    max_vars_range: Tuple[int, int]
    # Valor de k do k-SAT (2 para 2-SAT, 3 para 3-SAT)
    k_literals_per_clause: int
    # Semente opcional para reprodutibilidade (None => aleatório a cada execução)
    # Caso a seed seja fornecida serão gerados o mesmo intervalo de valores
    seed: int | None = None
    # Em “strict=True” tentamos FORÇAR exatamente k literais por cláusula (se faltar variável distinta, reduzimos a fórmula).
    # Nota: por padrão mantemos strict=False para permitir degradação (1..k) e não repetir variável na mesma cláusula.
    strict: bool = False


# ---------- Geração de nomes: 'A', 'B', ..., 'Z', 'AA', ... ----------
def _number_to_variable_name(n: int) -> str:
    """Converte 1 -> 'A', 26 -> 'Z', 27 -> 'AA', etc. (estilo Excel)."""
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(ord('A') + r) + s
    return s

def generate_variable_names(qty: int) -> List[str]:
    """Gera nomes ['A', 'B', ..., 'Z', 'AA', ...] até 'qty' itens."""
    return [_number_to_variable_name(i) for i in range(1, qty + 1)]


# ---------- Avaliação e formatação ----------
def evaluate_clause(clause: Clause, assignment: Dict[str, bool]) -> bool:
    """Cláusula (OR) é verdadeira se pelo menos um literal for verdadeiro."""
    for var, neg in clause:
        val = assignment[var]
        lit_val = (not val) if neg else val
        if lit_val:
            return True
    return False

def evaluate_formula(formula: Formula, assignment: Dict[str, bool]) -> Tuple[int, int, bool]:
    """Retorna (satisfeitas, total, valor_da_conjunção)."""
    total = len(formula)
    sat = sum(evaluate_clause(c, assignment) for c in formula)
    return sat, total, (sat == total)

def format_literal(lit: Literal) -> str:
    var, neg = lit
    return f"¬{var}" if neg else var

def format_clause(clause: Clause) -> str:
    return "(" + " ∨ ".join(format_literal(l) for l in clause) + ")"

def format_formula(formula: Formula) -> str:
    return " ∧ ".join(format_clause(c) for c in formula)


# ---------- Geradores ----------
def generate_global_assignment(var_names: Iterable[str]) -> Dict[str, bool]:
    """
    Gera uma valoração global fixa para TODAS as variáveis.
    Cada variável recebe True/False uma única vez por execução.
    """
    return {v: random.choice([True, False]) for v in var_names}

def generate_clause(available_vars: List[str], k: int, strict: bool) -> Clause:
    """
    Gera UMA cláusula usando 'available_vars' (variáveis distintas na mesma cláusula).
    - Tentamos usar 'k' literais (para k-SAT).
    - Se strict=False e a fórmula tiver menos de k variáveis disponíveis, degradamos para 2 ou 1.
    - Se strict=True, ainda tentaremos k; se não houver variáveis suficientes, usamos o máximo possível
      (não repetimos a mesma variável na cláusula).
      * Se desejar “falhar” caso não haja variáveis suficientes em modo estrito, você pode lançar um erro aqui.
    """
    if not available_vars:
        # Sem variáveis disponíveis, retorna cláusula unitária falsa (sem efeito) — mas evitamos isso.
        return []

    if strict:
        size = min(k, len(available_vars))  # ESTRITO: tenta k, mas sem repetir variável
    else:
        # Degradação suave: usa até k, respeitando o nº de variáveis disponíveis (>=1)
        size = min(k, len(available_vars))
        if size == 0:  # segurança
            size = 1

    # Escolhe variáveis distintas para esta cláusula
    chosen = random.sample(available_vars, k=size)

    # Sorteia a negação de cada literal independentemente
    clause: Clause = []
    for var in chosen:
        negated = random.choice([True, False])
        clause.append((var, negated))
    return clause

def generate_k_sat_formula(
        universe: List[str],
        max_vars_in_formula: int,
        num_clauses: int,
        k: int,
        strict: bool,
) -> Formula:
    """
    Monta uma fórmula (lista de cláusulas) em FNC:
    - Escolhe um subconjunto (até 'max_vars_in_formula') do universo para ESTA fórmula.
    - Gera 'num_clauses' cláusulas; cada cláusula tenta ter 'k' literais (2 ou 3),
      degradando para 2/1 se necessário quando strict=False.
    """
    qty = min(max_vars_in_formula, len(universe))
    if qty == 0:
        return []

    vars_of_formula = random.sample(universe, k=qty)

    # Gera as cláusulas
    formula: Formula = [generate_clause(vars_of_formula, k=k, strict=strict) for _ in range(num_clauses)]
    # Remove possíveis cláusulas vazias (por segurança extrema; não é esperado ocorrer com as checagens acima)
    formula = [c for c in formula if len(c) > 0]
    return formula


# ---------- Função principal ----------
def generate_formulas_set(config: SATConfig):
    """
    - Cria o universo global de variáveis.
    - Define uma valoração global (firme para toda a execução).
    - Para cada fórmula:
        * Sorteia K (nº de cláusulas) no intervalo especificado.
        * Sorteia M (máx. de variáveis) no intervalo especificado.
        * Gera a fórmula k-SAT, avalia e imprime.
    - Ao final: imprime resumo com todas as fórmulas e suas valorações.
    """
    if config.seed is not None:
        random.seed(config.seed)

    universe = generate_variable_names(config.num_global_variables)
    global_assignment = generate_global_assignment(universe)

    print(f"Universo de variáveis: {config.num_global_variables} ({universe[0]}..{universe[-1]})")
    print("A valoração abaixo é GLOBAL e se mantém para todas as fórmulas nesta execução.\n")

    resultados = []  # guarda (idx, formula_str, assignment_used)

    for idx in range(1, config.num_formulas + 1):
        k_min, k_max = config.clauses_range
        m_min, m_max = config.max_vars_range
        k_clauses = random.randint(k_min, k_max)
        m_vars    = random.randint(m_min, m_max)

        formula = generate_k_sat_formula(
            universe=universe,
            max_vars_in_formula=m_vars,
            num_clauses=k_clauses,
            k=config.k_literals_per_clause,
            strict=config.strict,
        )

        formula_str = format_formula(formula)
        used_vars = sorted({var for clause in formula for (var, _) in clause})
        assignment_used = {v: global_assignment[v] for v in used_vars}
        sat, total, final_value = evaluate_formula(formula, global_assignment)

        print(f"Fórmula {idx}:")
        print(f"  - Nº de cláusulas (K): {k_clauses}")
        print(f"  - Máx. de variáveis consideradas (M): {m_vars}")
        print(f"  - k-SAT (alvo de literais/ cláusula): {config.k_literals_per_clause}")
        print(f"  - FNC: {formula_str if formula_str else '(vazia)'}")
        print(f"  - Variáveis usadas ({len(used_vars)}): {', '.join(used_vars) if used_vars else '-'}")
        if used_vars:
            print("  - Valoração (usadas): " +
                  ", ".join(f"{v}={'1' if b else '0'}" for v, b in assignment_used.items()))
        else:
            print("  - Valoração (usadas): -")
        print(f"  - Cláusulas satisfeitas: {sat}/{total}")
        print(f"  - Valor lógico da fórmula (conjunção): {'1 (Verdadeiro)' if final_value else '0 (Falso)'}\n")

        resultados.append((idx, formula_str, assignment_used, final_value))

    # --------- Resumo final ---------
    print("="*60)
    print("RESUMO FINAL: Fórmulas e suas valorações\n")
    for idx, formula_str, assignment_used, final_value in resultados:
        val_str = ", ".join(f"{v}={b}" for v, b in assignment_used.items())
        print(f"F{idx}: {formula_str if formula_str else '(vazia)'}")
        print(f"    Valoração: {val_str if val_str else '-'}")
        print(f"    Valor lógico da fórmula: {final_value}\n")


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
            strict=False
        )

        # Captura saída
        import io, sys
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


def create_gui():
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
        ("Seed (opcional):", "", "seed")
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
    text_details = tk.Text(frame_left, wrap="none", width=90, height=25, state="disabled")
    scrollbar_y1 = ttk.Scrollbar(frame_left, orient="vertical", command=text_details.yview)
    scrollbar_x1 = ttk.Scrollbar(frame_left, orient="horizontal", command=text_details.xview)
    text_details.configure(yscrollcommand=scrollbar_y1.set, xscrollcommand=scrollbar_x1.set)

    text_details.grid(row=0, column=0, sticky="nsew")
    scrollbar_y1.grid(row=0, column=1, sticky="ns")
    scrollbar_x1.grid(row=1, column=0, sticky="ew")
    frame_left.rowconfigure(0, weight=1)
    frame_left.columnconfigure(0, weight=1)

    # Coluna 2: Resumo
    frame_right = ttk.Frame(output_frame)
    text_summary = tk.Text(frame_right, wrap="none", width=60, height=25, state="disabled")
    scrollbar_y2 = ttk.Scrollbar(frame_right, orient="vertical", command=text_summary.yview)
    scrollbar_x2 = ttk.Scrollbar(frame_right, orient="horizontal", command=text_summary.xview)
    text_summary.configure(yscrollcommand=scrollbar_y2.set, xscrollcommand=scrollbar_x2.set)

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
        command=lambda: run_generator(entries, text_details, text_summary)
    ).grid(row=1, column=0, pady=10)

    # Ajustes de expansão
    root.rowconfigure(2, weight=1)
    root.columnconfigure(0, weight=1)

    return root


# ---------- Execução ----------
if __name__ == "__main__":
    app = create_gui()
    app.mainloop()
