<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# Docker Build Segfault Troubleshooting Guide

This document provides solutions for the PDM segmentation fault issue
encountered during Docker builds.

## Problem Summary

The Docker build is failing with a segmentation fault during the PDM
dependency installation step:

```text
#13 1.980 Segmentation fault (core dumped)
#13 ERROR: process "/bin/sh -c pdm install --prod --no-isolation --no-self" \
   did not complete: exit code: 139
```

## Root Causes

The segmentation fault results from these factors:

1. **Memory constraints** during dependency resolution and compilation
2. **pycurl compilation issues** - requires specific system libraries
3. **PDM cache corruption** or conflicts
4. **Platform compatibility** issues with compiled packages
5. **Python version mismatches** between PDM expectations and container

## Solutions (Try in Order)

### Solution 1: Enhanced Dockerfile (Recommended)

The main `Dockerfile` includes comprehensive fixes:

- Added required system dependencies for pycurl compilation
- Implemented memory limits and timeouts
- Added fallback to pip installation
- Cleared caches to prevent corruption
- Added proper error handling

**Key changes:**

- Added `python3-dev` and `libffi-dev` packages
- Set memory limits with `ulimit -n 1024`
- Added timeout protection: `timeout 300 pdm install`
- Fallback to pip with exact dependency versions

### Solution 2: Pip-Based Dockerfile (Alternative)

If PDM continues to segfault, use the pip-based approach:

```bash
# Copy the alternative Dockerfile
cp docker-fixes/Dockerfile.pip-based Dockerfile

# Build with pip-based approach
docker build -t your-image:latest .
```

This bypasses PDM and uses pip directly for all dependency management.

### Solution 3: Debug and Identify Specific Issues

Run the debug script to identify the specific cause:

```bash
# Inside the container during build (add to Dockerfile temporarily)
COPY docker-fixes/debug-pdm.sh /tmp/
RUN chmod +x /tmp/debug-pdm.sh && /tmp/debug-pdm.sh
```

This will provide detailed information about:

- System resources and limits
- Python environment configuration
- PDM installation status
- Dependency conflicts
- Memory usage

### Solution 4: Manual PDM Configuration

If you need to stick with PDM, try these manual steps:

```dockerfile
# Clear all caches first
RUN rm -rf /root/.cache/pdm/* /tmp/pip-* ~/.cache/pip/*

# Set PDM environment variables
ENV PDM_IGNORE_SAVED_PYTHON=1
ENV PDM_USE_VENV=1
ENV PDM_PYTHON=/usr/local/bin/python3.11
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install with safer options
RUN ulimit -n 1024 && \
    timeout 300 pdm install --prod --no-isolation --no-self --no-lock --verbose
```

## Specific Package Issues

### pycurl Compilation

The `pycurl` package requires specific system libraries:

```dockerfile
RUN apt-get update && apt-get install -y \
    libcurl4-openssl-dev \
    libssl-dev \
    python3-dev \
    libffi-dev \
    build-essential \
    pkg-config
```

### Memory-Intensive Packages

Some packages require significant memory during compilation:

- Use `ulimit -v 2097152` to limit virtual memory
- Consider using pre-compiled wheels instead of source builds
- Check build logs for memory-related errors

## Environment Variables Reference

```bash
# PDM Configuration
PDM_IGNORE_SAVED_PYTHON=1      # Ignore saved Python interpreter
PDM_USE_VENV=1                 # Force virtual environment usage
PDM_PYTHON=/usr/local/bin/python3.11  # Explicit Python path

# Python Configuration
PYTHONUNBUFFERED=1             # Immediate stdout/stderr output
PYTHONDONTWRITEBYTECODE=1      # Don't create .pyc files

# Build Configuration
PIP_NO_CACHE_DIR=1             # Disable pip cache
PIP_DISABLE_PIP_VERSION_CHECK=1 # Skip pip version checks
```

## Testing the Fixes

### Local Testing

```bash
# Test the enhanced Dockerfile
docker build -t http-api-tool:test .

# Test the pip-based version
cp docker-fixes/Dockerfile.pip-based Dockerfile
docker build -t http-api-tool:pip-based .

# Run debug analysis
docker run --rm http-api-tool:test /tmp/debug-pdm.sh
```

### CI/CD Testing

Add these steps to your GitHub Actions workflow:

```yaml
- name: Build Docker image with enhanced error handling
  run: |
    docker build \
      --progress=plain \
      --build-arg BUILDKIT_INLINE_CACHE=1 \
      -t ${{ env.IMAGE_NAME }}:${{ github.sha }} .

- name: Test container functionality
  run: |
    docker run --rm ${{ env.IMAGE_NAME }}:${{ github.sha }} --help
```

## Fallback Strategy

If all PDM-based solutions fail, use this fallback:

1. **Use pip-based Dockerfile** (provided in `docker-fixes/Dockerfile.pip-based`)
2. **Pin exact versions** from `pdm.lock` in a `requirements.txt`
3. **Use multi-stage builds** to separate compilation from runtime
4. **Consider using conda** or other package managers if needed

## Prevention Strategies

### 1. Resource Monitoring

```dockerfile
# Add resource monitoring during build
RUN echo "Memory before PDM:" && free -h
RUN pdm install --prod --no-isolation --no-self
RUN echo "Memory after PDM:" && free -h
```

### 2. Incremental Installation

```dockerfile
# Install packages incrementally to isolate issues
RUN pdm add pycurl>=7.45.0
RUN pdm add typer[all]>=0.9.0
RUN pdm add certifi>=2025.6.15
RUN pdm add requests>=2.32.4
```

### 3. Cache Management

```dockerfile
# Regular cache cleanup
RUN rm -rf /root/.cache/pdm/* /tmp/pip-* ~/.cache/pip/* || true
```

## When to Use Each Solution

| Scenario | Recommended Solution |
|----------|---------------------|
| First-time segfault | Enhanced Dockerfile (Solution 1) |
| Persistent segfaults | Pip-based Dockerfile (Solution 2) |
| Need detailed diagnosis | Debug script (Solution 3) |
| Custom PDM setup required | Manual configuration (Solution 4) |
| Production deployment | Pip-based for stability |

## Support and Monitoring

### Build Logs Analysis

Look for these patterns in failed builds:

```text
Segmentation fault (core dumped)           # Memory/compilation issue
exit code: 139                            # Segfault exit code
Killed                                    # Out of memory
ResourceWarning                           # Resource leaks
```

### Health Checks

Add these to verify successful builds:

```dockerfile
# Verify installation
RUN python -m http_api_tool --help
RUN python -c "import pycurl, typer, certifi, requests; print('All imports successful')"
```

## Resources

- [PDM Documentation](https://pdm.fming.dev/)
- [Docker Multi-stage Builds](https://docs.docker.com/develop/dev-best-practices/dockerfile_best-practices/#use-multi-stage-builds)
- [Python Package Installation Issues](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/)
- [Memory Management in Docker](https://docs.docker.com/config/containers/resource_constraints/)
