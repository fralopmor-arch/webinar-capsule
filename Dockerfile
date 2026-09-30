# Use official Python 3.12 slim image
FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies (ffmpeg required for audio extraction/whisper)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv from official astral image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy dependency specifications first to leverage Docker layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies into virtual environment without building the root project yet
RUN uv sync --frozen --no-install-project --no-dev --no-cache

# Copy application source code (including README.md, src/, and app.py)
COPY . .

# Finalize sync to install the local project package
RUN uv sync --frozen --no-dev --no-cache

# Expose default Streamlit port
EXPOSE 8501

ENV PORT=8501 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    PATH="/app/.venv/bin:$PATH"

# Launch Streamlit app, dynamically respecting $PORT injected by cloud providers (Render, Railway, etc.)
CMD ["sh", "-c", "streamlit run app.py --server.port=${PORT:-8501} --server.address=0.0.0.0"]
