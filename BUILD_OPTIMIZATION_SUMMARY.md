<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- SPDX-FileCopyrightText: 2025 The Linux Foundation -->

# Build and Test Optimization Summary

This document summarizes the caching and optimization improvements implemented
for the HTTP API Tool Docker project to reduce build/test cycle times.

## Implemented Optimizations

### 1. Dockerfile Optimizations (`Dockerfile`)

**Multi-stage builds** for better layer caching:

- Separate `base`, `deps`, and `production` stages
- Dependencies installed in separate stage for better caching
- Build dependencies cached separately from runtime

**Docker build cache mounts**:

- `--mount=type=cache,target=/root/.cache/pip` for pip caching
- `--mount=type=cache,target=/root/.cache/pdm` for PDM caching
- Leverages BuildKit cache mounts for persistent package caches

**Security improvements**:

- Non-root user execution
- Minimal final image size through multi-stage builds

### 2. GitHub Container Registry Integration

**New workflow**: `.github/workflows/docker-build-publish.yaml`

- Builds and publishes containers to GHCR
- Advanced caching strategy using GitHub Actions cache and registry cache
- Supports two platforms (linux/amd64, linux/arm64)
- Automatic tagging for branches, PRs, and releases
- Security scanning with Trivy
- SBOM and provenance attestation

**Registry caching**:

```yaml
cache-from: |
  type=gha
  type=registry,ref=ghcr.io/org/repo:buildcache
cache-to: |
  type=gha,mode=max
  type=registry,ref=ghcr.io/org/repo:buildcache,mode=max
```

### 3. Optimized Build/Test Workflows

**Enhanced build-test workflow**: `.github/workflows/build-test-optimized.yaml`

- Python setup with pip caching: `cache: 'pip'`
- Docker builds using pre-built images from registry
- Parallel job execution where possible
- Shared Docker images between jobs

**Workflow structure**:

1. `python-build` - Build Python packages with caching
2. `docker-build` - Build and cache Docker image
3. `python-tests` - Run tests with cached dependencies
4. `docker-test` - Test Docker functionality using cached image

### 4. Makefile Enhancements (`Makefile`)

**Pip caching**:

```makefile
install-pdm: ## Install PDM package manager with caching
 pip install --cache-dir ~/.cache/pip pdm==2.24.2
```

**PDM caching**:

```makefile
install-dev: ## Install development dependencies using PDM with caching
 pdm install --cache-dir ~/.cache/pdm -G dev -G test
```

**Docker BuildKit caching**:

```makefile
docker-build: ## Build Docker image with caching
 DOCKER_BUILDKIT=1 docker build \
  --cache-from http-api-tool:latest \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  -t http-api-tool .
```

### 5. Build Context Optimization (`.dockerignore`)

**Reduced build context size** by excluding:

- Test files and coverage reports
- Documentation files
- IDE/editor files
- Git history and GitHub Actions
- Python cache and build artifacts
- Development tools (Makefile, etc.)

### 6. GitHub Actions Refactoring (`.github/actions/go-httpbin`)

**New reusable action** for go-httpbin setup:

- Extracted duplicated go-httpbin setup code into a dedicated action at
  `.github/actions/go-httpbin`
- Modular design with configurable inputs (container name, port, network mode,
  debug level)
- Consistent SSL certificate generation using mkcert across all test jobs
- Standardized output format providing service URLs, CA certificates, and
  network information

**Action inputs**:

```yaml
inputs:
  container-name: 'go-httpbin'     # Container name
  port: '8080'                     # Service port
  use-host-network: 'false'        # Network mode
  debug: 'false'                   # Debug output
  wait-timeout: '60'               # Service readiness timeout
```

**Action outputs**:

```yaml
outputs:
  service-url: 'https://HOST:PORT'           # Service base URL
  host-gateway-ip: '172.17.0.1'             # Docker gateway IP
  ca-cert-path: 'mkcert-ca.pem'            # CA certificate path (relative to workspace)
  container-name: 'go-httpbin'              # Created container name
```

### Testing workflow improvements**

- Eliminated ~200 lines of duplicated code across 5 test jobs
- Consistent SSL setup and certificate handling
- Standardized error handling and service validation
- Better maintainability and reusability for future tests

## Expected Performance Improvements

### Build Time Reductions

1. **First-time builds**: 20-30% faster due to optimized Dockerfile layering
2. **Later builds**: 60-80% faster due to:
   - Docker layer caching
   - Registry cache hits
   - Cached pip/PDM packages
   - Smaller build context

### CI/CD Pipeline Improvements

1. **PR workflows**: Use pre-built base images from main branch
2. **Dependency caching**: Persistent across workflow runs
3. **Parallel execution**: Jobs run concurrently where possible
4. **Registry reuse**: Pull existing images instead of rebuilding
5. **Code reusability**: Modular go-httpbin action reduces maintenance overhead

### Development Experience

1. **Local development**: Makefile targets use local caching
2. **Faster iterations**: Cached dependencies and Docker layers
3. **Reduced network usage**: Less package downloading
4. **Easier testing**: Consistent test environment setup across all jobs

## Usage Instructions

### For Pull Requests

The optimized workflow automatically:

1. Attempts to pull pre-built image from registry
2. Falls back to local build if not available
3. Uses GitHub Actions cache for dependencies
4. Publishes image for later jobs

### For Main Branch

1. Full Docker build with multi-platform support
2. Push to GitHub Container Registry
3. Update cache layers for future builds
4. Security scanning and attestation

### Local Development

```bash
# Use cached builds
make docker-build

# Full development setup with caching
make bootstrap

# Run tests with cached dependencies
make test
```

## Monitoring and Maintenance

- **Cache hit rates**: Check in GitHub Actions logs
- **Registry storage**: Images auto-expire based on usage
- **Security scanning**: Automated Trivy scans on published images
- **Build times**: Track in workflow summaries

## Next Steps

1. Check cache effectiveness in real workflows
2. Tune cache strategies based on usage patterns
3. Consider dependency pre-heating for even faster builds
4. Set up cache cleanup policies for storage management
