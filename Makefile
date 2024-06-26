SRC := $(shell find ./src -name "*.py" )
SRC_MARKER := .local_install

local:				$(SRC_MARKER)

$(SRC_MARKER):		$(SRC)
					pip install .
					@touch $(SRC_MARKER)

build:				clean
					python -m build

dev:				build
					twine upload --repository testpypi dist/*

prod:				build
					twine upload dist/*

test:				clean local
					pytest

clean:
					rm -rf dist

.PHONY: local dev prod test clean
