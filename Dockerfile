# Dockerfile for LiveKit Voice Agent
# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.13
FROM python:${PYTHON_VERSION}-slim

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/develop/develop-images/dockerfile_best-practices/#user
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/home/appuser" \
    --shell "/sbin/nologin" \
    --uid "${UID}" \
    appuser

# Install system dependencies including ffmpeg for audio processing
RUN apt-get update && \
    apt-get install -y \
    gcc \
    python3-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster Python dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Create app directory and cache directories
USER appuser
WORKDIR /home/appuser

# Copy dependency files first for better caching
COPY --chown=appuser:appuser pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --frozen --no-dev

# Copy application code
COPY --chown=appuser:appuser . .

# Download any required models (e.g., Silero VAD)
RUN uv run python main.py download-files

# Expose LiveKit agent port (typically 8080 or 8081)
EXPOSE 8080

# Run the application
CMD ["uv", "run", "python", "main.py", "start"]