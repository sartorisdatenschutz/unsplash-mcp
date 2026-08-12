FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MCP_TRANSPORT=http \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8000

WORKDIR /app

RUN groupadd --system mcp && useradd --system --gid mcp --home-dir /app mcp

COPY pyproject.toml README.md ./
RUN pip install --upgrade pip && pip install .

COPY --chown=mcp:mcp server.py ./

USER mcp

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import socket; s=socket.create_connection(('127.0.0.1', 8000), 3); s.close()" || exit 1

CMD ["python", "server.py"]
