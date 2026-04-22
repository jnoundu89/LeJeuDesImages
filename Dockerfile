FROM python:3.12-slim

WORKDIR /app

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install dependencies first (cache layer)
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

# Copy application code
COPY app.py config.yaml ./
COPY models/ models/
COPY routes/ routes/
COPY templates/ templates/
COPY static/ static/

# Data directory (mount via volume)
RUN mkdir -p data

EXPOSE 5000

CMD ["uv", "run", "python", "app.py"]
