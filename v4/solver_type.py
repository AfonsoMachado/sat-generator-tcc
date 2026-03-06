from enum import Enum

class SolverType(Enum):
    MAXSAT = "Max-sat"
    PARTIAL_MAXSAT = "Partial Max-sat"
    WEIGHTED_PARTIAL_MAXSAT = "Weighted Partial Max-sat"