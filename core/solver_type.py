from enum import Enum


class SolverType(Enum):
    """
    Enumeração que define os tipos de solver suportados no experimento.

    Essa estrutura é utilizada para padronizar a identificação do tipo de
    problema sendo resolvido, permitindo que o fluxo de execução selecione
    corretamente a estratégia de modelagem e resolução (ex: pesos, restrições, etc).

    Tipos disponíveis:
    - MAXSAT:
        Todas as cláusulas são tratadas como soft constraints com o mesmo peso.
        O objetivo é maximizar o número total de cláusulas satisfeitas.

    - PARTIAL_MAXSAT:
        Combina cláusulas hard (obrigatórias) e soft (otimizáveis).
        O solver deve satisfazer todas as cláusulas hard e maximizar as soft.

    - WEIGHTED_PARTIAL_MAXSAT:
        Variante do Partial Max-SAT onde as cláusulas soft possuem pesos distintos,
        permitindo priorização de determinadas cláusulas na função objetivo.

    Observação:
    Os valores associados (strings) são utilizados para:
    - Identificação em logs e arquivos de saída
    - Nomeação de arquivos de resultados
    - Exibição na interface do usuário
    """

    MAXSAT = "Max-sat"
    PARTIAL_MAXSAT = "Partial Max-sat"
    WEIGHTED_PARTIAL_MAXSAT = "Weighted Partial Max-sat"
