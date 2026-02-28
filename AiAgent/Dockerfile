FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml uv.lock* /app/

RUN pip install -U pip && pip install uv && uv sync --frozen --no-dev

COPY . /app
