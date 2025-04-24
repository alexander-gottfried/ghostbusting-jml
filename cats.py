import sys
import functools
import dataclasses

from dictutil import dict_entry_set_add

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


def possible_transition_maps(graph):
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


def something(graph):
    prestates, preceders = {}, {}
    for src, transitions in graph.items():
        for method, destinations in transitions.items():
            dict_entry_set_add(prestates, method, src)
            for dest in destinations:
                dict_entry_set_add(preceders, dest, method)
    return prestates, preceders


def from_graph(graph, methods, initial_state):
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

"""
def from_graph(all_methods, initital_state):
    pre_methods, post_methods = to_maps(all_methods)

    exclude_all_methods = cats.AbstractTrace(
            [m[0] for m in all_methods])

    result = {}

    for method_id, pres, _ in all_methods:
        pops = set()
        includes_init = False
        for pre in pres:
            if not pre in post_methods: continue
            includes_init = (pre == initital_state) or includes_init
            pops.update(post_methods[pre])
        pops = (cats.Event('pop', pop) for pop in list(pops))
        pops = functools.reduce(cats.Union, pops) # pop(m1) v pop(m2) v ...
        pretrace = cats.Concat(pops, exclude_all_methods)
        if includes_init: pretrace = cats.Union(exclude_all_methods, pretrace)
        result[method_id] = pretrace

    return result
"""
