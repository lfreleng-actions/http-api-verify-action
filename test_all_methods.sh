#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

# Comprehensive test of all HTTP methods
echo "=== Comprehensive HTTP Method Testing ==="

# Function to test an HTTP method
test_http_method() {
    local method="$1"
    local url="$2"
    local body="$3"
    local expected_code="$4"

    echo ""
    echo "--- Testing $method ---"

    # Build curl command
    curl_cmd="curl -s --max-time 10 -X $method"

    # Add body for POST/PUT/PATCH
    if [ -n "$body" ]; then
        curl_cmd="$curl_cmd -H 'Content-Type: application/json' -d '$body'"
    fi

    # Add redirects
    curl_cmd="$curl_cmd -L"

    echo "Command: $curl_cmd -w \"HTTP_CODE:%{http_code}\" \"$url\""

    # Execute with eval (our fix)
    result=$(eval "$curl_cmd -w \"HTTP_CODE:%{http_code}\" \"$url\" -o response_body_$method" 2>/dev/null)
    exit_code=$?

    echo "Exit code: $exit_code"
    echo "Result: $result"

    if [ $exit_code -eq 0 ]; then
        # Extract HTTP code
        http_code=$(echo "$result" | grep -o 'HTTP_CODE:[0-9]*' | cut -d: -f2)
        if [ "$http_code" = "$expected_code" ]; then
            echo "✅ $method test PASSED (HTTP $http_code)"
        else
            echo "⚠️  $method test WARNING: Expected HTTP $expected_code, got $http_code"
        fi

        # Show a sample of the response
        if [ -f "response_body_$method" ]; then
            echo "Response preview:"
            head -5 "response_body_$method"
        fi
    else
        echo "❌ $method test FAILED (exit code $exit_code)"
    fi
}

# Test all methods from the workflow
echo "Testing HTTP methods as defined in GitHub Actions workflow..."

test_http_method "GET" "https://httpbin.org/get" "" "200"
test_http_method "POST" "https://httpbin.org/post" '{"test": "data", "timestamp": "2025-05-28"}' "200"
test_http_method "PUT" "https://httpbin.org/put" '{"updated": true, "version": 2}' "200"
test_http_method "DELETE" "https://httpbin.org/delete" "" "200"
test_http_method "PATCH" "https://httpbin.org/patch" '{"patch": "data"}' "200"

# Test status codes
echo ""
echo "--- Testing Custom Status Codes ---"
test_http_method "GET" "https://httpbin.org/status/201" "" "201"
test_http_method "GET" "https://httpbin.org/status/302" "" "302"
test_http_method "GET" "https://httpbin.org/status/404" "" "404"

echo ""
echo "=== All HTTP Method Tests Complete ==="

# Cleanup
rm -f response_body_*
