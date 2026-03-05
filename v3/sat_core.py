# -*- coding: utf-8 -*-
"""
Gerador de fórmulas k-SAT (2-SAT ou 3-SAT) em FNC com valoração GLOBAL
única por execução.

Você pode escolher:
- k = 2 -> 2-SAT
- k = 3 -> 3-SAT

Impressão:
- Fórmula em FNC (uso de ∨, ∧, ¬)
- Valoração apenas das variáveis usadas na fórmula
- Nº de cláusulas satisfeitas e valor lógico final (conjunção)

Observação importante:
- Para evitar duplicidade da MESMA variável dentro de uma cláusula,
  são escolhidas variáveis distintas por cláusula.
- Em 3-SAT, se o número de variáveis disponíveis na fórmula for menor que 3,
  a cláusula pode ficar com 2 ou 1 literal (degradação suave).
"""
import random
from dataclasses import dataclass
from typing import List, Tuple, Dict, Iterable
from pysat.examples.rc2 import RC2
from pysat.formula import WCNF

# ---------- Tipos auxiliares ----------
Literal = Tuple[str, bool]  # (nome_da_variavel, negado?)
Clause = List[Literal]
Formula = List[Clause]


# ---------- Configuração por dataclass ----------
@dataclass
class SATConfig:
    # Número total de fórmulas a gerar
    num_formulas: int
    # Tamanho do universo global de variáveis
    # (uma valoração para cada, fixada por execução)
    num_global_variables: int
    # Intervalo de sorteio para o número de cláusulas K por fórmula (min, max)
    clauses_range: Tuple[int, int]
    # Intervalo de sorteio para o número MÁXIMO de
    # variáveis distintas permitidas em cada fórmula (min, max)
    max_vars_range: Tuple[int, int]
    # Valor de k do k-SAT (2 para 2-SAT, 3 para 3-SAT)
    k_literals_per_clause: int
    # Semente opcional para reprodutibilidade (None => aleatório por execução)
    # Caso a seed seja fornecida serão gerados o mesmo intervalo de valores
    seed: int | None = None
    # Com “strict=True” tenta-se FORÇAR exatamente k literais por cláusula
    # (se faltar variável distinta, a fórmula é reduzida).
    # Nota: por padrão é mantido strict=False para permitir degradação (1..k)
    # e não repetir variável na mesma cláusula.
    strict: bool = True


# ---------- Geração de nomes: 'A', 'B', ..., 'Z', 'AA', ... ----------
def _number_to_variable_name(n: int) -> str:
    """Converte 1 -> 'A', 26 -> 'Z', 27 -> 'AA', etc. (estilo Excel)."""
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(ord("A") + r) + s
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


def evaluate_formula(
    formula: Formula, assignment: Dict[str, bool]
) -> Tuple[int, int, bool]:
    """Retorna (satisfeitas, total, valor_da_conjunção)."""
    total = len(formula)
    sat = sum(evaluate_clause(c, assignment) for c in formula)
    return sat, total, (sat == total)


def format_literal(lit: Literal) -> str:
    var, neg = lit
    return f"¬{var}" if neg else var


