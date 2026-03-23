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
def evaluate_clause(clause: List[int], assignment: Dict[int, bool]) -> bool:

    for lit in clause:

        var = abs(lit)
        neg = lit < 0

        val = assignment[var]

        if not val if neg else val:
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
def generate_global_assignment(num_vars: int):

    return {
        v: random.choice([True, False])
        for v in range(1, num_vars + 1)
    }

def generate_clause(num_vars: int, k: int, strict: bool) -> List[int]:
    """
    Gera uma cláusula diretamente no formato PySAT (inteiros).

    Requisitos do algoritmo do texto:
    - vetor de candidatos reconstruído a cada cláusula
    - candidatos = [-N..-1, 1..N]
    - escolha sem repetição
    - cláusula com K literais
    """

    # vetor de candidatos reconstruído
    candidates = list(range(-num_vars, 0)) + list(range(1, num_vars + 1))

    if strict:
        size = k
    else:
        size = min(k, num_vars)

    # escolhe K literais distintos
    clause = random.sample(candidates, size)

    return clause

def generate_k_sat_formula(
    num_vars: int,
    num_clauses: int,
    k: int,
    strict: bool,
) -> List[List[int]]:
    """
    Gera fórmula já no formato CNF do PySAT.

    Retorna:
        List[List[int]]
    """

    formula = []

    for _ in range(num_clauses):

        clause = generate_clause(
            num_vars=num_vars,
            k=k,
            strict=strict
        )

        formula.append(clause)

    return formula


# ---------- Função principal ----------
def generate_formulas_set(config: SATConfig):

    if config.seed is not None:
        random.seed(config.seed)

    N = config.num_global_variables

    global_assignment = generate_global_assignment(N)

    print(f"Universo de variáveis: {N} (1..{N})")
    print("A valoração abaixo é GLOBAL e se mantém para todas as fórmulas nesta execução.\n")

    resultados = []

    for idx in range(1, config.num_formulas + 1):

        k_min, k_max = config.clauses_range
        m_min, m_max = config.max_vars_range

        k_clauses = random.randint(k_min, k_max)
        m_vars    = random.randint(m_min, m_max)

        cnf = generate_k_sat_formula(
            num_vars=m_vars,
            num_clauses=k_clauses,
            k=config.k_literals_per_clause,
            strict=config.strict,
        )

        pysat_str = format_pysat_cnf(cnf)

        # variáveis usadas
        used_vars = sorted({abs(lit) for clause in cnf for lit in clause})

        assignment_used = {v: global_assignment[v] for v in used_vars}

        sat, total, final_value = evaluate_formula(cnf, global_assignment)

        print(f"Fórmula {idx}:")
        print(f"  - Nº de cláusulas (K): {k_clauses}")
        print(f"  - Máx. de variáveis consideradas (M): {m_vars}")
        print(f"  - k-SAT (literais/cláusula): {config.k_literals_per_clause}")

        print(f"  - PySAT CNF: {pysat_str if pysat_str else '(vazia)'}")

        print(f"  - Variáveis usadas ({len(used_vars)}): "
              f"{', '.join(map(str, used_vars)) if used_vars else '-'}")

        if used_vars:
            print("  - Valoração (usadas): " +
                  ", ".join(f"{v}={'1' if b else '0'}"
                            for v, b in assignment_used.items()))
        else:
            print("  - Valoração (usadas): -")

        print(f"  - Cláusulas satisfeitas: {sat}/{total}")

        print(f"  - Valor lógico da fórmula (conjunção): "
              f"{'1 (Verdadeiro)' if final_value else '0 (Falso)'}\n")

        resultados.append((idx, pysat_str, assignment_used, final_value))

    # -------- RESUMO FINAL --------

    print("=" * 60)
    print("RESUMO FINAL: Fórmulas e suas valorações\n")

    for idx, pysat_str, assignment_used, final_value in resultados:

        val_str = ", ".join(
            f"{v}={int(b)}"
            for v, b in assignment_used.items()
        )

        print(f"F{idx}:")
        print(f"    PySAT CNF: {pysat_str if pysat_str else '(vazia)'}")
        print(f"    Valoração: {val_str if val_str else '-'}")
        print(f"    Valor lógico da fórmula: {final_value}\n")

def format_pysat_cnf(cnf: List[List[int]]) -> str:
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
