FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]" 2>/dev/null || pip install --no-cache-dir -e .

# Copy source
COPY src/ ./src/

EXPOSE 8000

CMD ["uvicorn", "pancake_mcp.server:app", "--host", "0.0.0.0", "--port", "8000"]
