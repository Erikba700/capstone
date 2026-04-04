# syntax=docker/dockerfile:1

FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:0.9.22 /uv /uvx /bin/
WORKDIR /project
COPY pyproject.toml /project/pyproject.toml
COPY uv.lock /project/uv.lock

RUN uv sync --locked --compile-bytecode
COPY app /project/app
CMD ["/project/.venv/bin/python", "-m", "app.main", "--mode", "dev"]
