PARSER=tree-sitter-java
VENV=.venv

all: venv

parser: $(PARSER)/grammar.js
	cd $(PARSER) && \
	tree-sitter generate && \
	tree-sitter build
	$(VENV)/bin/pip install --force-reinstall ./$(PARSER)

venv: parser
	mkdir $(VENV)
	python -m venv $(VENV)
	$(VENV)/bin/pip install -r requirements.txt
