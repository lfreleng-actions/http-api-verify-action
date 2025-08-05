<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# HTTP API Test Tool

An HTTP API testing tool for GitHub Actions and command-line usage.

This action performs HTTP requests with configurable verification of response
status, content, headers, and timing. Implemented in Python to modern PEP
standards, using Typer and pycurl. Avoids JSON escaping issues associated with
shell code implementations in GitHub actions.

## http-api-tool-docker

A containerized version of the HTTP API test tool with secure,
multi-architecture support.

### Docker Security Features

The Dockerfile implements these security best practices:

- **Version Pinning**: uv binary version is explicitly pinned (0.8.4)
- **Checksum Validation**: Downloads verify against SHA256 checksums to
  prevent MITM attacks
- **Multi-Architecture Support**: Automatically detects and downloads the
  correct binary for:
  - `linux/amd64` (Intel/AMD x86_64)
  - `linux/arm64` (Apple Silicon/ARM64)

### Building the Container

```bash
# Build for current platform
docker build -t http-api-tool .

# Build for specific platform
docker build --platform linux/amd64 -t http-api-tool .
docker build --platform linux/arm64 -t http-api-tool .

# Override uv version
docker build --build-arg UV_VERSION=0.8.5 -t http-api-tool .
```

### Container Usage

```bash
# Run the tool
docker run --rm http-api-tool --help

# Check uv version in container
docker run --rm --entrypoint=/usr/local/bin/uv http-api-tool --version
```

## Features

- **Supported HTTP Methods**: Supports GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS
- **Authentication**: Basic Auth via auth_string and custom headers support
- **Response Validation**: Status code, regex pattern matching, response time limits
- **Retry Logic**: Configurable exponential backoff with jitter
- **Dual Usage**: Works as both a CLI tool and GitHub Action
- **Robust Error Handling**: Detailed error messages and proper exit codes
- **JSON Safety**: Uses pycurl instead of shell commands to avoid escaping issues
- **SSL/TLS Support**: Full SSL verification with custom CA bundle support
- **Response Metrics**: Comprehensive timing and size measurements

## Usage

### As a GitHub Action

```yaml
- name: Test API Endpoint
  uses: ./
  with:
    url: 'https://api.example.com/health'
    http_method: 'GET'
    expected_http_code: '200'
    curl_timeout: '30'
    max_response_time: '10'
    retries: '3'
    initial_sleep_time: '2'

# Example with custom CA certificate
- name: Test API with Custom CA
  uses: ./
  with:
    url: 'https://internal-api.company.com/health'
    ca_bundle_path: '/path/to/ca-certificates.pem'
    expected_http_code: '200'
```

### As a CLI Tool

```bash
# Install PDM (if not already installed)
pip install --no-cache-dir pdm==2.24.2

# Install dependencies using PDM with hash verification
pdm install

# Basic usage
pdm run python -m http_api_tool test --url https://api.example.com/health

# Advanced usage
pdm run python -m http_api_tool test \
  --url https://api.example.com/users \
  --http-method POST \
  --request-body '{"name": "John", "email": "john@example.com"}' \
  --request-headers '{"Content-Type": "application/json"}' \
  --auth-string username:password \
  --expected-http-code 201 \
  --regex '"id":\s*\d+' \
  --curl-timeout 30 \
  --max-response-time 10 \
  --retries 3
```

## Inputs

<!-- markdownlint-disable MD013 -->

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `url` | URL of API server/interface to check | Yes | - |
| `auth_string` | Authentication string, colon separated username/password | No | - |
| `service_name` | Name of HTTP/HTTPS API service tested | No | `API Service` |
| `initial_sleep_time` | Time in seconds between API service connection attempts | No | `1` |
| `max_delay` | Max delay in seconds between retries | No | `30` |
| `retries` | Number of retries before declaring service unavailable | No | `3` |
| `expected_http_code` | HTTP response code to accept from the API service | No | `200` |
| `regex` | Verify server response with regular expression | No | - |
| `show_header_json` | Display response header as JSON in action output | No | `false` |
| `curl_timeout` | Max time in seconds for cURL to wait for a response | No | `5` |
| `http_method` | HTTP method to use (GET, POST, PUT, etc.) | No | `GET` |
| `request_body` | Data to send with POST/PUT/PATCH requests | No | - |
| `content_type` | Content type for the request body | No | `application/json` |
| `request_headers` | Custom HTTP headers sent in JSON format | No | - |
| `verify_ssl` | Verify SSL certificates | No | `true` |
| `ca_bundle_path` | Path to CA bundle file for SSL verification | No | - |
| `include_response_body` | Include response body in outputs (base64) | No | `false` |
| `follow_redirects` | Follow HTTP redirects | No | `true` |
| `max_response_time` | Max acceptable response time in seconds | No | `0` |
| `connection_reuse` | Reuse connections between requests | No | `true` |
| `debug` | Enables debugging output | No | `false` |
| `fail_on_timeout` | Fail if response time exceeds max_response_time | No | `false` |

<!-- markdownlint-enable MD013 -->

## Outputs

| Output | Description |
|--------|-------------|
| `time_delay` | Number of seconds waiting for service availability/failure |
| `response_http_code` | HTTP response code received from the server |
| `response_header_json` | HTTP response header as JSON |
| `response_header_size` | HTTP response header size in bytes |
| `response_body_size` | HTTP response body size in bytes |
| `regex_match` | Whether the regular expression matched the server reply |
| `response_body_base64` | Response body base64 encoded (when enabled) |
| `total_time` | Total time for the request in seconds |
| `connect_time` | Time to establish connection in seconds |
| `response_time_exceeded` | Whether response time exceeded max time |

## Authentication

### Authentication String

```yaml
with:
  auth_string: 'username:password'
```

### Custom Headers

