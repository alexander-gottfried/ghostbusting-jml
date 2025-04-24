package tree_sitter_java_jml_subset_test

import (
	"testing"

	tree_sitter "github.com/tree-sitter/go-tree-sitter"
	tree_sitter_java_jml_subset "github.com/tree-sitter/tree-sitter-java_jml_subset/bindings/go"
)

func TestCanLoadGrammar(t *testing.T) {
	language := tree_sitter.NewLanguage(tree_sitter_java_jml_subset.Language())
	if language == nil {
		t.Errorf("Error loading JavaJmlSubset grammar")
	}
}
