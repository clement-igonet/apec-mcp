FROM ghcr.io/astral-sh/uv:python3.12-slim

WORKDIR /app

# Install dependencies (cached layer)
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev

# Copy source
COPY src/ src/

EXPOSE 8080

CMD ["uv", "run", "apec-mcp"]
