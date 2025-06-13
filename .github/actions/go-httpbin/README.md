<!--
SPDX-License-Identifier: Apache-2.0
SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# go-httpbin GitHub Action

A reusable GitHub Action that sets up a local
[go-httpbin](https://github.com/mccutchen/go-httpbin) service with HTTPS support
using mkcert for testing HTTP API tools and services.

## Features

- 🔒 **HTTPS Support**: Automatically generates valid SSL certificates using
  mkcert
- 🐳 **Docker-based**: Runs go-httpbin in a Docker container for isolation
- 🔧 **Configurable**: Supports configuration options for different
  use cases
- 🚀 **Fast Setup**: Optimized for CI/CD pipelines with caching considerations
- 🌐 **Network Flexibility**: Supports both host networking and standard port
  mapping
- 📊 **Debug Support**: Optional verbose logging for troubleshooting

## Usage

### Basic Usage

```yaml
steps:
  - name: Setup go-httpbin
    uses: ./.github/actions/go-httpbin
    id: httpbin

  - name: Test API endpoint
    run: |
      curl -k "${{ steps.httpbin.outputs.service-url }}/get"
```

### Advanced Usage

```yaml
steps:
  - name: Setup go-httpbin with custom configuration
    uses: ./.github/actions/go-httpbin
    id: httpbin
    with:
      container-name: 'my-httpbin'
      port: '9090'
      use-host-network: 'true'
      debug: 'true'
      wait-timeout: '120'

  - name: Test with proper SSL verification
    run: |
      curl --cacert "${{ steps.httpbin.outputs.ca-cert-path }}" \
           "${{ steps.httpbin.outputs.service-url }}/get"
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `container-name` | Name for the Docker container | No | `go-httpbin` |
| `port` | Port to expose the service on | No | `8080` |
| `image` | Docker image to use | No | `ghcr.io/mccutchen/go-httpbin` |
| `use-host-network` | Use host networking (true/false) | No | `false` |
| `install-homebrew` | Install Homebrew (true/false) | No | `true` |
| `wait-timeout` | Wait time for service ready (seconds) | No | `60` |
| `debug` | Enable debug output (true/false) | No | `false` |

## Outputs

| Output | Description |
|--------|-------------|
| `container-name` | Name of the created container |
| `service-url` | Base URL of the running service |
| `host-gateway-ip` | Docker host gateway IP for container communication |
| `ca-cert-path` | Path to the mkcert CA certificate (relative to workspace) |
| `cert-file` | Path to the SSL certificate file |
| `key-file` | Path to the SSL private key file |

## Environment Variables

The action also sets the following environment variables for convenience:

- `HOST_GATEWAY`: Docker host gateway IP
- `MKCERT_CA_PATH`: Path to the mkcert CA certificate
- `GO_HTTPBIN_URL`: Base URL of the running service

## Network Modes

### Standard Mode (default)

Uses Docker port mapping to expose the service on the specified port:

```yaml
- uses: ./.github/actions/go-httpbin
  with:
    port: '8080'
```

Access the service at: `https://localhost:8080` or
`https://${{ steps.httpbin.outputs.host-gateway-ip }}:8080` from containers.

### Host Network Mode

Uses Docker host networking for direct access:

```yaml
- uses: ./.github/actions/go-httpbin
  with:
    use-host-network: 'true'
```

Access the service at: `https://localhost:8080` from both host and containers.

## SSL Certificate Handling

The action automatically:

1. Installs mkcert and creates a local CA
2. Generates SSL certificates for `localhost`
3. Installs the CA certificate in the system trust store
4. Provides paths to certificates for manual SSL verification

### Using with SSL Verification

```yaml
# With system CA (automatic)
- run: curl "${{ steps.httpbin.outputs.service-url }}/get"

# With explicit CA bundle
- run: |
    curl --cacert "${{ steps.httpbin.outputs.ca-cert-path }}" \
         "${{ steps.httpbin.outputs.service-url }}/get"

# Disable SSL verification (not recommended for production)
- run: curl -k "${{ steps.httpbin.outputs.service-url }}/get"
```

## Common Use Cases

### Testing HTTP API Tools

```yaml
jobs:
  test-api-tool:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup go-httpbin
        uses: ./.github/actions/go-httpbin
        id: httpbin

      - name: Test API tool
        run: |
          ./my-api-tool test \
            --url "${{ steps.httpbin.outputs.service-url }}/get" \
            --ca-bundle "${{ steps.httpbin.outputs.ca-cert-path }}"
```

### Testing Docker Containers

```yaml
jobs:
  test-docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup go-httpbin
        uses: ./.github/actions/go-httpbin
        id: httpbin
        with:
          use-host-network: 'true'  # Better for container-to-container communication

      - name: Test containerized application
        run: |
          docker run --rm --network=host my-app:test \
            test-endpoint "${{ steps.httpbin.outputs.service-url }}/post"
```

### Performance Testing

```yaml
jobs:
  performance-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup go-httpbin
        uses: ./.github/actions/go-httpbin
        id: httpbin
        with:
          debug: 'false'  # Reduce noise during performance tests
          wait-timeout: '120'  # Allow more time for heavy load

      - name: Run performance tests
        run: |
          # Run concurrent requests
          for i in {1..10}; do
            curl -s "${{ steps.httpbin.outputs.service-url }}/delay/1" &
          done
          wait
```

## Troubleshooting

### Enable Debug Mode

```yaml
- uses: ./.github/actions/go-httpbin
  with:
    debug: 'true'
```

This will provide verbose output including:

- Certificate generation details
- Container startup logs
- Network connectivity tests
- Final service verification

### Common Issues

1. **Service not ready timeout**: Increase `wait-timeout` value
2. **SSL certificate issues**: Check `ca-cert-path` output and use it explicitly
3. **Network connectivity**: Try `use-host-network: 'true'` for
   container-to-container communication
4. **Port conflicts**: Change the `port` input to an available port

### Manual Debugging

```yaml
- name: Debug go-httpbin setup
  run: |
    # Check container status
    docker ps -a -f name="${{ steps.httpbin.outputs.container-name }}"

    # Check container logs
    docker logs "${{ steps.httpbin.outputs.container-name }}"

    # Test connectivity
    curl -v -k "${{ steps.httpbin.outputs.service-url }}/" || true

    # Check certificates
    ls -la /tmp/localhost*pem
    openssl x509 -in "${{ steps.httpbin.outputs.cert-file }}" -text \
      -noout | head -10
```

## Requirements

- Ubuntu runner (tested on `ubuntu-latest`)
- Docker (available by default in GitHub Actions runners)
- Internet connectivity (for downloading Homebrew and mkcert)

## License

This action uses the Apache License 2.0. See the main project LICENSE file for
details.
