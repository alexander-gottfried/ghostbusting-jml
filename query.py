import tree_sitter_java
from tree_sitter import Language, Parser

JAVA = Language(tree_sitter_java.language())

# includes constants (i.e. 'final')
VARIABLES = JAVA.query(
        """
(local_variable_declaration
  declarator: (variable_declarator
    name: (identifier) @the-name
    )
)
        """
)

GHOST_VARIABLES = JAVA.query(
        """
(jml_ghost_declaration
  !final
  (variable_declarator
    name: (identifier) @the-name
    value: (_) @the-value))
        """
)

GHOST_CONSTANTS = JAVA.query(
        """
(jml_ghost_declaration
  "final"
  (variable_declarator
    name: (identifier) @the-name
    value: (_) @the-value))
        """
)

GHOST_ASSIGNMENTS = JAVA.query(
        """
(jml_set_statement
  (variable_declarator
    name: (identifier) @the-name
    value: (_) @the-value))
        """
)

METHODS = JAVA.query(
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

INVARIANTS = JAVA.query(
        """
(jml_invariant (_) @invariant)
        """
)
