import dataclasses
import functools
from typing import Self

from dictutil import dict_entry_set_add

class Regex(object):
    __match_args__ = ()

    def __str__(self):
        match self:
            case Empty():
                return 'ε'
            case Terminal(name):
                return str(name)
            case Concat(Alter(al, ar), right):
                return f'({al} | {ar}) {right}'
            case Concat(left, Alter(al, ar)):
                return f'{left} ({al} | {ar})'
            case Concat(left, right):
                return f'{left} {right}'
            case Alter(left, right):
                return f'{left} | {right}'
            case Repeat(Terminal(name)):
                return f'{name}*'
            case RepeatOne(Terminal(name)):
                return f'{name}+'
            case Optional(Terminal(name)):
                return f'{name}?'
            case Repeat(expr):
                return f'({expr})*'
            case RepeatOne(expr):
                return f'({expr})+'
            case Optional(expr):
                return f'({expr})?'

dataclass = functools.partial(
        dataclasses.dataclass,
        slots=True, frozen=True)

@dataclass
class Empty(Regex):
    pass

@dataclass
class Terminal(Regex):
    name: str

@dataclass
class Repeat(Regex):
    expr: Regex

@dataclass
class Concat(Regex):
    left: Regex
    right: Self

    def __post_init__(self):
        if type(self.left) == Concat:
            raise TypeError("left of Concat can't be an Concat")

@dataclass
class Alter(Regex):
    left: Regex
    right: Self

    def __post_init__(self):
        if type(self.left) == Alter:
            raise TypeError("left of Alter can't be an Alter")

@dataclass
class Optional(Regex):
    expr: Regex

@dataclass
class RepeatOne(Regex):
    expr: Regex


def concat_to_list(regex):
    match regex:
        case Concat(left, Concat(_) as right):
            return [left] + concat_to_list(right)
        case Concat(left, right):
            return [left, right]
    return [regex]

def alter_to_list(regex):
    match regex:
        case Alter(left, Alter(_) as right):
            return [left] + alter_to_list(right)
        case Alter(left, right):
            return [left, right]
    return [regex]


# Constructors #
# These perform trivial simplifications, like A** = A*

def empty():
    return Empty()

def terminal(x):
    return Terminal(x)

def repeat(e):
    match e:
        case Empty() | Repeat(_):
            return e
        case Optional(a) | RepeatOne(a):
            return Repeat(a)
        case _:
            return Repeat(e)

def repeat_one(e):
    match e:
        case Empty() | Repeat(_) | RepeatOne(_):
            return e
        case Optional(a):
            return repeat(a)
        case _:
            return RepeatOne(e)

def optional(e):
    match e:
        case Empty() | Repeat(_) | Optional(_):
            return e
        case RepeatOne(a):
            return repeat(a)
        case _:
            return Optional(e)

def concat(l, r):
    match (l, r):
        case (Empty(), x) | (x, Empty()):
            return x
        case (Concat(cl, cr), x):
            return concat(cl, concat(cr, x))
        case _:
            return Concat(l, r)

def alter(l, r):
    if l == r:
        return l
    match (l, r):
        case (Empty(), Empty()):
            return empty()
        case (Alter(al, ar), x):
            return alter(al, alter(ar, x))
        case _:
            return Alter(l, r)


def pass_on(func, regex: Regex) -> Regex:
    match regex:
        case Empty() | Terminal(_):
            return regex
        case Repeat(a):
            return repeat(func(a))
        case RepeatOne(a):
            return repeat_one(func(a))
        case Optional(a):
            return optional(func(a))
        case Alter(l, r):
            l, r = map(func, (l, r))
            return alter(l, r)
        case Concat(l, r):
            l, r = map(func, (l, r))
            return concat(l, r)


def eliminate_optionals(regex: Regex) -> Regex:
    match regex:
        case Repeat(_) | Optional(_):
            return empty()
        case RepeatOne(a):
            return eliminate_optionals(a)
        case Concat(Repeat(_) | Optional(_), rest):
            return eliminate_optionals(rest)

    return pass_on(eliminate_optionals, regex)


