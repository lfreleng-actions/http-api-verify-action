#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

# Test the action directly with PUT request inputs
echo "=== Testing Action with PUT Request Inputs ==="

# Set environment variables like GitHub Actions would
export INPUT_URL="https://httpbin.org/put"
export INPUT_SERVICE_NAME="HTTPBin PUT Endpoint"
export INPUT_HTTP_METHOD="PUT"
export INPUT_REQUEST_BODY='{"updated": true, "version": 2}'
export INPUT_EXPECTED_HTTP_CODE="200"
export INPUT_DEBUG="true"

# Mock GITHUB_OUTPUT and GITHUB_STEP_SUMMARY
export GITHUB_OUTPUT="/tmp/github_output"
export GITHUB_STEP_SUMMARY="/tmp/github_summary"

# Create temporary files
touch "$GITHUB_OUTPUT"
touch "$GITHUB_STEP_SUMMARY"

echo "Environment variables set:"
echo "  INPUT_URL: $INPUT_URL"
echo "  INPUT_HTTP_METHOD: $INPUT_HTTP_METHOD"
echo "  INPUT_REQUEST_BODY: $INPUT_REQUEST_BODY"
echo "  INPUT_EXPECTED_HTTP_CODE: $INPUT_EXPECTED_HTTP_CODE"
echo ""

# Extract and run just the relevant shell code from action.yaml
# This simulates what would happen in the GitHub Action environment

# Set defaults like in the action
url="${INPUT_URL}"
http_method="${INPUT_HTTP_METHOD:-GET}"
request_body="${INPUT_REQUEST_BODY}"
expected_http_code="${INPUT_EXPECTED_HTTP_CODE:-200}"

echo "Processing variables:"
echo "  url: $url"
echo "  http_method: $http_method"
echo "  request_body: $request_body"
echo "  expected_http_code: $expected_http_code"
echo ""

# Build curl command (simplified version of action logic)
curl_cmd="curl -s --max-time 5"
curl_cmd="$curl_cmd -X $http_method"

# Add body if provided
if [ -n "$request_body" ]; then
    content_type="application/json"
    curl_cmd="$curl_cmd -H 'Content-Type: $content_type' -d '$request_body'"
fi

# Add redirects
curl_cmd="$curl_cmd -L"

echo "Built curl command: $curl_cmd"
echo ""

# Execute the command using our fix
output_string="TOTAL_TIME:%{time_total}|CONNECT_TIME:%{time_connect}|HTTP_CODE:%{http_code}|BODY_SIZE:%{size_download}|HEADER_SIZE:%{size_header}|HEADER_JSON:%{header_json}"

echo "Executing command with eval (the fix)..."
set +e
curl_output=$(eval "$curl_cmd -w \"$output_string\" \"${url}\" -o response_body" 2>/dev/null)
curl_exit_code=$?
set -e

echo "Exit code: $curl_exit_code"
echo "Output: $curl_output"

if [ $curl_exit_code -eq 0 ]; then
    echo "✅ PUT request successful!"

    # Parse output like the action does
    http_code=$(echo "$curl_output" | grep -o 'HTTP_CODE:[0-9]*' | cut -d: -f2)
    total_time=$(echo "$curl_output" | grep -o 'TOTAL_TIME:[0-9.]*' | cut -d: -f2)

    echo "HTTP Code: $http_code"
    echo "Total Time: $total_time"

    if [ "$http_code" = "$expected_http_code" ]; then
        echo "✅ HTTP code matches expected ($expected_http_code)"
    else
        echo "❌ HTTP code mismatch: expected $expected_http_code, got $http_code"
    fi

    if [ -f response_body ]; then
        echo ""
        echo "Response body:"
        cat response_body
    fi
else
    echo "❌ PUT request failed with exit code $curl_exit_code"
fi

# Cleanup
rm -f response_body "$GITHUB_OUTPUT" "$GITHUB_STEP_SUMMARY"

echo ""
echo "=== PUT Action Test Complete ==="
