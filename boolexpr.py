"""
Classes for modeling boolean expressions in JML clauses. Being a subset of JML
boolean expressions, Java boolean expressions may be modeled too.

TODO:
    - binary comparisons should be able to contain full expressions too. Add
      those cases.
"""

import dataclasses
import functools
from enum import Enum, auto

dataclass = functools.partial(
        dataclasses.dataclass,
        slots=True, frozen=True)

@dataclass
class Value:
    def resolve(self, state, prestate):
        """Return a variable's value given a state and prestate."""
        match self:
            case Literal(x):
                result = x
            case Variable(i):
                result = state[i]
            case Old(i):
                result = prestate[i]
        return result

@dataclass
class Variable(Value):
    var_id: int

@dataclass
class Old(Value):
    var_id: int

@dataclass
class Literal(Value):
    value: int


@dataclass
class BoolExpr:
    """Class representing a JML boolean expression."""
    def contains_old(self):
        r"""Return True if the expression contains any \old() variables."""
        match self:
            case Rel(_, left, right):
                result = Old in (type(left), type(right))
            case And(left, right) | Or(left, right):
                result = left.contains_old() or right.contains_old()
            case Not(e):
                result = e.contains_old()
            case BoolTrue() | BoolFalse():
                result = False
        return result

@dataclass
class And(BoolExpr):
    left: BoolExpr
    right: BoolExpr

@dataclass
class Or(BoolExpr):
    left: BoolExpr
    right: BoolExpr

@dataclass
class Not(BoolExpr):
    expr: BoolExpr

@dataclass
class BoolTrue(BoolExpr):
    pass

@dataclass
class BoolFalse(BoolExpr):
    pass

class RelType(Enum):
    EQUAL = auto()
    NOT_EQUAL = auto()
    LESS_THAN = auto()
    LESS_EQUAL = auto()
    GREATER_THAN = auto()
    GREATER_EQUAL = auto()

@dataclass
class Rel(BoolExpr):
    kind: RelType
    left: Value
    right: Value

    def negation(self):
        match self.kind:
            case RelType.EQUAL:
                result = Rel(RelType.NOT_EQUAL, self.left, self.right)
            case RelType.NOT_EQUAL:
                result = Rel(RelType.EQUAL, self.left, self.right)
            case RelType.LESS_THAN:
                result = Rel(RelType.GREATER_EQUAL, self.left, self.right)
            case RelType.LESS_EQUAL:
                result = Rel(RelType.GREATER_THAN, self.left, self.right)
            case RelType.GREATER_THAN:
                result = Rel(RelType.LESS_EQUAL, self.left, self.right)
            case RelType.GREATER_EQUAL:
                result = Rel(RelType.LESS_THAN, self.left, self.right)
        return result

    def evaluate(self, state, prestate=None):
        left = self.left.resolve(state, prestate)
        right = self.right.resolve(state, prestate)
        match self.kind:
            case RelType.EQUAL:
                result = left == right
            case RelType.NOT_EQUAL:
                result = left != right
            case RelType.LESS_THAN:
                result = left < right
            case RelType.LESS_EQUAL:
                result = left <= right
            case RelType.GREATER_THAN:
                result = left > right
            case RelType.GREATER_EQUAL:
                result = left >= right
        return result

def _rel(kind, left, right):
    def to_literal(node):
        return Literal(node) if isinstance(node, int) else node
    left, right = map(to_literal, (left, right))
    return Rel(kind, left, right)

def Equal(left, right):
    return _rel(RelType.EQUAL, left, right)

def NotEqual(left, right):
    return _rel(RelType.NOT_EQUAL, left, right)

def LessThan(left, right):
    return _rel(RelType.LESS_THAN, left, right)

def LessEqual(left, right):
    return _rel(RelType.LESS_EQUAL, left, right)

def GreaterThan(left, right):
    return _rel(RelType.GREATER_THAN, left, right)

def GreaterEqual(left, right):
    return _rel(RelType.GREATER_EQUAL, left, right)


def satisfies(state: tuple[int], expr: BoolExpr, prestate=None) -> bool:
    """
    Return True if the variable mapping represented by `state` satisfies
    the boolean expression `expr`.

    `state` has to map all variables; KeyError may be raised otherwise.
    """
    match expr:
        case BoolTrue():
            result = True
        case BoolFalse():
            result = False
        case Rel(_, _, _):
            result = expr.evaluate(state, prestate)
        case And(left, right):
            result = satisfies(state, left) and satisfies(state, right)
        case Or(left, right):
            result = satisfies(state, left) or satisfies(state, right)
        case Not(a):
            result = not satisfies(state, a)
    return result


@functools.cache
def downprop_negations(a: BoolExpr) -> BoolExpr:
    """
    Eliminate `Not` by propagating them downwards and return the result. The
    'leaves' of an expression are either binary comparisons like ==, or boolean
    literals, which can be negated trivially.

    Eliminating `Not` makes expressions easier to work with in some cases.
    """
    result = a
    match a:
        case Not(BoolTrue()):
            result = BoolFalse()
        case Not(BoolFalse()):
            result = BoolTrue()
        case Not(Equal(name, val)):
            result = NotEqual(name, val)
        case Not(NotEqual(name, val)):
            result = Equal(name, val)
        case Not(And(left, right)):
            left, right = map(lambda x: downprop_negations(Not(x)), (left, right))
            result = Or(left, right)
        case Not(Or(left, right)):
            left, right = map(lambda x: downprop_negations(Not(x)), (left, right))
            result = And(left, right)
        case Not(Not(a)):
            result = downprop_negations(a)
        case And(left, right):
            left, right = map(downprop_negations, (left, right))
            result = And(left, right)
        case Or(left, right):
            left, right = map(downprop_negations, (left, right))
            result = Or(left, right)
    return result

def implies(a, b):
    return not(a) or b

def expr_satisfies(one: BoolExpr, other: BoolExpr) -> bool:
    """Return True if states satisfying `one` also satisfy `other`."""
    one, other = map(downprop_negations, (one, other))
    match one, other:
        case (_, BoolTrue()) | (BoolTrue(), _) | (BoolFalse(), _):
            result = True
        case _, BoolFalse():
            result = False
        case Equal(a, x), Equal(b, y):
            result = implies(a == b, x == y)
        case (Equal(a, x), NotEqual(b, y)) | (NotEqual(a, x), Equal(b, y)):
            result = implies(a == b, x != y)
        case NotEqual(a, x), NotEqual(b, y):
            result = True
        case And(a, b), right:
            result = (expr_satisfies(a, right)
                    and expr_satisfies(b, right))
        case Or(a, b), right:
            result = (expr_satisfies(a, right)
                    or expr_satisfies(b, right))
        case left, And(a, b):
            result = (expr_satisfies(left, a)
                    and expr_satisfies(left, b))
        case left, Or(a, b):
            result = (expr_satisfies(left, a)
                    or expr_satisfies(left, b))
    return result


def rename_old(expr, remap):
    r"""
    Replace \old variables with aliases as specified by the dict `remap`.

    Used for translation into CATs.
    """
    match expr:
        case Old(i):
            return Variable(remap[i])
        case Literal(_) | Variable(_) | RelType():
            return expr
    constr = type(expr)
    args = (getattr(expr, slot) for slot in expr.__slots__)
    args = (rename_old(arg, remap) for arg in args)
    return constr(*args)
