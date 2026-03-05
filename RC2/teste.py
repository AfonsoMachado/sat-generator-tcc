from pysat.examples.rc2 import RC2
from pysat.formula import WCNF

# cria fórmula
wcnf = WCNF()

# adiciona cláusulas
wcnf.append([1, 2])
wcnf.append([-1, 3])
wcnf.append([-2, -3])

# executa solver
with RC2(wcnf) as rc2:
    model = rc2.compute()

    print("Modelo:", model)
    print("Custo:", rc2.cost)
