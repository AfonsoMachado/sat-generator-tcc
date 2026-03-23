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
- n.º de cláusulas satisfeitas e valor lógico final (conjunção)

Observação importante:
- Para evitar duplicidade da MESMA variável numa cláusula, escolhemos variáveis distintas por cláusula.
- Em 3-SAT, se o número de variáveis disponíveis na fórmula for menor que 3, a cláusula pode ficar com 2 ou 1 literal
  (degradação suave). Se quiser proibir isso, veja 'strict' na classe SATConfig.'
"""
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
        cnf, var_map = convert_formula_to_pysat(formula)
        pysat_str = format_pysat_cnf(cnf)
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

        resultados.append((idx, formula_str, pysat_str, assignment_used, final_value))

    # --------- Resumo final ---------
    print("="*60)
    print("RESUMO FINAL: Fórmulas e suas valorações\n")
    for idx, formula_str, pysat_str, assignment_used, final_value in resultados:
        val_str = ", ".join(f"{v}={b}" for v, b in assignment_used.items())
        print(f"F{idx}: {formula_str if formula_str else '(vazia)'}")
        print(f"    PySAT CNF: {pysat_str if pysat_str else '(vazia)'}")
        print(f"    Valoração: {val_str if val_str else '-'}")
        print(f"    Valor lógico da fórmula: {final_value}\n")

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


# ---------- Perfis prontos ----------
def profile_2sat(seed: int | None = 42) -> SATConfig:
    return SATConfig(
        num_formulas=10,
        num_global_variables=102,
        clauses_range=(2, 5),
        max_vars_range=(2, 5),
        k_literals_per_clause=2,
        seed=seed,
        # O ideal é não permitir degradação de cláusulas para gerar todas com exatamente 2 literais
        strict=True,
    )

def profile_3sat(seed: int | None = 42) -> SATConfig:
    return SATConfig(
        num_formulas=50,
        num_global_variables=103,
        clauses_range=(1, 10),
        max_vars_range=(1, 100),
        k_literals_per_clause=3,
        seed=seed,
        # O ideal é não permitir degradação de cláusulas para gerar todas com exatamente 3 literais
        strict=True,
    )

# ---------- Execução de exemplo ----------
if __name__ == "__main__":
    # Escolha UM dos perfis abaixo descomentando a linha correspondente:

    # A seed definida como done gera resultados diferentes em cada execução.

    # 1) 2-SAT (padrão anterior)
    config = profile_2sat(seed=None)

    # 2) 3-SAT (conforme enunciado)
    # config = profile_3sat(seed=None)

    generate_formulas_set(config)
