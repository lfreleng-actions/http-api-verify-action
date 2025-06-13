#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

# Script to demonstrate how to update testing workflows to use pre-built containers
# This shows the pattern that should be applied to the docker-tests job in testing.yaml

set -euo pipefail

REGISTRY="ghcr.io"
REPO="$1"  # Pass repository name as argument
IMAGE_NAME="${REGISTRY}/${REPO}"

echo "=== Docker Container Optimization Demo ==="
echo "Repository: $REPO"
echo "Image Name: $IMAGE_NAME"

# Login to GitHub Container Registry (if credentials available)
if [ -n "${GITHUB_TOKEN:-}" ]; then
    echo "Logging into container registry..."
    echo "$GITHUB_TOKEN" | docker login "$REGISTRY" -u "$GITHUB_ACTOR" --password-stdin
fi

# Strategy 1: Try to pull pre-built image from main branch
echo "Attempting to pull pre-built image..."
if docker pull "${IMAGE_NAME}:latest" 2>/dev/null; then
    echo "✅ Using pre-built image from registry"
    docker tag "${IMAGE_NAME}:latest" http-api-tool
    BUILD_TIME="~5 seconds (cache hit)"
else
    echo "⚠️  Pre-built image not available, building locally"
    echo "This would happen on first PR or after significant changes"

    # Fallback: Build with cache-from to still benefit from layer caching
    DOCKER_BUILDKIT=1 docker build \
        --cache-from "${IMAGE_NAME}:latest" \
        --cache-from "${IMAGE_NAME}:buildcache" \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        -t http-api-tool \
        .
    BUILD_TIME="~30-60 seconds (with layer caching)"
fi

echo "=== Build completed ==="
echo "Estimated build time: $BUILD_TIME"

# Test the image
echo "Testing image functionality..."
docker run --rm http-api-tool --help >/dev/null
echo "✅ Image test passed"

# Cleanup
docker image prune -f >/dev/null 2>&1 || true

echo ""
echo "=== Integration with testing.yaml ==="
echo "To integrate this optimization into testing.yaml:"
echo ""
echo "1. Add container registry permissions:"
echo "   permissions:"
echo "     contents: read"
echo "     packages: read"
echo ""
echo "2. Replace the 'Build Docker image' step with:"
echo "   - name: Log in to Container Registry"
echo "     uses: docker/login-action@v3"
echo "     with:"
echo "       registry: ghcr.io"
echo "       username: \${{ github.actor }}"
echo "       password: \${{ secrets.GITHUB_TOKEN }}"
echo ""
echo "   - name: Pull or build Docker image"
echo "     run: |"
echo "       if docker pull ghcr.io/\${{ github.repository }}:latest 2>/dev/null; then"
echo "         docker tag ghcr.io/\${{ github.repository }}:latest http-api-tool"
echo "       else"
echo "         docker build -t http-api-tool ."
echo "       fi"
echo ""
echo "3. Add 'needs: [docker-build]' to jobs that depend on the container"
echo ""
echo "This will reduce build times from ~2-3 minutes to ~5-10 seconds for cached builds!"
