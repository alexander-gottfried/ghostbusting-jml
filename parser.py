import tree_sitter_java_jml_subset
from tree_sitter import Language, Parser

RJAVA = Language(tree_sitter_java_jml_subset.language())


def parse(src_path):
    parser = Parser(RJAVA)
    with open(src_path, 'rb') as file:
        source = file.read()
        def read(byte_pos, _):
            return source[byte_pos : byte_pos + 1]
        tree = parser.parse(read, encoding='utf8')
        print(tree.root_node)