def collapse_same_prefix(regex: Regex) -> Regex:
    match regex:
        case Alter(Empty(), rest):
            rest = collapse_same_prefix(rest)
            return optional(rest)
        case Alter(a, Concat(b, rest)):
            a, b, rest = map(collapse_same_prefix, (a, b, rest))
            if a == b:
                return concat(a, optional(rest))
            return alter(a, concat(b, rest))
        case Alter(Concat(rest, a), b):
            a, b, rest = map(collapse_same_prefix, (a, b, rest))
            if a == b:
                return concat(optional(rest), a)
            return alter(concat(rest, a), b)

    return pass_on(collapse_same_prefix, regex)


def must_contain(regex: Regex) -> Regex:
    regex = eliminate_optionals(regex)
    regex = collapse_same_prefix(regex)
    regex = eliminate_optionals(regex)
    return set(alter_to_list(regex))


def last_calls(regex: Regex) -> Regex:
    regex = eliminate_optionals(regex)

    def aux(r):
        match r:
            case Empty() | Terminal(_):
                return r
            case Repeat(_) | Optional(_):
                return empty()
            case RepeatOne(a):
                return aux(a)
            case Concat(_, rest):
                return aux(rest)
            case Alter(l, rest):
                return alter(aux(l), aux(rest))

    return set(alter_to_list(aux(regex)))


def graph(graph, starting_node=None, ending_nodes=None):
    result = {}
    for s, ts in graph.items():
        result[s] = {}
        for t, ds in ts.items():
            for d in ds:
                term = terminal(t)
                if d in result[s]:
                    result[s][d] = alter(term, result[s][d])
                else:
                    result[s][d] = term
    if starting_node is None or ending_nodes is None:
        return result

    result['S'] = {starting_node: empty()}
    for end in ending_nodes:
        result[end]['E'] = empty()
    return result


def _depth_one_copy(graph):
    return {k: v.copy() for k, v in graph.items()}


def graph_with_end(graph, ending_nodes):
    result = _depth_one_copy(graph)
    if 'E' in graph:
        return result
    for end in ending_nodes:
        result[end]['E'] = Empty()
    return result


def _flipped(graph):
    """
    return a dict[key:state, value:set] where the value set contains all sources
    with a transition to the key state
    """
    result = {}
    for s, ts in graph.items():
        for d, t in ts.items():
            dict_entry_set_add(result, d, s)
    return result


def _ripout(graph, flipped, node):
    if not node in graph or not node in flipped:
        return

    if node in graph[node]:
        r_self = repeat(graph[node][node])
        del graph[node][node]
        flipped[node].remove(node)
    else:
        r_self = empty()

    # this updates flipped with the transitions created in the below loop
    flipped_additions = {}

    for n_in in flipped[node]:
        r_in = graph[n_in][node]
        for n_out, r_out in graph[node].items():
            r_new = concat(r_in, concat(r_self, r_out))
            if n_out in graph[n_in]:
                r_already = graph[n_in][n_out]
                r_new = alter(r_already, r_new)
            graph[n_in][n_out] = r_new

            dict_entry_set_add(flipped_additions, n_out, n_in)

    for n, add in flipped_additions.items():
        flipped[n].update(add)

    for _, ts in graph.items():
        if node in ts:
            del ts[node]
    for _, ts in flipped.items():
        if node in ts:
            ts.remove(node)

    del graph[node]
    del flipped[node]


def from_graph(source, starting_state, method):
    ending_nodes = [k for k, v in source.items() if method in v]
    regex_graph = graph(source, starting_state, ending_nodes)
    flipped = _flipped(regex_graph)
    all_nodes = source.keys()

    # TODO investigate why `reversed(all_nodes)` results in much longer regexes
    for node in all_nodes:
        _ripout(regex_graph, flipped, node)

    return regex_graph['S']['E']