def format_clause(clause: Clause) -> str:
    return "(" + " ∨ ".join(format_literal(lit) for lit in clause) + ")"


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
    Gera UMA cláusula usando 'available_vars'
    (variáveis distintas na mesma cláusula).
    - Tenta usar 'k' literais (para k-SAT).
    - Se strict=False e a fórmula tiver menos de k variáveis disponíveis,
      degrada-se para 2 ou 1.
    - Se strict=True, ainda tenta k; se não houver variáveis suficientes,
      usa-se o máximo possível (não é repetida a mesma variável na cláusula).
    """
    if not available_vars:
        # Sem variáveis disponíveis,
        # retorna cláusula unitária falsa (sem efeito).
        return []

    if strict:
        # ESTRITO: tenta k, mas sem repetir variável
        size = min(k, len(available_vars))
    else:
        # Degradação suave: usa até k,
        # respeitando o nº de variáveis disponíveis (>=1)
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
    - Escolhe um subconjunto (até 'max_vars_in_formula')
      do universo para ESTA fórmula.
    - Gera 'num_clauses' cláusulas; cada cláusula tenta ter 'k' literais,
      degradando para 2/1 se necessário quando strict=False.
    """
    qty = min(max_vars_in_formula, len(universe))
    if qty == 0:
        return []

    vars_of_formula = random.sample(universe, k=qty)

    # Gera as cláusulas
    formula: Formula = [
        generate_clause(
            vars_of_formula,
            k=k,
            strict=strict,
        )
        for _ in range(num_clauses)
    ]

    # Remove possíveis cláusulas vazias
    formula = [c for c in formula if len(c) > 0]
    return formula

def convert_formula_to_pysat(formula: Formula):
    """
    Converte Formula (com variáveis nomeadas) para CNF numérica (PySAT).
    Retorna (cnf, var_map) onde:
      - cnf: List[List[int]]
      - var_map: Dict[str, int]  (ex: {"A":1, "B":2, ...})
    """
    var_map: Dict[str, int] = {}
    next_id = 1
    cnf: List[List[int]] = []

    for clause in formula:
        new_clause: List[int] = []
        for var, neg in clause:
            if var not in var_map:
                var_map[var] = next_id
                next_id += 1

            lit = var_map[var]
            if neg:
                lit = -lit

            new_clause.append(lit)

        cnf.append(new_clause)

    return cnf, var_map


def format_pysat_cnf(cnf: List[List[int]]) -> str:
    """
    Formata CNF no estilo DIMACS (cada cláusula termina com 0).
    Exemplo: '1 -2 3 0  -1 4 0'
    """
    return "  ".join(" ".join(map(str, clause)) + " 0" for clause in cnf)


def solve_with_rc2(formula: Formula):
    """
    Resolve uma fórmula CNF usando o solver RC2 (Max-SAT puro).

    Passos:
    1. Converte a fórmula para o formato PySAT (inteiros).
    2. Cria uma estrutura WCNF.
    3. Adiciona todas as cláusulas com peso 1 (Max-SAT puro).
    4. Executa o solver RC2.

    Retorna:
        model  -> modelo encontrado pelo solver
        cost   -> número de cláusulas violadas
        cnf    -> fórmula no formato PySAT
        var_map -> mapeamento variável -> inteiro
    """

    cnf, var_map = convert_formula_to_pysat(formula)

    wcnf = WCNF()

    for clause in cnf:
        wcnf.append(clause, weight=1)

    with RC2(wcnf) as rc2:
        model = rc2.compute()
        cost = rc2.cost

    return model, cost, cnf, var_map


def model_to_assignment(model, var_map):
    """
    Converte o modelo retornado pelo RC2 para uma valoração de variáveis.

    model: lista de inteiros (ex: [1, -2, 3])
    var_map: mapeamento {variavel: indice}
    """
    assignment = {}

    for var, idx in var_map.items():
        assignment[var] = idx in model

    return assignment

