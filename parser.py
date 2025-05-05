import dataclasses

import tree_sitter_java
import tree_sitter as ts

import query
import expression as expr


JAVA = ts.Language(tree_sitter_java.language())

@dataclasses.dataclass
class Source:
    tree: ts.Tree
    code: str


def _parse_source(source_file_path):
    parser = ts.Parser(JAVA)
    with open(source_file_path, 'rb') as file:
        code = file.read()
        def read(byte_pos, _):
            return code[byte_pos : byte_pos + 1]
        tree = parser.parse(read, encoding='utf8')
    return Source(tree, code)


def _node_to_str(node, code: Source):
    return code[node.start_byte : node.end_byte]


def _captured_strs(captures, code, key='the-name'):
    for capture in captures[key]:
        yield _node_to_str(capture, code)


@dataclasses.dataclass
class Program:
    normal: set[str]
    ghost_constants: dict[str, int]
    ghosts: dict[str, int]

def program_from_tree(source: Source):
    root = source.tree.root_node

    normal_captures = query.VARIABLES.captures(root)
    normal = set(_captured_strs(normal_captures, source.code))
    print(normal)

    def to_str(node):
        return source.code[node.start_byte : node.end_byte].decode('utf-8')

    def aux(query):
        captures = query.captures(root)
        names = _captured_strs(captures, source.code, key='the-name')
        values = map(lambda x: expr.parse_expression(x, to_str), captures['the-value'])
        return dict(zip(names, values))

    ghost_variables = aux(query.GHOST_VARIABLES)
    ghost_constants = aux(query.GHOST_CONSTANTS)

    print(ghost_variables)
    print(ghost_constants)


def parse(src_path):
    parser = ts.Parser(JAVA)
    with open(src_path, 'rb') as file:
        source_code = file.read()
        def read(byte_pos, _):
            return source_code[byte_pos : byte_pos + 1]
        tree = parser.parse(read, encoding='utf8')

    #print(tree.root_node)
    
    source = Source(tree, source_code)
    variables = program_from_tree(source)

    import expression as e

    def to_str(node):
        return source.code[node.start_byte : node.end_byte].decode('utf-8')

    cursor = tree.walk()
    cursor.goto_first_child()
    while cursor.node.type != 'jml_invariant':
        cursor.goto_next_sibling()
    cursor.goto_first_child()
    cursor.goto_next_sibling()
    print(cursor.node.type)

    testo = e.parse_expression(cursor.node, to_str)
    print(testo)
