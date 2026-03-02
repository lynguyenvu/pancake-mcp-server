FROM python:3.11-slim

WORKDIR /app

# Create pip configuration for timeout handling
COPY pip.conf /etc/pip.conf

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY src/ ./src/

# Install pip with timeout configuration
ENV PIP_TIMEOUT=600
ENV PIP_RETRIES=5
ENV PIP_DEFAULT_TIMEOUT=100

RUN pip install --upgrade pip setuptools wheel

# Install dependencies with timeout handling and retries
# Use a step-by-step approach to handle potential CDN timeouts
RUN pip install --no-cache-dir --timeout=600 --retries=5 --default-timeout=100 \
    fastmcp>=2.3.0 httpx>=0.27.0 uvicorn[standard]>=0.30.0 pydantic>=2.7.0 \
    python-dotenv>=1.0.0 aiohttp>=3.8.0

# Install image processing dependencies with timeout handling
RUN pip install --no-cache-dir --timeout=600 --retries=5 --default-timeout=100 \
    Pillow>=10.0.0 opencv-python-headless>=4.8.0.0 pytesseract>=0.3.10 easyocr>=1.7.0

# Install dev dependencies with timeout handling
RUN pip install --no-cache-dir --timeout=600 --retries=5 --default-timeout=100 \
    pytest>=8.0.0 pytest-asyncio>=0.23.0 respx>=0.21.0 pytest-httpx>=0.30.0

# Install the package itself with timeout handling
RUN pip install --no-cache-dir --timeout=600 --retries=5 --default-timeout=100 -e .

# Set working directory to source
WORKDIR /app/src

EXPOSE 8000

CMD ["uvicorn", "pancake_mcp.server:app", "--host", "0.0.0.0", "--port", "8000"]
