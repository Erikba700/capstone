# Load environment variables from .env.local
ENV_FILE ?= .env
include $(shell [ -f $(ENV_FILE) ] && echo $(ENV_FILE) || echo .env.local)
export


.PHONY: dev
dev:
	uv run -m app.main --mode dev

.PHONY: fmt
fmt:
	uv run ruff format .
	uv run ruff check . --fix
	uv run mypy .
	uv run ruff check .

.PHONY: test
test:
	uv run pytest -m unit -vv
