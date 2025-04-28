PARSER=tree-sitter-java
VENV=.venv

all: venv

gen_parser: $(PARSER)/grammar.js
	cd $(PARSER) && \
	tree-sitter generate && \
	tree-sitter build

parser: gen_parser
	$(VENV)/bin/pip install --force-reinstall ./$(PARSER)

venv: gen_parser
	mkdir $(VENV)
	python -m venv $(VENV)
	$(VENV)/bin/pip install -r requirements.txt
