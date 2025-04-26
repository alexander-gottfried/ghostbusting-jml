#! .venv/bin/python
import sys

import collections
import itertools
import functools

import cats
import regex
import boolexpr
import graph
import cases


def main():
    variables, possible_states, initital_state, methods =\
            cases.simpler_casino_with_invariant_appended()
    g = graph.from_program(
            possible_states,
            methods)
    print(g)
    r, f = cats.something(g)
    print(r)
    print(f)

    method_names = list(methods.keys())

    cat = cats.naive_pretrace_from_graph(g, method_names, initital_state)

    for method in method_names:
        print(f'\n{method=}\n')
        print(f'naive cat:\n {cat[method]}\n')
        r = regex.from_graph(g, initital_state, method)
        print(f'regex:\n {r}\n')
        c = regex.collapse_same_prefix(r)
        print(f'simpler:\n {c}\n')
        m = list(map(str, regex.must_contain(r)))
        print(f'must contain:\n {m}\n')
        l = [str(x) for x in regex.last_calls(r)]
        print(f'traces end with:\n {l}\n')

from boolexpr import *

def main():
    import parser
    example = './example.rjava'
    parser.parse(example)


if __name__ == '__main__':
    main()
