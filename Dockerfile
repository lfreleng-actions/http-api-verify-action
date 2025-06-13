# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

# Multi-stage build for optimized caching and smaller final image
FROM python:3.11-slim@sha256:7a3ed1226224bcc1fe5443262363d42f48cf832a540c1836ba8ccbeaadf8637c AS base

# Install system dependencies and create app user in a single layer
RUN apt-get update && apt-get install -y \
    build-essential \
    ca-certificates \
    curl \
    docker.io \
    iproute2 \
    libcurl4-openssl-dev \
    libssl-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && groupadd -r appuser \
    && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Build stage for dependencies
FROM base AS deps

# Copy requirements file for PDM installation with hash verification
COPY requirements-docker.txt ./

# Upgrade pip and install PDM with hash verification using pip cache
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install -r requirements-docker.txt

# Copy project files and lock file for dependency resolution
COPY pyproject.toml pdm.lock ./

# Install dependencies only (without the package itself) using PDM cache
RUN --mount=type=cache,target=/root/.cache/pdm \
    pdm install --prod --no-isolation --no-self

# Production stage
FROM base AS production

# Copy the virtual environment from deps stage
COPY --from=deps /app/.venv /app/.venv

# Copy source code and project configuration
COPY src/ src/
COPY pyproject.toml ./

# Fix the python symlinks (PDM creates circular symlinks) and install the package
RUN rm -f /app/.venv/bin/python /app/.venv/bin/python3 /app/.venv/bin/python3.11 && \
    ln -sf /usr/local/bin/python3.11 /app/.venv/bin/python && \
    ln -sf /app/.venv/bin/python /app/.venv/bin/python3 && \
    ln -sf /app/.venv/bin/python /app/.venv/bin/python3.11 && \
    VENV_SITE_PACKAGES=$(/app/.venv/bin/python -c "import site; print(site.getsitepackages()[0])") && \
    cp -r /app/src/http_api_tool "$VENV_SITE_PACKAGES/" && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Activate the virtual environment permanently for the container
ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/.venv"

# Set entrypoint to use the installed package from site-packages
ENTRYPOINT ["/app/.venv/bin/python", "-m", "http_api_tool"]
