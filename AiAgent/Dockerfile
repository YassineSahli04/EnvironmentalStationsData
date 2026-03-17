FROM python:3.12-slim

WORKDIR /app/AiAgent

RUN apt-get update && apt-get install -y curl ca-certificates gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \
    | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" \
    > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update && apt-get install -y nodejs \
    && npm install -g excel-csv-mcp-server \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock* README.md ./
COPY src ./src

RUN pip install -U pip && pip install uv && uv sync --frozen --no-dev

COPY . .

ENV PATH="/app/AiAgent/.venv/bin:$PATH"

EXPOSE 8001

CMD ["uvicorn", "agent.Api:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "8"]