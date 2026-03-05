# STAGE 1: Build
FROM astral/uv:python3.11-bookworm-slim AS builder

# Set UV env variables
# Disable Python downloads, because we want to use the system interpreter
# across both images. If using a managed Python version, it needs to be
# copied from the build image into the final image.
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

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
# It is important to use the image that matches the builder, as the path to the
# Python executable must be the same, e.g., using `python:3.10-slim-bookworm`
# will fail.
FROM python:3.11-slim-bookworm AS runtime

# Install Tesseract OCR and Vietnamese language pack
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-vie \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

#  Copy the app from builder
COPY --from=builder /app /app

# Clean up bytecode cache to reduce image size
RUN find /app/.venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Set working directory to source
WORKDIR /app/src

# Expose port 8000 for service
EXPOSE 8000

# Add the virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Run docker image as service
CMD ["uvicorn", "pancake_mcp.server:app", "--host", "0.0.0.0", "--port", "8000"]
