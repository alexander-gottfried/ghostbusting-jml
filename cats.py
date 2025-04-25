import sys
import functools
import dataclasses

from dictutil import dict_entry_set_add
from boolexpr import BoolExpr
import jml

dataclass = functools.partial(
        dataclasses.dataclass,
        frozen=True, slots=True)

@dataclass
class CatNode(object):
    def __str__(self, paren=False, cdot=False):
        match self:
            case Union(l, r):
                if paren:
                    return f'({l} ∨ {r})'
                return f'{l} ∨ {r}'
            case Concat(l, r):
                mid = '' if AbstractTrace in [type(l), type(r)] else ' ⋅ '
                l, r = map(functools.partial(CatNode.__str__, paren=True), (l, r))
                return l + mid + r
            case FixPoint(expr):
                return f'μ{recvar}.({expr})'
            case AbstractTrace(excluded):
                result = '⋅⋅'
                if excluded: result += f'excl{excluded}'
                return result
            case Event(eventtype, args):
                return f'{eventtype}({args})'
            case Observation(mappings, statement):
                return f'℧{mappings}.⌈{statement}⌉'
            case Statement(expr):
                return f'⌈{expr}⌉'
        return None

@dataclass
class Union(CatNode):
    left: CatNode
    right: CatNode

@dataclass
class Concat(CatNode):
    left: CatNode
    right: CatNode

@dataclass
class Recvar(CatNode):
    name: str

@dataclass
class FixPoint(CatNode):
    recvar: Recvar
    expr: CatNode

@dataclass
class Event(CatNode):
    eventtype: str
    args: list[str]

@dataclass
class AbstractTrace(CatNode):
    excluded: list[Event]

@dataclass
class Observation(CatNode):
    mappings: ... # would be a dict, but variable ids don't have a set type yet
    statement: BoolExpr

@dataclass
class Statement(CatNode):
    expr: BoolExpr


def possible_transition_maps(graph):
    """
    Given a graph of form dict[state->dict[method->state]], return:
    (1) a nested dictionary `result` where `result[method][start]` gives all
    destination states `method` can transition into starting from `start`, and
    (2) a nested dictionary `flipped` where `flipped[method][destination]`
    gives all states that can transition into `destination` via `method`.
    """
    result, flipped = {}, {}
    for src, transitions in graph.items():
        for method, destinations in transitions.items():
            if method not in result:
                result[method] = {}
                flipped[method] = {}
            for dest in destinations:
                dict_entry_set_add(result[method], src, dest)
                dict_entry_set_add(flipped[method], dest, src)
    return result, flipped


#TODO rename
def something(graph):
    """
    Given a graph of form dict[state->dict[method->state]], return:
    (1) a dictionary `prestates` mapping each method to its possible prestates,
    (2) a dictionary `preceders` mapping each state to the set of methods it is
    a possible poststate of.
    """
    prestates, preceders = {}, {}
    for src, transitions in graph.items():
        for method, destinations in transitions.items():
            dict_entry_set_add(prestates, method, src)
            for dest in destinations:
                dict_entry_set_add(preceders, dest, method)
    return prestates, preceders


def naive_pretrace_from_graph(graph, methods, initial_state):
    """
    Return a pre-trace for each method in `methods` of form
    pop(preceders)⋅⋅excl[all] where preceders are all methods
    that may run right before the method.

    Union with ⋅⋅excl[all] if the method's prestates include an initial
    state.
    """
    prestates, preceders = something(graph)
    result = {}

    exclude_all_methods = AbstractTrace(methods)
    
    for method in methods:
        m_pres = prestates[method]
        pops = set()
        for pre in m_pres:
            if pre not in preceders: continue
            pops.update(preceders[pre])
        pops = (Event('pop', pop) for pop in list(pops))
        pops = functools.reduce(Union, pops)
        pretrace = Concat(pops, exclude_all_methods)
        includes_init = (initial_state in m_pres)
        if includes_init:
            pretrace = Union(exclude_all_methods, pretrace)
        result[method] = pretrace

    return result


def from_prepostcondition(cond: jml.Requires | jml.Ensures):
    ...
