# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
HTTP API testing functionality.

This module contains the main HTTPAPITester class and related utilities.
"""

import base64
import json
import os
import re
import sys
import time
from io import BytesIO
from typing import Any, Dict
from urllib.parse import urlparse

import pycurl


class HTTPAPITester:
    """Main class for HTTP API testing functionality."""

    def __init__(self) -> None:
        self.debug = False
        self.step_summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
        self.github_output_file = os.environ.get("GITHUB_OUTPUT")

    def log(self, message: str, emoji: str = "") -> None:
        """Log a message with optional emoji."""
        if emoji:
            message = f"{message} {emoji}"
        print(message)

    def debug_log(self, message: str) -> None:
        """Log a debug message if debug mode is enabled."""
        if self.debug:
            print(f"🐞 {message}")

    def write_step_summary(self, message: str) -> None:
        """Write to GitHub Actions step summary if available."""
        if self.step_summary_file:
            try:
                with open(self.step_summary_file, "a", encoding="utf-8") as f:
                    f.write(f"{message}\n")
            except OSError as e:
                # Gracefully handle permission errors when running in Docker containers
                # where the step summary file may not be writable by the current user
                if self.debug:
                    print(f"🐞 Unable to write to step summary file: {e}")

    def write_github_output(self, key: str, value: str) -> None:
        """Write to GitHub Actions output file if available."""
        if self.github_output_file:
            try:
                with open(self.github_output_file, "a", encoding="utf-8") as f:
                    if "\n" in str(value):
                        # Multi-line output needs special handling
                        f.write(f"{key}<<EOF\n{value}\nEOF\n")
                    else:
                        f.write(f"{key}={value}\n")
            except OSError as e:
                # Gracefully handle permission errors when running in Docker containers
                # where the output file may not be writable by the current user
                if self.debug:
                    print(f"🐞 Unable to write to GitHub output file: {e}")
                # Still print the output for debugging
                print(f"Output: {key}={value}")

    def mask_secret(self, secret: str) -> None:
        """Mask a secret in GitHub Actions logs."""
        if secret:
            print(f"::add-mask::{secret}")

    def parse_url(self, url: str) -> Dict[str, Any]:
        """Parse URL and extract components."""
        parsed = urlparse(url)

        # Extract credentials from URL if present
        username = None
        password = None
        if parsed.username:
            username = parsed.username
            password = parsed.password or ""

        # Determine default port based on scheme
        port = parsed.port
        if port is None:
            port = 443 if parsed.scheme == "https" else 80

        return {
            "protocol": parsed.scheme,
            "username": username,
            "password": password,
            "host": parsed.hostname,
            "port": port,
            "path": parsed.path or "/",
            "query": parsed.query,
            "fragment": parsed.fragment,
        }

    def validate_inputs(self, **kwargs: Any) -> Dict[str, Any]:
        """Validate and normalize inputs."""
        # Convert string boolean inputs to actual booleans for GitHub Actions
        bool_fields = [
            "verify_ssl",
            "include_response_body",
            "follow_redirects",
            "connection_reuse",
            "debug",
            "fail_on_timeout",
            "show_header_json",
        ]

        for field in bool_fields:
            if field in kwargs and isinstance(kwargs[field], str):
                kwargs[field] = kwargs[field].lower() in (
                    "true",
                    "1",
                    "yes",
                    "on",
                )

        # Validate required URL only if this is called from GitHub Actions context
        # For CLI usage, the URL validation is handled in the typer command
        if os.environ.get("GITHUB_ACTIONS"):
            if not kwargs.get("url") and not os.environ.get("HTTP_API_URL"):
                raise ValueError("Error: a URL must be provided as input ❌")

        # Use environment variable as fallback
        if not kwargs.get("url"):
            kwargs["url"] = os.environ.get("HTTP_API_URL")

        # Validate integer inputs
        int_fields = [
            "initial_sleep_time",
            "max_delay",
            "retries",
            "curl_timeout",
            "expected_http_code",
        ]
        for field in int_fields:
            if field in kwargs:
                try:
                    value = int(kwargs[field])
                    if value < 0:
                        error_msg = f"Error: {field} must be a positive integer ❌"
                        raise ValueError(error_msg)
                    kwargs[field] = value
                except (ValueError, TypeError):
                    error_msg = f"Error: {field} must be a positive integer ❌"
                    raise ValueError(error_msg)

        # Validate float inputs
        if "max_response_time" in kwargs:
            try:
                kwargs["max_response_time"] = float(kwargs["max_response_time"])
            except (ValueError, TypeError):
                raise ValueError("Error: max_response_time must be a number ❌")

        # Validate regex if provided
        if kwargs.get("regex"):
            try:
                re.compile(kwargs["regex"])
            except re.error:
                raise ValueError(
                    f"Error: Invalid regular expression syntax ❌\n"
                    f"Regex: {kwargs['regex']}"
                )

        # Parse request headers JSON if provided
        if kwargs.get("request_headers"):
            try:
                json.loads(kwargs["request_headers"])
            except json.JSONDecodeError:
                raise ValueError("Error: request_headers must be valid JSON ❌")

        return kwargs

    def create_curl_handle(self, **config: Any) -> pycurl.Curl:
        """Create and configure a pycurl handle."""
        curl = pycurl.Curl()

        # Basic configuration
        curl.setopt(pycurl.URL, config["url"])
        curl.setopt(pycurl.TIMEOUT, config["curl_timeout"])
        curl.setopt(pycurl.CUSTOMREQUEST, config["http_method"])
        curl.setopt(pycurl.VERBOSE, config["debug"])

        # SSL/TLS options
        if not config["verify_ssl"]:
            curl.setopt(pycurl.SSL_VERIFYPEER, 0)
            curl.setopt(pycurl.SSL_VERIFYHOST, 0)
            self.log("Warning: SSL certificate verification disabled", "⚠️")
        else:
            # Check if a custom CA bundle is provided
            ca_bundle_path = config.get("ca_bundle_path")
            if ca_bundle_path:
                if os.path.isfile(ca_bundle_path):
                    curl.setopt(pycurl.CAINFO, ca_bundle_path)
                    self.debug_log(f"Using custom CA bundle: {ca_bundle_path}")
                else:
                    self.log(
                        f"Warning: CA bundle file not found: {ca_bundle_path}", "⚠️"
                    )

        # Connection options
        if not config["connection_reuse"]:
            curl.setopt(pycurl.FRESH_CONNECT, 1)
            curl.setopt(pycurl.FORBID_REUSE, 1)

        # Redirect handling
        if config["follow_redirects"]:
            curl.setopt(pycurl.FOLLOWLOCATION, 1)
        else:
            curl.setopt(pycurl.MAXREDIRS, 0)

        # Authentication
        auth_string = config.get("auth_string")
        if not auth_string:
            # Try to extract from URL
            url_parts = self.parse_url(config["url"])
            if url_parts["username"]:
                username = url_parts["username"]
                password = url_parts["password"] or ""
                auth_string = f"{username}:{password}"

        if auth_string:
            self.log("Authentication credentials provided", "💬")
            curl.setopt(pycurl.USERPWD, auth_string)
            self.mask_secret(auth_string)

        # Headers
        headers = []

        # Content-Type for request body
        if config.get("request_body"):
            headers.append(f"Content-Type: {config['content_type']}")

        # Custom headers from JSON
        if config.get("request_headers"):
            try:
                custom_headers = json.loads(config["request_headers"])
                for key, value in custom_headers.items():
                    headers.append(f"{key}: {value}")
                self.debug_log(f"Added custom headers: {custom_headers}")
            except json.JSONDecodeError:
                raise ValueError("Error: Invalid JSON in request_headers ❌")

        if headers:
            curl.setopt(pycurl.HTTPHEADER, headers)

        # Request body
        if config.get("request_body"):
            body_data = config["request_body"].encode("utf-8")
            curl.setopt(pycurl.POSTFIELDS, body_data)
            curl.setopt(pycurl.POSTFIELDSIZE, len(body_data))
            self.mask_secret(config["request_body"])

        # Response handling
        if (
            not config.get("regex")
            and not config.get("include_response_body", True)
            and not config["debug"]
        ):
            curl.setopt(pycurl.NOBODY, 1)  # HEAD request

        return curl

    def perform_request(self, curl: pycurl.Curl) -> Dict[str, Any]:
        """Perform HTTP request and return response data."""
        # Prepare buffers
        response_buffer = BytesIO()
        header_buffer = BytesIO()

        curl.setopt(pycurl.WRITEDATA, response_buffer)
        curl.setopt(pycurl.HEADERFUNCTION, header_buffer.write)

        try:
            curl.perform()

            # Get response metrics
            response_code = curl.getinfo(pycurl.RESPONSE_CODE)
            total_time = curl.getinfo(pycurl.TOTAL_TIME)
            connect_time = curl.getinfo(pycurl.CONNECT_TIME)
            download_size = curl.getinfo(pycurl.SIZE_DOWNLOAD)
            header_size = curl.getinfo(pycurl.HEADER_SIZE)

            # Get response content
            response_body = response_buffer.getvalue()
            response_headers = header_buffer.getvalue().decode("utf-8", errors="ignore")

            # Parse headers into JSON format
            header_json = self._parse_headers_to_json(response_headers)

            return {
                "success": True,
                "http_code": int(response_code),
                "total_time": total_time,
                "connect_time": connect_time,
                "body_size": int(download_size),
                "header_size": int(header_size),
                "response_body": response_body,
                "response_headers": response_headers,
                "header_json": header_json,
                "curl_error": None,
            }

        except pycurl.error as e:
            error_code, error_msg = e.args
            return {
                "success": False,
                "http_code": 0,
                "total_time": 0,
                "connect_time": 0,
                "body_size": 0,
                "header_size": 0,
                "response_body": b"",
                "response_headers": "",
                "header_json": "{}",
                "curl_error": (error_code, error_msg),
            }

    def _parse_headers_to_json(self, headers_text: str) -> str:
        """Parse HTTP headers text into JSON format."""
        if not headers_text.strip():
            return "{}"

        headers_dict = {}
        lines = headers_text.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line or line.startswith("HTTP/"):
                continue

            if ":" in line:
                key, value = line.split(":", 1)
                headers_dict[key.strip()] = value.strip()

        try:
            return json.dumps(headers_dict, separators=(",", ":"))
        except Exception:
            return "{}"

    def check_regex_match(self, response_body: bytes, regex_pattern: str) -> bool:
        """Check if response body matches the given regex pattern."""
        if not regex_pattern:
            return True

        try:
            # Decode response body to string for regex matching
            body_text = response_body.decode("utf-8", errors="ignore")
            return bool(re.search(regex_pattern, body_text))
        except Exception:
            return False

    def handle_curl_error(self, error_code: int, _error_msg: str) -> bool:
        """Handle cURL errors and return whether to continue retrying."""
        self.log(f"cURL error code: {error_code}")

        # Define error messages and whether they should cause immediate exit
        error_handlers = {
            1: ("Error: Unsupported protocol", False),
            3: ("Error: URL malformed", False),
            5: ("Error: Couldn't resolve proxy", False),
            6: ("Error: Couldn't resolve host", False),
            7: ("Error: Failed to connect to host", False),
            28: ("Error: Request timeout", False),
            35: ("Error: SSL connect error", True),  # Immediate exit
            51: (
                "Error: The peer's SSL certificate is not OK",
                True,
            ),  # Immediate exit
            52: ("Error: Nothing was returned from the server", False),
            60: ("Error: SSL self-signed certificate", True),  # Immediate exit
        }

        if error_code in error_handlers:
            error_msg_formatted, should_exit = error_handlers[error_code]
            self.log(error_msg_formatted, "❌")
            if should_exit:
                self.write_step_summary(f"{error_msg_formatted} ❌")
                return False  # Stop retrying
        else:
            self.log(f"Error: cURL encountered an error (code {error_code})", "❌")

        return True  # Continue retrying for non-fatal errors

    def test_api(self, **config: Any) -> Dict[str, Any]:
        """Main testing function with retry logic."""
        # Validate inputs
        config = self.validate_inputs(**config)
        self.debug = config["debug"]

        # Parse URL for display purposes
        url_parts = self.parse_url(config["url"])
        protocol = url_parts["protocol"]
        host = url_parts["host"]
        port = url_parts["port"]

        # Show what we're about to verify (for GitHub Actions context)
        if os.environ.get("GITHUB_ACTIONS"):
            self.log(f"🎯 Starting test: {config['service_name']}")
            self.log(f"🌐 Target URL: {config['url']}")

        self.debug_log("URL Debug Info:")
        self.debug_log(f"  Original URL: '{config['url']}'")
        self.debug_log(f"  Protocol: '{protocol}'")
        self.debug_log(f"  Host: '{host}'")
        self.debug_log(f"  Port: '{port}'")
        self.debug_log(f"  Path: '{url_parts['path']}'")

        # Write initial step summary
        self.write_step_summary(f"# {config['service_name']}")
        self.write_step_summary("### Check API/Service Availability 🌍")

        # Initialize counters
        counter = 0
        time_delay = 0
        sleep_time = config["initial_sleep_time"]

        # Initialize default outputs
        result = {
            "response_http_code": 0,
            "response_header_json": "{}",
            "response_header_size": 0,
            "response_body_size": 0,
            "total_time": 0,
            "connect_time": 0,
            "regex_match": False,
            "response_body_base64": "",
            "time_delay": 0,
            "response_time_exceeded": False,
        }

        # Main retry loop
        while True:
            counter += 1

            self.debug_log(f"Attempt: {counter} / {config['retries']}")
            self.debug_log(f"Delay/Wait Interval: {sleep_time} seconds")
            self.debug_log(f"Delay/Wait Current Value: {time_delay} seconds")

            # Create and configure curl handle
            curl = self.create_curl_handle(**config)

            try:
                # Perform the request
                response = self.perform_request(curl)

                # Update result with response data
                result.update(
                    {
                        "response_http_code": response["http_code"],
                        "response_header_json": response["header_json"],
                        "response_header_size": response["header_size"],
                        "response_body_size": response["body_size"],
                        "total_time": response["total_time"],
                        "connect_time": response["connect_time"],
                        "time_delay": time_delay,
                    }
                )

                # Handle response body if requested
                if config["include_response_body"] and response["response_body"]:
                    result["response_body_base64"] = base64.b64encode(
                        response["response_body"]
                    ).decode("ascii")

                self.debug_log(f"Response Code: {response['http_code']}")
                self.debug_log(f"Header Size: {response['header_size']} bytes")
                self.debug_log(f"Body Size: {response['body_size']} bytes")

                # Check if request was successful
                if not response["success"]:
                    error_code, error_msg = response["curl_error"]
                    if not self.handle_curl_error(error_code, error_msg):
                        # Fatal error - exit immediately
                        sys.exit(1)
                else:
                    # Request succeeded - check response code
                    if response["http_code"] == config["expected_http_code"]:
                        self.log(f"{protocol}://{host}:{port}", "✅")
                        self.write_step_summary(f"{protocol}://{host}:{port} ✅")
                        self.log(f"Returned status code: {response['http_code']}")

                        if counter > 1:
                            self.log(
                                f"Time taken for service availability: {time_delay}",
                                "💬",
                            )

                        # Validate response time if specified
                        if config["max_response_time"] > 0 and response["total_time"]:
                            if response["total_time"] > config["max_response_time"]:
                                self.log(
                                    f"Warning: Response time exceeded maximum ({response['total_time']} > {config['max_response_time']} seconds)",
                                    "⚠️",
                                )
                                result["response_time_exceeded"] = True
                                self.write_step_summary(
                                    f"Response Time: {response['total_time']} seconds (exceeded limit of {config['max_response_time']})"
                                )

                                if config["fail_on_timeout"]:
                                    self.log(
                                        "Error: Response time exceeded maximum allowed time",
                                        "❌",
                                    )
                                    self.write_step_summary(
                                        "Error: Response time exceeded maximum allowed time ❌"
                                    )
                                    sys.exit(1)
                            else:
                                self.log(
                                    f"Response time within acceptable limit ({response['total_time']} <= {config['max_response_time']} seconds)",
                                    "✅",
                                )
                                self.write_step_summary(
                                    f"Response Time: {response['total_time']} seconds"
                                )

                        # Check regex if provided
                        if config.get("regex"):
                            self.log(
                                "Regular expression provided; validating response/reply"
                            )
                            if not response["response_body"]:
                                self.log(
                                    "Error: regex validation requested, but response empty",
                                    "❌",
                                )
                                sys.exit(1)

                            if self.check_regex_match(
                                response["response_body"], config["regex"]
                            ):
                                self.log("RegEx matched server reply/body", "✅")
                                self.write_step_summary(
                                    "RegEx matched server reply/body ✅"
                                )
                                result["regex_match"] = True
                            else:
                                self.log(
                                    "Warning: RegEx NOT matched server reply/body", "⚠️"
                                )
                                self.write_step_summary(
                                    "Warning: RegEx NOT matched server reply/body ⚠️"
                                )
                                result["regex_match"] = False

                        # Success!
                        return result

            finally:
                curl.close()

            # Check if we've exhausted all retries
            if counter >= config["retries"]:
                self.write_step_summary(f"{protocol}://{host}:{port}")
                self.log(f"{protocol}://{host}:{port}")
                self.log(f"Error: service marked failed at {time_delay} seconds", "❌")
                self.write_step_summary(
                    f"Error: service marked failed at {time_delay} seconds ❌"
                )

                # Provide feedback on common response codes
                response_code = result["response_http_code"]
                if isinstance(response_code, int) and response_code == 401:
                    self.log(
                        "Unauthorized; check/supply valid API/service credentials", "⚠️"
                    )
                elif isinstance(response_code, int) and response_code == 404:
                    self.log("Not Found; verify the URL or endpoint", "⚠️")
                elif isinstance(response_code, int) and response_code >= 500:
                    self.log("Server Error; the API might be down or overloaded", "⚠️")

                sys.exit(1)

            # Wait before next retry
            self.log(f"Waiting for {sleep_time} seconds before retrying...")
            time.sleep(sleep_time)
            time_delay += sleep_time

            # Exponential backoff with cap
            sleep_time = min(sleep_time * (2 ** (counter - 1)), config["max_delay"])
            self.log(f"Sleep/wait time for next attempt: {sleep_time} seconds")
