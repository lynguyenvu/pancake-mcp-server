# STAGE 1: Build
FROM astral/uv:python3.11-bookworm-slim AS builder

# Set UV env variables
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_INSTALL_DIR=/opt/python

#  Create UV_PYTHON_INSTALL_DIR
RUN mkdir -p /opt/python

# Set working directory
WORKDIR /app

# Copy only the dependency files first to leverage caching
COPY ./pyproject.toml uv.lock ./

# Install the dependencies (this creates .venv automatically)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --frozen --no-install-project

# Copy the application code
COPY ./src/ ./src/

# Sync the environment with locked dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --frozen

# STAGE 2: Runtime
FROM python:3.11-slim AS runtime

# Set working directory
WORKDIR /app

#  Set environment variables
ENV PATH="/app/.venv/bin:/opt/python:$PATH" \
    PYTHONUNBUFFERED=1

#  Copy Python installation from builder
COPY --from=builder /opt/python /opt/python

#  Copy the app from builder
COPY --from=builder /app /app

# Set working directory to source
WORKDIR /app/src

# Expose port 8000 for service
EXPOSE 8000

# Run docker image as service
CMD ["uvicorn", "pancake_mcp.server:app", "--host", "0.0.0.0", "--port", "8000"]
