# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
CLI interface for HTTP API testing.

This module provides the command-line interface using Typer for both standalone
CLI usage and GitHub Actions integration.
"""

import os
import sys
import subprocess
from typing import Any, Dict, Optional
from urllib.parse import urlparse, urlunparse

import typer

from .verifier import HTTPAPITester

app = typer.Typer(help="A Python tool to test HTTP API services.")


def _get_docker_host_gateway() -> Optional[str]:
    """Get the Docker host gateway IP that containers can use to reach the host."""
    try:
        # Try to get the gateway IP from the container's route table
        result = subprocess.run(
            ["sh", "-c", "ip route | grep '^default' | cut -d' ' -f3"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            gateway_ip = result.stdout.strip()
            if gateway_ip and gateway_ip != "localhost" and gateway_ip != "127.0.0.1":
                return gateway_ip
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def _transform_localhost_url(url: str) -> str:
    """Transform localhost URLs to use Docker host gateway when running in a container."""
    # Only transform if we're in a containerized environment (GitHub Actions)
    if not os.environ.get("GITHUB_ACTIONS"):
        return url

    parsed = urlparse(url)
    if parsed.hostname in ["localhost", "127.0.0.1"]:
        gateway_ip = _get_docker_host_gateway()
        if gateway_ip:
            # Replace the hostname with the gateway IP
            new_netloc = parsed.netloc.replace(parsed.hostname, gateway_ip)
            new_parsed = parsed._replace(netloc=new_netloc)
            transformed_url = urlunparse(new_parsed)
            return transformed_url

    return url


@app.callback()  # type: ignore[misc]
def main_callback() -> None:
    """
    HTTP server/API testing tool

    This script can be used both as a CLI tool (using Typer) and as a GitHub Action.
    It uses pycurl for HTTP requests to avoid the shell escaping issues of the
    original implementation.
    """
    pass


@app.command("test")  # type: ignore[misc]
def verify(
    url: str = typer.Option(..., help="URL of API server/interface to check"),
    auth_string: Optional[str] = typer.Option(
        None, help="Authentication string, colon separated username/password"
    ),
    service_name: str = typer.Option(
        "API Service", help="Name of HTTP/HTTPS API service tested"
    ),
    initial_sleep_time: int = typer.Option(
        1, help="Time in seconds between API service connection attempts"
    ),
    max_delay: int = typer.Option(30, help="Maximum delay in seconds between retries"),
    retries: int = typer.Option(
        3, help="Number of retries before declaring service unavailable"
    ),
    expected_http_code: int = typer.Option(
        200, help="HTTP response code to accept from the API service"
    ),
    regex: Optional[str] = typer.Option(
        None, help="Verify server response with regular expression"
    ),
    show_header_json: bool = typer.Option(
        False, help="Display response header as JSON in action output"
    ),
    curl_timeout: int = typer.Option(
        5, help="Maximum time in seconds for cURL to wait for a response"
    ),
    http_method: str = typer.Option(
        "GET", help="HTTP method to use (GET, POST, PUT, etc.)"
    ),
    request_body: Optional[str] = typer.Option(
        None, help="Data to send with POST/PUT/PATCH requests"
    ),
    content_type: str = typer.Option(
        "application/json", help="Content type of the request body"
    ),
    request_headers: Optional[str] = typer.Option(
        None, help="Custom HTTP headers sent in JSON format"
    ),
    verify_ssl: bool = typer.Option(True, help="Verify SSL certificates"),
    ca_bundle_path: Optional[str] = typer.Option(
        None, help="Path to CA bundle file for SSL verification"
    ),
    include_response_body: bool = typer.Option(
        False, help="Include response body in outputs (base64 encoded)"
    ),
    follow_redirects: bool = typer.Option(True, help="Follow HTTP redirects"),
    max_response_time: float = typer.Option(
        0, help="Maximum acceptable response time in seconds"
    ),
    connection_reuse: bool = typer.Option(
        True, help="Reuse connections between requests"
    ),
    debug: bool = typer.Option(False, help="Enables debugging output"),
    fail_on_timeout: bool = typer.Option(
        False, help="Fail the action if response time exceeds max_response_time"
    ),
) -> None:
    """Test HTTP API endpoint testing with retry logic."""
    verifier = HTTPAPITester()

    # Prepare config
    config = {
        "url": url,
        "auth_string": auth_string,
        "service_name": service_name,
        "initial_sleep_time": initial_sleep_time,
        "max_delay": max_delay,
        "retries": retries,
        "expected_http_code": expected_http_code,
        "regex": regex,
        "show_header_json": show_header_json,
        "curl_timeout": curl_timeout,
        "http_method": http_method,
        "request_body": request_body,
        "content_type": content_type,
        "request_headers": request_headers,
        "verify_ssl": verify_ssl,
        "ca_bundle_path": ca_bundle_path,
        "include_response_body": include_response_body,
        "follow_redirects": follow_redirects,
        "max_response_time": max_response_time,
        "connection_reuse": connection_reuse,
        "debug": debug,
        "fail_on_timeout": fail_on_timeout,
    }

    # Transform URL if necessary
    if isinstance(config["url"], str):
        config["url"] = _transform_localhost_url(config["url"])

    try:
        result = verifier.test_api(**config)

        # For CLI usage, print the results
        if not os.environ.get("GITHUB_ACTIONS"):
            typer.echo("✅ API test successful!")
            typer.echo(f"Response Code: {result['response_http_code']}")
            typer.echo(f"Total Time: {result['total_time']:.3f}s")
            typer.echo(f"Connect Time: {result['connect_time']:.3f}s")
            if result.get("regex_match"):
                typer.echo(f"Regex Match: {'✅' if result['regex_match'] else '❌'}")

    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


def _log_action_parameters(config: Dict[str, Any]) -> None:
    """Log the action parameters in a user-friendly format."""
    print("📋 Configuration:")
    print(f"   URL: {config.get('url', 'Not specified')}")
    print(f"   HTTP Method: {config.get('http_method', 'GET')}")
    print(f"   Service Name: {config.get('service_name', 'API Service')}")
    print(f"   Expected HTTP Code: {config.get('expected_http_code', '200')}")
    print(f"   Retries: {config.get('retries', '3')}")
    print(f"   Timeout: {config.get('curl_timeout', '5')} seconds")
    print(f"   SSL Verification: {config.get('verify_ssl', 'true')}")
    print(f"   Follow Redirects: {config.get('follow_redirects', 'true')}")

    # Show optional parameters if they're set
    if config.get("regex"):
        print(f"   Regex Pattern: {config['regex']}")
    if config.get("request_body"):
        body = config["request_body"]
        truncated_body = body[:100] + ("..." if len(body) > 100 else "")
        print(f"   Request Body: {truncated_body}")
    if config.get("request_headers"):
        print(f"   Custom Headers: {config['request_headers']}")
    if config.get("auth_string"):
        print("   Authentication: *** (hidden)")
    max_time = config.get("max_response_time")
    if max_time and float(max_time) > 0:
        print(f"   Max Response Time: {max_time} seconds")

    debug_enabled = config.get("debug", "false").lower() == "true"
    print(f"   Debug Mode: {debug_enabled}")
    print("=" * 50)
    print()


def run_github_action() -> None:
    """Run in GitHub Actions mode."""
    verifier = HTTPAPITester()

    # Print startup banner
    print("🚀 HTTP API Tool")
    print("=" * 50)

    # Map GitHub Action inputs to function parameters
    config = {}
    input_mappings = {
        "url": "INPUT_URL",
        "auth_string": "INPUT_AUTH_STRING",
        "service_name": "INPUT_SERVICE_NAME",
        "initial_sleep_time": "INPUT_INITIAL_SLEEP_TIME",
        "max_delay": "INPUT_MAX_DELAY",
        "retries": "INPUT_RETRIES",
        "expected_http_code": "INPUT_EXPECTED_HTTP_CODE",
        "regex": "INPUT_REGEX",
        "show_header_json": "INPUT_SHOW_HEADER_JSON",
        "curl_timeout": "INPUT_CURL_TIMEOUT",
        "http_method": "INPUT_HTTP_METHOD",
        "request_body": "INPUT_REQUEST_BODY",
        "content_type": "INPUT_CONTENT_TYPE",
        "request_headers": "INPUT_REQUEST_HEADERS",
        "verify_ssl": "INPUT_VERIFY_SSL",
        "ca_bundle_path": "INPUT_CA_BUNDLE_PATH",
        "include_response_body": "INPUT_INCLUDE_RESPONSE_BODY",
        "follow_redirects": "INPUT_FOLLOW_REDIRECTS",
        "max_response_time": "INPUT_MAX_RESPONSE_TIME",
        "connection_reuse": "INPUT_CONNECTION_REUSE",
        "debug": "INPUT_DEBUG",
        "fail_on_timeout": "INPUT_FAIL_ON_TIMEOUT",
    }

    # Set defaults
    defaults = {
        "service_name": "API Service",
        "initial_sleep_time": "1",
        "max_delay": "30",
        "retries": "3",
        "expected_http_code": "200",
        "curl_timeout": "5",
        "http_method": "GET",
        "content_type": "application/json",
        "verify_ssl": "true",
        "include_response_body": "false",
        "follow_redirects": "true",
        "max_response_time": "0",
        "connection_reuse": "true",
        "debug": "false",
        "fail_on_timeout": "false",
        "show_header_json": "false",
    }

    # Get inputs from environment with defaults
    for param, env_var in input_mappings.items():
        value = os.environ.get(env_var, defaults.get(param))
        if value is not None:
            config[param] = value

    # Transform localhost URLs for Docker container networking
    if "url" in config:
        config["url"] = _transform_localhost_url(config["url"])

    # Log the configuration
    _log_action_parameters(config)

    try:
        result = verifier.test_api(**config)

        # Write outputs to GitHub Actions
        for key, value in result.items():
            # Convert boolean values to lowercase strings for GitHub Actions
            # Note: result dict contains mixed types: bool, int, float, str
            value_any: Any = value  # Help MyPy understand mixed types
            if isinstance(value_any, bool):
                output_value = str(value_any).lower()
            else:
                # Handle non-boolean values (int, float, str, etc.)
                output_value = str(value_any)
            verifier.write_github_output(key, output_value)

        # Show completion message
        print()
        print("✅ HTTP API Tool")
        print("=" * 50)

    except Exception as e:
        # Only log once to avoid duplication
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main entry point - handles both GitHub Actions and CLI usage."""
    # Check if we're in GitHub Actions context AND not being invoked for help
    # AND no CLI subcommands are provided (indicating genuine GitHub Actions usage)
    has_cli_command = any(cmd in sys.argv for cmd in ["test", "help", "--help", "-h"])

    if (
        os.environ.get("GITHUB_ACTIONS")
        and not has_cli_command
        and "--help" not in sys.argv
        and "-h" not in sys.argv
    ):
        run_github_action()
    else:
        # Running as CLI tool or help was requested or explicit CLI command provided
        app()
