SRC := $(shell find ./src -name "*.py" )
SRC_MARKER := .local_install

local:				$(SRC_MARKER)

$(SRC_MARKER):		$(SRC)
					uv sync --dev
					@touch $(SRC_MARKER)

build:				clean
					uv build

check:				build
					uv run --with api42lib --no-project -- python -c "from api42lib import IntraAPIClient"

dev:				build check
					uv publish --index testpypi --username __token__ --password "$(PYPI_TOKEN_TEST)"

prod:				build check
					uv publish --username __token__ --password "$(PYPI_TOKEN_PROD)"

test:				clean local check
					uv run pytest

clean:
					rm -rf dist build *.egg-info src/*.egg-info *__pycache__

.PHONY: local dev prod test clean
