# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Comprehensive test suite for HTTP API Test Tool.

This test suite covers all the functionality of the HTTP API testing tool,
including various scenarios, error conditions, and edge cases.

Test Categories:
- Unit Tests (TestHTTPAPITester): Mock-based tests for individual methods
- Integration Tests (TestIntegration): Workflow tests using mocks

External Dependencies:
All external HTTP calls have been removed from pytest tests to ensure
fast, reliable test execution without network dependencies. Response time
and delay testing is handled by the GitHub Actions workflow using a local
go-httpbin service in testing.yaml.

Test Markers:
- @pytest.mark.unit: Unit tests that can be run independently
- @pytest.mark.integration: Integration tests for complete workflows

Usage:
- Run all tests: pytest tests/
- Run only unit tests: pytest tests/ -m "unit"
- Run only integration tests: pytest tests/ -m "integration"
- Exclude integration tests: pytest tests/ -m "not integration"
"""

import json
import os
import tempfile
from unittest.mock import Mock, patch

import pycurl
import pytest

# Import the module to test
from http_api_tool.verifier import HTTPAPITester


@pytest.mark.unit
class TestHTTPAPITester:
    """Unit tests for HTTPAPITester functionality.

    These tests use mocks to isolate individual methods and test them
    without external dependencies.
    """

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.verifier = HTTPAPITester()
        # Create temporary files for GitHub Actions simulation
        self.temp_summary = tempfile.NamedTemporaryFile(mode="w+", delete=False)
        self.temp_output = tempfile.NamedTemporaryFile(mode="w+", delete=False)

        # Set environment variables
        os.environ["GITHUB_STEP_SUMMARY"] = self.temp_summary.name
        os.environ["GITHUB_OUTPUT"] = self.temp_output.name

        self.verifier.step_summary_file = self.temp_summary.name
        self.verifier.github_output_file = self.temp_output.name

    def teardown_method(self) -> None:
        """Clean up test fixtures."""
        # Clean up temp files
        try:
            os.unlink(self.temp_summary.name)
            os.unlink(self.temp_output.name)
        except OSError:
            pass

        # Clean up environment variables
        for key in ["GITHUB_STEP_SUMMARY", "GITHUB_OUTPUT", "HTTP_API_URL"]:
            if key in os.environ:
                del os.environ[key]

    def test_parse_url_basic(self) -> None:
        """Test basic URL parsing."""
        url = "https://example.com:8080/api/v1"
        result = self.verifier.parse_url(url)

        assert result["protocol"] == "https"
        assert result["host"] == "example.com"
        assert result["port"] == 8080
        assert result["path"] == "/api/v1"
        assert result["username"] is None
        assert result["password"] is None

    def test_parse_url_with_credentials(self) -> None:
        """Test URL parsing with embedded credentials."""
        url = "http://user:pass@example.com/api"
        result = self.verifier.parse_url(url)

        assert result["protocol"] == "http"
        assert result["host"] == "example.com"
        assert result["port"] == 80  # Default HTTP port
        assert result["path"] == "/api"
        assert result["username"] == "user"
        assert result["password"] == "pass"

    def test_parse_url_default_ports(self) -> None:
        """Test URL parsing with default ports."""
        # HTTP default port
        result = self.verifier.parse_url("http://example.com")
        assert result["port"] == 80

        # HTTPS default port
        result = self.verifier.parse_url("https://example.com")
        assert result["port"] == 443

    def test_validate_inputs_basic(self) -> None:
        """Test basic input validation."""
        inputs = {
            "url": "https://example.com",
            "retries": "3",
            "curl_timeout": "5",
            "expected_http_code": "200",
            "verify_ssl": "true",
            "debug": "false",
        }

        result = self.verifier.validate_inputs(**inputs)

        assert result["url"] == "https://example.com"
        assert result["retries"] == 3
        assert result["curl_timeout"] == 5
        assert result["expected_http_code"] == 200
        assert result["verify_ssl"] is True
        assert result["debug"] is False

    def test_validate_inputs_environment_fallback(self) -> None:
        """Test URL fallback to environment variable."""
        os.environ["HTTP_API_URL"] = "https://env-example.com"

        inputs = {"retries": "3"}
        result = self.verifier.validate_inputs(**inputs)

        assert result["url"] == "https://env-example.com"

    def test_validate_inputs_missing_url(self) -> None:
        """Test validation error for missing URL in GitHub Actions context."""
        inputs = {"retries": "3"}

        # Mock GitHub Actions environment
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}):
            with pytest.raises(ValueError, match="Error: a URL must be provided"):
                self.verifier.validate_inputs(**inputs)

    def test_validate_inputs_missing_url_cli(self) -> None:
        """Test that missing URL in CLI context does not raise error in validate_inputs."""
        inputs = {"retries": "3"}

        # Ensure we're not in GitHub Actions context
        with patch.dict(os.environ, {}, clear=True):
            # This should not raise an error since URL validation is skipped in CLI mode
            result = self.verifier.validate_inputs(**inputs)
            assert result["retries"] == 3

    def test_validate_inputs_invalid_integer(self) -> None:
        """Test validation error for invalid integer inputs."""
        inputs = {"url": "https://example.com", "retries": "invalid"}

        with pytest.raises(ValueError, match="retries must be a positive integer"):
            self.verifier.validate_inputs(**inputs)

    def test_validate_inputs_negative_integer(self) -> None:
        """Test validation error for negative integer inputs."""
        inputs = {"url": "https://example.com", "retries": "-1"}

        with pytest.raises(ValueError, match="retries must be a positive integer"):
            self.verifier.validate_inputs(**inputs)

    def test_validate_inputs_invalid_regex(self) -> None:
        """Test validation error for invalid regex."""
        inputs = {
            "url": "https://example.com",
            "regex": "[",  # Invalid regex - unclosed bracket
        }

        with pytest.raises(ValueError, match="Invalid regular expression syntax"):
            self.verifier.validate_inputs(**inputs)

    def test_validate_inputs_invalid_json_headers(self) -> None:
        """Test validation error for invalid JSON headers."""
        inputs = {"url": "https://example.com", "request_headers": "{invalid json}"}

        with pytest.raises(ValueError, match="request_headers must be valid JSON"):
            self.verifier.validate_inputs(**inputs)

    def test_validate_inputs_valid_json_headers(self) -> None:
        """Test validation with valid JSON headers."""
        inputs = {
            "url": "https://example.com",
            "request_headers": '{"Content-Type": "application/json", "X-API-Key": "test"}',
        }

        result = self.verifier.validate_inputs(**inputs)
        assert (
            result["request_headers"]
            == '{"Content-Type": "application/json", "X-API-Key": "test"}'
        )

    def test_parse_headers_to_json(self) -> None:
        """Test HTTP headers parsing to JSON."""
        headers_text = """HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 123
