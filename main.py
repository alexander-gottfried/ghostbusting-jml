#! ./bin/python

import collections
import itertools
import functools

import cats
import regex
import boolexpr
import graph
import cases

#import tree_sitter_reduced_java
#from tree_sitter import Language, Parser

"""
def main():
    RJAVA = Language(tree_sitter_reduced_java.language())
    parser = Parser(RJAVA)
    with open('../supersimple/example.rjava', 'rb') as file:
        source = file.read()
        def read(byte_pos, _):
            return source[byte_pos : byte_pos + 1]
        tree = parser.parse(read, encoding='utf8')
        print(tree.root_node)
"""


def main():
    variables, possible_states, initital_state, methods = cases.casino()
    g = graph.from_program(
            possible_states,
            methods)
    print(g)
    r, f = cats.something(g)
    print(r)
    print(f)

    method_names = list(methods.keys())

    cat = cats.from_graph(g, method_names, initital_state)

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


if __name__ == '__main__':
    main()
