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

## Features

- **Supported HTTP Methods**: Supports GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS
- **Authentication**: Basic Auth, Bearer Token, API Key, and custom headers
- **Response Validation**: Status code, regex pattern matching, response time limits
- **Retry Logic**: Configurable exponential backoff with jitter
- **Dual Usage**: Works as both a CLI tool and GitHub Action
- **Robust Error Handling**: Detailed error messages and proper exit codes
- **JSON Safety**: Uses pycurl instead of shell commands to avoid escaping issues

## Usage

### As a GitHub Action

```yaml
- name: Test API Endpoint
  uses: ./
  with:
    url: 'https://api.example.com/health'
    method: 'GET'
    expected_status: '200'
    timeout: '30'
    max_time: '10'
    retry_attempts: '3'
    retry_delay: '2'
```

### As a CLI Tool

```bash
# Install PDM (if not already installed)
pip install --no-cache-dir pdm==2.24.2

# Install dependencies using PDM with hash verification
pdm install

# Basic usage
pdm run python -m http_api_tool --url https://api.example.com/health

# Advanced usage
pdm run python -m http_api_tool \
  --url https://api.example.com/users \
  --method POST \
  --data '{"name": "John", "email": "john@example.com"}' \
  --headers 'Content-Type: application/json' \
  --basic-auth username:password \
  --expected-status 201 \
  --regex-pattern '"id":\s*\d+' \
  --timeout 30 \
  --max-time 10 \
  --retry-attempts 3
```

## Inputs

<!-- markdownlint-disable MD013 -->

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `url` | The URL to request | Yes | - |
| `method` | HTTP method (GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS) | No | `GET` |
| `data` | Request body data | No | - |
| `headers` | Custom headers (one per line or JSON) | No | - |
| `basic_auth` | Basic authentication (username:password) | No | - |
| `bearer_token` | Bearer token for Authorization header | No | - |
| `api_key` | API key for X-API-Key header | No | - |
| `expected_status` | Expected HTTP status code | No | `200` |
| `regex_pattern` | Regex pattern to match in response | No | - |
| `timeout` | Connection timeout in seconds | No | `30` |
| `max_time` | Upper limit on request time in seconds | No | `60` |
| `retry_attempts` | Number of retry attempts | No | `3` |
| `retry_delay` | Initial retry delay in seconds | No | `1` |
| `user_agent` | Custom User-Agent header | No | `http-api-tool/1.0` |
| `follow_redirects` | Follow HTTP redirects | No | `true` |
| `verify_ssl` | Verify SSL certificates | No | `true` |
| `debug` | Enable debug output | No | `false` |

<!-- markdownlint-enable MD013 -->

## Outputs

| Output | Description |
|--------|-------------|
| `status_code` | HTTP response status code |
| `response_time` | Response time in seconds |
| `response_body` | HTTP response body |
| `response_headers` | HTTP response headers |

## Authentication

### Basic Authentication

```yaml
with:
  basic_auth: 'username:password'
```

### Bearer Token

```yaml
with:
  bearer_token: 'your-jwt-token'
```

### API Key

```yaml
with:
  api_key: 'your-api-key'
```

### Custom Headers

```yaml
with:
  headers: |
    Authorization: Custom token
    X-Custom-Header: value
```

## Examples

### Simple Health Check

```yaml
- name: Health Check
  uses: ./
  with:
    url: 'https://api.example.com/health'
    expected_status: '200'
```

### POST with JSON Data

```yaml
- name: Create User
  uses: ./
  with:
    url: 'https://api.example.com/users'
    method: 'POST'
    headers: 'Content-Type: application/json'
    data: '{"name": "John Doe", "email": "john@example.com"}'
    expected_status: '201'
    regex_pattern: '"id":\s*\d+'
```

### Authenticated Request with Retry

```yaml
- name: Get Protected Resource
  uses: ./
  with:
    url: 'https://api.example.com/protected'
    bearer_token: ${{ secrets.API_TOKEN }}
    retry_attempts: '5'
    retry_delay: '2'
    timeout: '30'
```

### Response Validation

```yaml
- name: Test API Response
  uses: ./
  with:
    url: 'https://api.example.com/status'
    regex_pattern: '"status":\s*"ok"'
    max_time: '5'
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

### Local Development

```bash
# Test CLI functionality
pdm run python -m http_api_tool --help

# Test against local server
python -m http.server 8000 &
pdm run python -m http_api_tool --url http://localhost:8000
```

## Migration from Shell Version

If you're migrating from the original shell-based implementation:

1. **Input Compatibility**: All inputs remain the same
2. **Output Compatibility**: Outputs are identical
3. **Behavior Changes**:
   - Better JSON handling (no more escaping issues)
   - More robust error reporting
   - Improved retry logic with exponential backoff
   - Better SSL/TLS handling

## Migration to PDM

If you're migrating from the previous pip-based setup:

### For Development

Install dependencies with:

```bash
pip install --no-cache-dir pdm==2.24.2
pdm install --dev
```

You then run unit tests in the usual manner with:

```bash
pdm run pytest tests/ -v
```

### For CI/CD

**Old Dockerfile:**

```dockerfile
COPY pyproject.toml .
RUN pip install -e .
```

**New Dockerfile:**

<!-- markdownlint-disable MD013 -->

```dockerfile
COPY pyproject.toml pdm.lock ./
RUN pip install --no-cache-dir pdm==2.24.2 && \
    pdm install --prod --no-self
```

<!-- markdownlint-enable MD013 -->

### Benefits of PDM Migration

- **Reproducible Builds**: Hash verification of dependency versions
- **Security**: Hash verification prevents supply chain attacks
- **Performance**: Faster dependency resolution and installation
- **Modern Standards**: PEP 621 compliance and modern Python packaging

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

## Changelog

### v1.1.0

- **BREAKING CHANGE**: Migrated from setuptools to PDM build backend
- Dependencies now managed with PDM lock files containing hash verification
- Updated Dockerfile to use PDM for dependency installation
- Updated GitHub Actions workflows to use PDM
- Updated development documentation for PDM usage
- Enhanced security with hash-verified dependency installation

### v1.0.0

- Initial Python implementation
- Replaced shell/curl with pycurl
- Added comprehensive test suite
- Added CLI interface with Typer
- Improved error handling and retry logic