Server: nginx/1.18.0
X-Custom-Header: test-value

"""

        result = self.verifier._parse_headers_to_json(headers_text)
        parsed = json.loads(result)

        assert parsed["Content-Type"] == "application/json"
        assert parsed["Content-Length"] == "123"
        assert parsed["Server"] == "nginx/1.18.0"
        assert parsed["X-Custom-Header"] == "test-value"

    def test_parse_headers_to_json_empty(self) -> None:
        """Test headers parsing with empty input."""
        result = self.verifier._parse_headers_to_json("")
        assert result == "{}"

    def test_check_regex_match_success(self) -> None:
        """Test successful regex matching."""
        response_body = b'{"status": "success", "message": "API is working"}'
        regex_pattern = r'"status":\s*"success"'

        result = self.verifier.check_regex_match(response_body, regex_pattern)
        assert result is True

    def test_check_regex_match_failure(self) -> None:
        """Test failed regex matching."""
        response_body = b'{"status": "error", "message": "API is down"}'
        regex_pattern = r'"status":\s*"success"'

        result = self.verifier.check_regex_match(response_body, regex_pattern)
        assert result is False

    def test_check_regex_match_no_pattern(self) -> None:
        """Test regex matching with no pattern (should return True)."""
        response_body = b'{"status": "success"}'

        result = self.verifier.check_regex_match(response_body, "")
        assert result is True

    def test_handle_curl_error_non_fatal(self) -> None:
        """Test handling of non-fatal cURL errors."""
        # Test connection timeout (should continue retrying)
        result = self.verifier.handle_curl_error(7, "Failed to connect")
        assert result is True

    def test_handle_curl_error_fatal(self) -> None:
        """Test handling of fatal cURL errors."""
        # Test SSL error (should stop retrying)
        result = self.verifier.handle_curl_error(35, "SSL connect error")
        assert result is False

    def test_handle_curl_error_unknown(self) -> None:
        """Test handling of unknown cURL errors."""
        # Test unknown error code (should continue retrying)
        result = self.verifier.handle_curl_error(999, "Unknown error")
        assert result is True

    def test_write_step_summary(self) -> None:
        """Test writing to GitHub Actions step summary."""
        self.verifier.write_step_summary("Test summary message")

        with open(self.temp_summary.name, "r") as f:
            content = f.read()

        assert "Test summary message\n" in content

    def test_write_github_output_single_line(self) -> None:
        """Test writing single-line output to GitHub Actions."""
        self.verifier.write_github_output("test_key", "test_value")

        with open(self.temp_output.name, "r") as f:
            content = f.read()

        assert "test_key=test_value\n" in content

    def test_write_github_output_multi_line(self) -> None:
        """Test writing multi-line output to GitHub Actions."""
        multi_line_value = "line1\nline2\nline3"
        self.verifier.write_github_output("test_key", multi_line_value)

        with open(self.temp_output.name, "r") as f:
            content = f.read()

        assert "test_key<<EOF\nline1\nline2\nline3\nEOF\n" in content

    @patch("http_api_tool.verifier.pycurl.Curl")
    def test_create_curl_handle_basic(self, mock_curl_class: Mock) -> None:
        """Test basic cURL handle creation."""
        mock_curl = Mock()
        mock_curl_class.return_value = mock_curl

        config = {
            "url": "https://example.com",
            "curl_timeout": 5,
            "http_method": "GET",
            "verify_ssl": True,
            "connection_reuse": True,
            "follow_redirects": True,
            "debug": False,
            "include_response_body": True,
        }

        self.verifier.create_curl_handle(**config)

        # Verify basic settings were applied
        mock_curl.setopt.assert_any_call(pycurl.URL, "https://example.com")
        mock_curl.setopt.assert_any_call(pycurl.TIMEOUT, 5)
        mock_curl.setopt.assert_any_call(pycurl.CUSTOMREQUEST, "GET")
        mock_curl.setopt.assert_any_call(pycurl.VERBOSE, False)

    @patch("http_api_tool.verifier.pycurl.Curl")
    def test_create_curl_handle_ssl_disabled(self, mock_curl_class: Mock) -> None:
        """Test cURL handle creation with SSL verification disabled."""
        mock_curl = Mock()
        mock_curl_class.return_value = mock_curl

        config = {
            "url": "https://example.com",
            "curl_timeout": 5,
            "http_method": "GET",
            "verify_ssl": False,
            "connection_reuse": True,
            "follow_redirects": True,
            "debug": False,
            "include_response_body": True,
        }

        self.verifier.create_curl_handle(**config)

        # Verify SSL verification was disabled
        mock_curl.setopt.assert_any_call(pycurl.SSL_VERIFYPEER, 0)
        mock_curl.setopt.assert_any_call(pycurl.SSL_VERIFYHOST, 0)

    @patch("http_api_tool.verifier.pycurl.Curl")
    def test_create_curl_handle_with_auth(self, mock_curl_class: Mock) -> None:
        """Test cURL handle creation with authentication."""
        mock_curl = Mock()
        mock_curl_class.return_value = mock_curl

        config = {
            "url": "https://example.com",
            "auth_string": "user:password",
            "curl_timeout": 5,
            "http_method": "GET",
            "verify_ssl": True,
            "connection_reuse": True,
            "follow_redirects": True,
            "debug": False,
            "include_response_body": True,
        }

        self.verifier.create_curl_handle(**config)

        # Verify authentication was set
        mock_curl.setopt.assert_any_call(pycurl.USERPWD, "user:password")

    @patch("http_api_tool.verifier.pycurl.Curl")
    def test_create_curl_handle_with_body(self, mock_curl_class: Mock) -> None:
        """Test cURL handle creation with request body."""
        mock_curl = Mock()
        mock_curl_class.return_value = mock_curl

        config = {
            "url": "https://example.com",
            "curl_timeout": 5,
            "http_method": "POST",
            "request_body": '{"test": "data"}',
            "content_type": "application/json",
            "verify_ssl": True,
            "connection_reuse": True,
            "follow_redirects": True,
            "debug": False,
            "include_response_body": True,
        }

        self.verifier.create_curl_handle(**config)

        # Verify body was set
        expected_body = b'{"test": "data"}'
        mock_curl.setopt.assert_any_call(pycurl.POSTFIELDS, expected_body)
        mock_curl.setopt.assert_any_call(pycurl.POSTFIELDSIZE, len(expected_body))

    @patch("http_api_tool.verifier.pycurl.Curl")
    def test_create_curl_handle_with_headers(self, mock_curl_class: Mock) -> None:
        """Test cURL handle creation with custom headers."""
        mock_curl = Mock()
        mock_curl_class.return_value = mock_curl

        config = {
            "url": "https://example.com",
            "curl_timeout": 5,
            "http_method": "GET",
            "request_headers": '{"X-API-Key": "test123", "X-Custom": "value"}',
            "verify_ssl": True,
            "connection_reuse": True,
            "follow_redirects": True,
            "debug": False,
            "include_response_body": True,
        }

        self.verifier.create_curl_handle(**config)

        # Check that headers were set (the exact call depends on the implementation)
        # We'll verify that setopt was called with HTTPHEADER
        header_calls = [
            call
            for call in mock_curl.setopt.call_args_list
            if call[0][0] == pycurl.HTTPHEADER
        ]
        assert len(header_calls) > 0

    @patch("http_api_tool.verifier.pycurl.Curl")
    def test_create_curl_handle_with_ca_bundle(self, mock_curl_class: Mock) -> None:
        """Test cURL handle creation with custom CA bundle."""
        mock_curl = Mock()
        mock_curl_class.return_value = mock_curl

        config = {
            "url": "https://example.com",
            "curl_timeout": 5,
            "http_method": "GET",
            "verify_ssl": True,
            "ca_bundle_path": "/path/to/ca-bundle.crt",
            "connection_reuse": True,
            "follow_redirects": True,
            "debug": False,
            "include_response_body": True,
        }

        # Mock file existence check
        with patch("os.path.isfile", return_value=True):
            self.verifier.create_curl_handle(**config)

        # Verify CA bundle was set
        mock_curl.setopt.assert_any_call(pycurl.CAINFO, "/path/to/ca-bundle.crt")

    @patch("http_api_tool.verifier.pycurl.Curl")
    def test_create_curl_handle_with_invalid_ca_bundle(
        self, mock_curl_class: Mock
    ) -> None:
        """Test cURL handle creation with invalid CA bundle path."""
        mock_curl = Mock()
        mock_curl_class.return_value = mock_curl

        config = {
            "url": "https://example.com",
            "curl_timeout": 5,
            "http_method": "GET",
            "verify_ssl": True,
            "ca_bundle_path": "/nonexistent/ca-bundle.crt",
            "connection_reuse": True,
            "follow_redirects": True,
            "debug": False,
            "include_response_body": True,
        }

        # Mock file existence check to return False
        with patch("os.path.isfile", return_value=False):
            self.verifier.create_curl_handle(**config)

        # Verify CA bundle was NOT set when file doesn't exist
        ca_info_calls = [
            call
            for call in mock_curl.setopt.call_args_list
            if call[0][0] == pycurl.CAINFO
        ]
        assert len(ca_info_calls) == 0

    @patch("pycurl.Curl")
    def test_perform_request_success(self, mock_curl_class: Mock) -> None:
        """Test successful HTTP request performance."""
        mock_curl = Mock()
        mock_curl_class.return_value = mock_curl

        # Mock successful response
        mock_curl.perform.return_value = None
        mock_curl.getinfo.side_effect = lambda info_type: {
            pycurl.RESPONSE_CODE: 200,
            pycurl.TOTAL_TIME: 0.123,
            pycurl.CONNECT_TIME: 0.050,
            pycurl.SIZE_DOWNLOAD: 456,
            pycurl.HEADER_SIZE: 234,
        }[info_type]

        # Mock response data
        with patch("http_api_tool.verifier.BytesIO") as mock_bytesio:
            response_buffer = Mock()
            header_buffer = Mock()
            response_buffer.getvalue.return_value = b'{"status": "ok"}'
            header_buffer.getvalue.return_value = (
                b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n"
            )

            mock_bytesio.side_effect = [response_buffer, header_buffer]

            result = self.verifier.perform_request(mock_curl)

            assert result["success"] is True
            assert result["http_code"] == 200
            assert result["total_time"] == 0.123
            assert result["connect_time"] == 0.050
            assert result["body_size"] == 456
            assert result["header_size"] == 234
            assert result["response_body"] == b'{"status": "ok"}'
            assert result["curl_error"] is None

    @patch("pycurl.Curl")
    def test_perform_request_curl_error(self, mock_curl_class: Mock) -> None:
        """Test HTTP request with cURL error."""
        mock_curl = Mock()
        mock_curl_class.return_value = mock_curl

        # Mock cURL error
        mock_curl.perform.side_effect = pycurl.error(7, "Failed to connect to host")

        with patch("http_api_tool.verifier.BytesIO") as mock_bytesio:
            response_buffer = Mock()
            header_buffer = Mock()
            response_buffer.getvalue.return_value = b""
            header_buffer.getvalue.return_value = b""

            mock_bytesio.side_effect = [response_buffer, header_buffer]

            result = self.verifier.perform_request(mock_curl)

            assert result["success"] is False
            assert result["http_code"] == 0
            assert result["curl_error"] == (7, "Failed to connect to host")


@pytest.mark.integration
class TestIntegration:
    """Integration tests for the complete verification flow.

    These tests use mocks but test the complete workflow from input validation
    to result output. Response time tests are now covered by testing.yaml
    using a local go-httpbin service to avoid external dependencies.
    """

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.verifier = HTTPAPITester()

    @patch("http_api_tool.verifier.HTTPAPITester.create_curl_handle")
    @patch("http_api_tool.verifier.HTTPAPITester.perform_request")
    def test_test_api_success_immediate(
        self, mock_perform: Mock, mock_create_handle: Mock
    ) -> None:
        """Test successful API verification on first attempt."""
        # Mock curl handle
        mock_curl = Mock()
        mock_create_handle.return_value = mock_curl

        # Mock successful response
        mock_perform.return_value = {
            "success": True,
            "http_code": 200,
            "total_time": 0.123,
            "connect_time": 0.050,
            "body_size": 456,
            "header_size": 234,
            "response_body": b'{"status": "ok"}',
            "response_headers": "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n",
            "header_json": '{"Content-Type": "application/json"}',
            "curl_error": None,
        }

        config = {
            "url": "https://example.com",
            "service_name": "Test API",
            "retries": 3,
            "expected_http_code": 200,
            "initial_sleep_time": 1,
            "max_delay": 30,
            "curl_timeout": 5,
            "http_method": "GET",
            "verify_ssl": True,
            "connection_reuse": True,
            "follow_redirects": True,
            "debug": False,
            "include_response_body": False,
            "max_response_time": 0,
            "fail_on_timeout": False,
        }

        result = self.verifier.test_api(**config)

        assert result["response_http_code"] == 200
        assert result["total_time"] == 0.123
        assert result["connect_time"] == 0.050
        assert result["time_delay"] == 0  # No delay on first attempt

    @patch("http_api_tool.verifier.HTTPAPITester.create_curl_handle")
    @patch("http_api_tool.verifier.HTTPAPITester.perform_request")
    @patch("time.sleep")  # Mock sleep to speed up test
    def test_test_api_success_with_retry(
        self, mock_sleep: Mock, mock_perform: Mock, mock_create_handle: Mock
    ) -> None:
        """Test successful API verification after retries."""
        # Mock curl handle
        mock_curl = Mock()
        mock_create_handle.return_value = mock_curl

        # Mock first attempt failure, second attempt success
        mock_perform.side_effect = [
            {
                "success": False,
                "http_code": 0,
                "total_time": 0,
                "connect_time": 0,
                "body_size": 0,
                "header_size": 0,
                "response_body": b"",
                "response_headers": "",
                "header_json": "{}",
                "curl_error": (7, "Failed to connect"),
            },
            {
                "success": True,
                "http_code": 200,
                "total_time": 0.123,
                "connect_time": 0.050,
                "body_size": 456,
                "header_size": 234,
                "response_body": b'{"status": "ok"}',
                "response_headers": "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n",
                "header_json": '{"Content-Type": "application/json"}',
                "curl_error": None,
            },
        ]

        config = {
            "url": "https://example.com",
            "service_name": "Test API",
            "retries": 3,
            "expected_http_code": 200,
            "initial_sleep_time": 1,
            "max_delay": 30,
            "curl_timeout": 5,
            "http_method": "GET",
            "verify_ssl": True,
            "connection_reuse": True,
            "follow_redirects": True,
            "debug": False,
            "include_response_body": False,
            "max_response_time": 0,
            "fail_on_timeout": False,
        }

        result = self.verifier.test_api(**config)

        assert result["response_http_code"] == 200
        assert result["time_delay"] == 1  # One retry delay

        # Verify sleep was called
        mock_sleep.assert_called_once_with(1)

    @patch("http_api_tool.verifier.HTTPAPITester.create_curl_handle")
    @patch("http_api_tool.verifier.HTTPAPITester.perform_request")
    @patch("time.sleep")
    def test_test_api_with_regex_success(
        self, mock_sleep: Mock, mock_perform: Mock, mock_create_handle: Mock
    ) -> None:
        """Test API verification with successful regex matching."""
        # Mock curl handle
        mock_curl = Mock()
        mock_create_handle.return_value = mock_curl

        # Mock successful response with matching content
        mock_perform.return_value = {
            "success": True,
            "http_code": 200,
            "total_time": 0.123,
            "connect_time": 0.050,
            "body_size": 456,
            "header_size": 234,
            "response_body": b'{"status": "success", "message": "API is working"}',
            "response_headers": "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n",
            "header_json": '{"Content-Type": "application/json"}',
            "curl_error": None,
        }

        config = {
            "url": "https://example.com",
            "service_name": "Test API",
            "retries": 3,
            "expected_http_code": 200,
            "initial_sleep_time": 1,
            "max_delay": 30,
            "curl_timeout": 5,
            "http_method": "GET",
            "verify_ssl": True,
            "connection_reuse": True,
            "follow_redirects": True,
            "debug": False,
            "include_response_body": False,
            "max_response_time": 0,
            "fail_on_timeout": False,
            "regex": r'"status":\s*"success"',
        }

        result = self.verifier.test_api(**config)

        assert result["response_http_code"] == 200
        assert result["regex_match"] is True

    @patch("http_api_tool.verifier.HTTPAPITester.create_curl_handle")
    @patch("http_api_tool.verifier.HTTPAPITester.perform_request")
    def test_test_api_response_time_exceeded(
        self, mock_perform: Mock, mock_create_handle: Mock
    ) -> None:
        """Test API verification with response time exceeded."""
        # Mock curl handle
        mock_curl = Mock()
        mock_create_handle.return_value = mock_curl

        # Mock slow response
        mock_perform.return_value = {
            "success": True,
            "http_code": 200,
            "total_time": 5.0,  # Slow response
            "connect_time": 0.050,
            "body_size": 456,
            "header_size": 234,
            "response_body": b'{"status": "ok"}',
            "response_headers": "HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n",
            "header_json": '{"Content-Type": "application/json"}',
            "curl_error": None,
        }

        config = {
            "url": "https://example.com",
            "service_name": "Test API",
            "retries": 3,
            "expected_http_code": 200,
            "initial_sleep_time": 1,
            "max_delay": 30,
            "curl_timeout": 5,
            "http_method": "GET",
            "verify_ssl": True,
            "connection_reuse": True,
            "follow_redirects": True,
            "debug": False,
            "include_response_body": False,
            "max_response_time": 2.0,  # 2 second limit
            "fail_on_timeout": False,
        }

        result = self.verifier.test_api(**config)

        assert result["response_http_code"] == 200
        assert result["response_time_exceeded"] is True

    @patch("http_api_tool.verifier.HTTPAPITester.create_curl_handle")
    @patch("http_api_tool.verifier.HTTPAPITester.perform_request")
    @patch("time.sleep")
    def test_test_api_exhausted_retries(
        self, mock_sleep: Mock, mock_perform: Mock, mock_create_handle: Mock
    ) -> None:
        """Test API verification with exhausted retries."""
        # Mock curl handle
        mock_curl = Mock()
        mock_create_handle.return_value = mock_curl

        # Mock consistent failures
        mock_perform.return_value = {
            "success": False,
            "http_code": 0,
            "total_time": 0,
            "connect_time": 0,
            "body_size": 0,
            "header_size": 0,
            "response_body": b"",
            "response_headers": "",
            "header_json": "{}",
            "curl_error": (7, "Failed to connect"),
        }

        config = {
            "url": "https://example.com",
            "service_name": "Test API",
            "retries": 2,
            "expected_http_code": 200,
            "initial_sleep_time": 1,
            "max_delay": 30,
            "curl_timeout": 5,
            "http_method": "GET",
            "verify_ssl": True,
            "connection_reuse": True,
            "follow_redirects": True,
            "debug": False,
            "include_response_body": False,
            "max_response_time": 0,
            "fail_on_timeout": False,
        }

        with pytest.raises(SystemExit):
            self.verifier.test_api(**config)

    # NOTE: Response time testing is now covered by the testing.yaml workflow
    # using a local go-httpbin service to avoid external dependencies in unit tests.


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
