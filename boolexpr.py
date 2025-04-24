import dataclasses
import functools
from enum import Enum, auto

dataclass = functools.partial(
        dataclasses.dataclass,
        slots=True, frozen=True)

@dataclass
class Value:
    def resolve(self, state, prestate):
        match self:
            case Literal(x):
                return x
            case Variable(i):
                return state[i]
            case Old(i):
                return prestate[i]

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
    def contains_old(self):
        match self:
            case Rel(_, left, right):
                return Old in (type(left), type(right))
            case And(left, right) | Or(left, right):
                return left.contains_old() or right.contains_old()
            case Not(e):
                return e.contains_old()
            case BoolTrue() | BoolFalse():
                return False

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
    Equal = auto()
    NotEqual = auto()
    LessThan = auto()
    LessEqual = auto()
    GreaterThan = auto()
    GreaterEqual = auto()

@dataclass
class Rel(BoolExpr):
    kind: RelType
    left: Value
    right: Value

    def negation(self):
        match self.kind:
            case RelType.Equal:
                return Rel(RelType.NotEqual, self.left, self.right)
            case RelType.NotEqual:
                return Rel(RelType.Equal, self.left, self.right)
            case RelType.LessThan:
                return Rel(RelType.GreaterEqual, self.left, self.right)
            case RelType.LessEqual:
                return Rel(RelType.GreaterThan, self.left, self.right)
            case RelType.GreaterThan:
                return Rel(RelType.LessEqual, self.left, self.right)
            case RelType.GreaterEqual:
                return Rel(RelType.LessThan, self.left, self.right)

    def evaluate(self, state, prestate=None):
        left = self.left.resolve(state, prestate)
        right = self.right.resolve(state, prestate)
        match self.kind:
            case RelType.Equal:
                return left == right
            case RelType.NotEqual:
                return left != right
            case RelType.LessThan:
                return left < right
            case RelType.LessEqual:
                return left <= right
            case RelType.GreaterThan:
                return left > right
            case RelType.GreaterEqual:
                return left >= right

def _Rel(kind, left, right):
    if type(left) is int: left = Literal(left)
    if type(right) is int: right = Literal(right)
    return Rel(kind, left, right)

def Equal(left, right):
    return _Rel(RelType.Equal, left, right)

def NotEqual(left, right):
    return _Rel(RelType.NotEqual, left, right)

def LessThan(left, right):
    return _Rel(RelType.LessThan, left, right)

def LessEqual(left, right):
    return _Rel(RelType.LessEqual, left, right)

def GreaterThan(left, right):
    return _Rel(RelType.GreaterThan, left, right)

def GreaterEqual(left, right):
    return _Rel(RelType.GreaterEqual, left, right)


def satisfies[T](state: tuple[int], expr: BoolExpr, prestate=None) -> bool:
    """
    state maps variables to values

    state should map all ghost variables
    may raise a KeyError otherwise
    """
    match expr:
        case BoolTrue():
            return True
        case BoolFalse():
            return False
        case Rel(_, _, _):
            return expr.evaluate(state, prestate)
        case And(left, right):
            return satisfies(state, left) and satisfies(state, right)
        case Or(left, right):
            return satisfies(state, left) or satisfies(state, right)
        case Not(a):
            return not satisfies(state, a)


@functools.cache
def downprop_negations(a: BoolExpr) -> BoolExpr:
    match a:
        case Not(BoolTrue()):
            return BoolFalse()
        case Not(BoolFalse()):
            return BoolTrue()
        case Not(Equal(name, val)):
            return NotEqual(name, val)
        case Not(NotEqual(name, val)):
            return Equal(name, val)
        case Not(And(left, right)):
            left, right = map(lambda x: downprop_negations(Not(x)), (left, right))
            return Or(left, right)
        case Not(Or(left, right)):
            left, right = map(lambda x: downprop_negations(Not(x)), (left, right))
            return And(left, right)
        case Not(Not(a)):
            return downprop_negations(a)
        case And(left, right):
            left, right = map(downprop_negations, (left, right))
            return And(left, right)
        case Or(left, right):
            left, right = map(downprop_negations, (left, right))
            return Or(left, right)
    return a

def implies(a, b):
    return not(a) or b

def expr_satisfies(one: BoolExpr, other: BoolExpr) -> BoolExpr:
    one, other = map(downprop_negations, (one, other))
    match one, other:
        case (_, BoolTrue()) | (BoolTrue(), _) | (BoolFalse(), _):
            return True
        case _, BoolFalse():
            return False
        case Equal(a, x), Equal(b, y):
            return implies(a == b, x == y)
        case (Equal(a, x), NotEqual(b, y)) | (NotEqual(a, x), Equal(b, y)):
            return implies(a == b, x != y)
        case NotEqual(a, x), NotEqual(b, y):
            return true
        case And(a, b), right:
            return (expr_satisfies(a, right)
                    and expr_satisfies(b, right))
        case Or(a, b), right:
            return (expr_satisfies(a, right)
                    or expr_satisfies(b, right))
        case left, And(a, b):
            return (expr_satisfies(left, a)
                    and expr_satisfies(left, b))
        case left, Or(a, b):
            return (expr_satisfies(left, a)
                    or expr_satisfies(left, b))
