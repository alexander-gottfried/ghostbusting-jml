"""
Classes representing JML clauses and statements.
"""

import functools
import dataclasses

from boolexpr import BoolExpr

dataclass = functools.partial(
        dataclasses.dataclass,
        slots=True, frozen=True)

class ContractClause:
    pass

@dataclass
class Requires(ContractClause):
    expr: BoolExpr

@dataclass
class Ensures(ContractClause):
    expr: BoolExpr

@dataclass
class Forall(ContractClause):
    variable: ...

@dataclass
class Callable(ContractClause):
    methods: list[str]

@dataclass
class Invariant:
    expr: BoolExpr

@dataclass
class Assignment:
    variable: ...
    
