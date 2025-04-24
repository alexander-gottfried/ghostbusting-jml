PARSER=tree-sitter-java_jml_subset
VENV=.venv

all: venv

parser: $(PARSER)/grammar.js
	cd $(PARSER) && \
	tree-sitter generate && \
	tree-sitter build

venv: parser
	mkdir $(VENV)
	python -m venv $(VENV)
	$(VENV)/bin/pip install -r requirements.txt
