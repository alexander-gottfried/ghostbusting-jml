import tree_sitter_java
from tree_sitter import Language, Parser

JAVA = Language(tree_sitter_java.language())


def parse(src_path):
    parser = Parser(JAVA)
    with open(src_path, 'rb') as file:
        source = file.read()
        def read(byte_pos, _):
            return source[byte_pos : byte_pos + 1]
        tree = parser.parse(read, encoding='utf8')

    #print(tree.root_node)
    
    ghost_captures = QUERY_GHOSTS.captures(tree.root_node)
    final_ghost_captures = QUERY_GHOST_CONSTANTS.captures(tree.root_node)
    #print(ghost_captures)

    def to_str(node):
        return source[node.start_byte : node.end_byte]

    def aux(captures):
        for name, value in zip(captures['the-name'], captures['the-value']):
            name, value = map(to_str, (name, value))
            print(f'{name}: {value}')

    aux(ghost_captures)
    aux(final_ghost_captures)



QUERY_GHOSTS = JAVA.query(
        """
(jml_ghost_declaration
  !final
  (variable_declarator
    name: (identifier) @the-name
    value: (_) @the-value))
        """
)

QUERY_GHOST_CONSTANTS = JAVA.query(
        """
(jml_ghost_declaration
  "final"
  (variable_declarator
    name: (identifier) @the-name
    value: (_) @the-value))
        """
)

QUERY_ASSIGNMENTS = JAVA.query(
        """
(jml_set_statement
  (variable_declarator
    name: (identifier) @the-name
    value: (_) @the-value))
        """
)

QUERY_METHODS = JAVA.query(
        """
(method_declaration
  (jml_contract
    [
      (jml_requires (_) @precondition)
      (jml_ensures (_) @postcondition)
    ])+
  name: (identifier) @method-name)
        """
)

QUERY_INVARIANTS = JAVA.query(
        """
(jml_invariant (_) @invariant)
        """
)



"""
we need to extract:
    ghost variables
    and their initial states:

    set statements

    contracts + method names
        requires
        ensures
        (that's it for now)

    invariants

"""
