FROM python:3.12-slim

WORKDIR /app/AiAgent

COPY pyproject.toml uv.lock* README.md ./
COPY src ./src

RUN pip install -U pip && pip install uv && uv sync --frozen --no-dev

COPY . .