# ---------- Função principal ----------
def generate_formulas_set(config: SATConfig):
    """
    - Cria o universo global de variáveis.
    - Define uma valoração global (firme para toda a execução).
    - Para cada fórmula:
        * São sorteados K (nº de cláusulas) no intervalo especificado.
        * São sorteados M (máx. de variáveis) no intervalo especificado.
        * Gera a fórmula k-SAT, avalia e imprime.
    - Ao final: é impresso com todas as fórmulas e suas valorações.
    """
    if config.seed is not None:
        random.seed(config.seed)

    universe = generate_variable_names(config.num_global_variables)
    global_assignment = generate_global_assignment(universe)

    print(
        f"Universo de variáveis: {config.num_global_variables} "
        f"({universe[0]}..{universe[-1]})"
    )

    print(
        "A valoração abaixo é GLOBAL e se mantém para todas as "
        "fórmulas nesta execução.\n"
    )

    resultados = []  # guarda (idx, formula_str, assignment_used)

    for idx in range(1, config.num_formulas + 1):
        k_min, k_max = config.clauses_range
        m_min, m_max = config.max_vars_range
        k_clauses = random.randint(k_min, k_max)
        m_vars = random.randint(m_min, m_max)

        formula = generate_k_sat_formula(
            universe=universe,
            max_vars_in_formula=m_vars,
            num_clauses=k_clauses,
            k=config.k_literals_per_clause,
            strict=config.strict,
        )

        model, cost, cnf, var_map = solve_with_rc2(formula)
        pysat_str = format_pysat_cnf(cnf)
        solver_assignment = model_to_assignment(model, var_map)

        formula_str = format_formula(formula)
        used_vars = sorted({var for clause in formula for (var, _) in clause})
        assignment_used = {v: global_assignment[v] for v in used_vars}
        # sat, total, final_value = evaluate_formula(formula, global_assignment)
        sat, total, final_value = evaluate_formula(formula, solver_assignment)

        print(f"Fórmula {idx}:")
        print(f"  - Nº de cláusulas (K): {k_clauses}")
        print(f"  - Máx. de variáveis consideradas (M): {m_vars}")

        k_value = config.k_literals_per_clause
        print(f"  - k-SAT (alvo de literais/cláusula): {k_value}")

        print(f"  - FNC: {formula_str if formula_str else '(vazia)'}")
        print(f"  - PySAT CNF: {pysat_str if pysat_str else '(vazia)'}")

        # --------- Valorações ---------
        if assignment_used:
            val_generated = ", ".join(
                f"{v}={'1' if b else '0'}" for v, b in assignment_used.items()
            )
        else:
            val_generated = "-"

        if solver_assignment:
            val_solver = ", ".join(
                f"{v}={'1' if b else '0'}" for v, b in solver_assignment.items()
            )
        else:
            val_solver = "-"

        print(f"  - Valoração gerada: {val_generated}")
        print(f"  - Valoração RC2: {val_solver}")

        # --------- Resultados ---------
        print(f"  - Modelo RC2: {model}")
        print(f"  - Custo RC2 (cláusulas violadas): {cost}")

        print(f"  - Cláusulas satisfeitas (modelo RC2): {sat}/{total}")
        print(
            "  - Valor lógico da fórmula (modelo RC2): "
            f"{'1 (Verdadeiro)' if final_value else '0 (Falso)'}\n"
        )

        resultados.append(
            (idx, formula_str, pysat_str, assignment_used, solver_assignment, final_value, model, cost)
        )
    # --------- Resumo final ---------
    # --------- Resumo final ---------
    print("=" * 60)
    print("RESUMO FINAL: Fórmulas e suas valorações\n")

    for idx, formula_str, pysat_str, assignment_used, solver_assignment, final_value, model, cost in resultados:
        val_generated = ", ".join(f"{v}={b}" for v, b in assignment_used.items()) if assignment_used else "-"
        val_solver = ", ".join(f"{v}={b}" for v, b in solver_assignment.items()) if solver_assignment else "-"

        print(f"F{idx}: {formula_str if formula_str else '(vazia)'}")
        print(f"    PySAT CNF: {pysat_str if pysat_str else '(vazia)'}")
        print(f"    Modelo RC2: {model}")
        print(f"    Custo RC2 (cláusulas violadas): {cost}")
        print(f"    Valoração gerada: {val_generated}")
        print(f"    Valoração RC2: {val_solver}")
        print(
            f"    Valor lógico da fórmula (modelo RC2): "
            f"{'1 (Verdadeiro)' if final_value else '0 (Falso)'}\n"
        )