```yaml
with:
  request_headers: |
    {
      "Authorization": "Bearer your-jwt-token",
      "X-API-Key": "your-api-key",
      "X-Custom-Header": "value"
    }
```

## Examples

### Simple Health Check

```yaml
- name: Health Check
  uses: ./
  with:
    url: 'https://api.example.com/health'
    expected_http_code: '200'
```

### POST with JSON Data

```yaml
- name: Create User
  uses: ./
  with:
    url: 'https://api.example.com/users'
    http_method: 'POST'
    request_headers: '{"Content-Type": "application/json"}'
    request_body: '{"name": "John Doe", "email": "john@example.com"}'
    expected_http_code: '201'
    regex: '"id":\s*\d+'
```

### Authenticated Request with Retry

```yaml
- name: Get Protected Resource
  uses: ./
  with:
    url: 'https://api.example.com/protected'
    request_headers: '{"Authorization": "Bearer ${{ secrets.API_TOKEN }}"}'
    retries: '5'
    initial_sleep_time: '2'
    curl_timeout: '30'
```

### Response Validation

```yaml
- name: Test API Response
  uses: ./
  with:
    url: 'https://api.example.com/status'
    regex: '"status":\s*"ok"'
    max_response_time: '5'
```

## Error Handling

The action provides detailed error messages for common scenarios:

- **Connection Errors**: Network connectivity issues
- **Timeout Errors**: Request or connection timeouts
- **Authentication Errors**: Invalid credentials
- **Validation Errors**: Unexpected status codes or response patterns
- **SSL Errors**: Certificate verification failures

## Development

### Running Tests

```bash
# Install PDM (if not already installed)
pip install --no-cache-dir pdm==2.24.2

# Install development dependencies with hash verification
pdm install --dev

# Run tests
pdm run pytest tests/ -v

# Run with coverage
pdm run pytest tests/ --cov=http_api_tool --cov-report=html
```

### Pre-commit Hooks

```bash
# Install pre-commit (included in dev dependencies)
pdm install --dev

# Install hooks
pdm run pre-commit install

# Run hooks manually
pdm run pre-commit run --all-files
```

### Docker Requirements Management

The Docker image uses a **dynamic requirements generation** approach where the
Docker build process generates the `requirements-docker.txt` file to
ensure correct platform compatibility.

If you need to manually regenerate for local development:

```bash
# Regenerate requirements-docker.txt with all dependencies and hashes
python3 scripts/generate_requirements.py \
  --platform linux_x86_64 \
  --python-version 311 \
  --output requirements-docker.txt \
  --comment "PDM and all its dependencies for Linux x86_64 platform" \
  pdm==2.24.2

# Or specify a different PDM version
python3 scripts/generate_requirements.py \
  --platform linux_x86_64 \
  --python-version 311 \
  --output requirements-docker.txt \
  --comment "PDM and all its dependencies for Linux x86_64 platform" \
  pdm==2.26.0

# Test the Docker build
docker build . --platform linux/arm64 -t http-api-tool-test
```

The `requirements-docker.txt` file contains:

- PDM and all its transitive dependencies
- SHA256 hashes for Linux ARM64 platform
- Security protection against supply chain attacks
- Ensures reproducible Docker builds

**When to regenerate:**

- Updating PDM version in the project
- Docker build failures with hash verification errors
- Setting up the project for the first time
- After changes to `pyproject.toml` affecting PDM dependencies

### Local Development

```bash
# Test CLI functionality
pdm run python -m http_api_tool test --help

# Test against local server
python -m http.server 8000 &
pdm run python -m http_api_tool test --url http://localhost:8000
```

### Testing with Local go-httpbin Service

For testing HTTP API functionality, use the local go-httpbin service instead of
external services:

```bash
# Start local go-httpbin service
make setup-go-httpbin

# Test Docker container against local service
make test-with-httpbin

# Manual testing with local service
docker run --rm --network host \
  -v $(PWD)/mkcert-ca.pem:/tmp/mkcert-ca.pem:ro \
  http-api-tool \
  test \
  --url https://localhost:8080/get \
  --http-method GET \
  --expected-http-code 200 \
  --ca-bundle-path /tmp/mkcert-ca.pem

# Stop local service when done
make stop-go-httpbin
```

The local go-httpbin service provides all the same endpoints as httpbin.org
but runs locally for faster, more reliable testing.

The `setup-go-httpbin` target automatically:

- Installs mkcert if not present
- Creates a local Certificate Authority (CA)
- Generates SSL certificates for localhost
- Saves the CA certificate as `mkcert-ca.pem` in the project root
- Starts the go-httpbin service with proper HTTPS support

This ensures that SSL certificate validation remains enabled for all tests,
providing a more realistic testing environment.

## Migration from Shell Version

If you're migrating from the original shell-based implementation:

1. **Input Compatibility**: Most inputs remain the same with updated naming
2. **Output Compatibility**: Outputs are similar with enhanced information
3. **Behavior Changes**:
   - Better JSON handling (no more escaping issues)
   - More robust error reporting
   - Improved retry logic with exponential backoff
   - Better SSL/TLS handling
   - Enhanced debugging output
   - More comprehensive response metrics

## Migration to PDM

This project uses PDM (Python Dependency Manager) for dependency management:

### For Development

Install dependencies with:

```bash
pip install --no-cache-dir pdm==2.24.2
pdm install --dev
```

Run unit tests with:

```bash
pdm run pytest tests/ -v
```

## Requirements

- Python 3.10+
- PDM (Python Dependency Manager)
- pycurl
- typer (for CLI usage)

PDM manages dependencies, with hash-verified lock files for reproducible builds.

## License

Apache-2.0 License. See [LICENSE](LICENSE) for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run pre-commit hooks
6. Submit a pull request
