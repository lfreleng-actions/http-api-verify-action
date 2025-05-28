#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

# Test the PUT request exactly as defined in the workflow
echo "=== Testing PUT Request ===";

# Mirror the action.yaml logic exactly
function process_headers() {
    local headers_json="$1"

    if [ -n "$headers_json" ]; then
        echo "Processing headers: $headers_json"

        # Create temp file for headers processing
        temp_headers_file=$(mktemp)

        # Process headers
        echo "$headers_json" | jq -r 'to_entries | .[] | "-H \"" + .key + ": " + .value + "\""' > "$temp_headers_file"

        # Read back processed headers
        cat "$temp_headers_file"

        # Clean up
        rm -f "$temp_headers_file"
    fi
}

# Test inputs from workflow
url="https://httpbin.org/put"
http_method="PUT"
request_body='{"updated": true, "version": 2}'
content_type="application/json"
expected_http_code="200"

echo "Input variables:"
echo "  url: $url"
echo "  http_method: $http_method"
echo "  request_body: $request_body"
echo "  expected_http_code: $expected_http_code"
echo ""

# Build curl command exactly like action
curl_cmd="curl -s --max-time 5"
curl_cmd="$curl_cmd -X $http_method"

# Add body if provided
if [ -n "$request_body" ]; then
    # Default content type to application/json if not specified but body is provided
    if [ -z "$content_type" ]; then
        content_type="application/json"
    fi
    curl_cmd="$curl_cmd -H 'Content-Type: $content_type' -d '$request_body'"
fi

# Add redirects (default behavior)
curl_cmd="$curl_cmd -L"

echo "Built curl command: $curl_cmd"
echo ""

# Test the command construction
output_string="TOTAL_TIME:%{time_total}|HTTP_CODE:%{http_code}"
full_command="$curl_cmd -w \"$output_string\" \"$url\" -o response_body"

echo "Full command to execute:"
echo "$full_command"
echo ""

# Test with eval (the fix)
echo "=== Testing with eval (the fixed approach) ==="
eval_result=$(eval "$curl_cmd -w \"$output_string\" \"$url\" -o response_body" 2>/dev/null)
eval_exit_code=$?
echo "Exit code: $eval_exit_code"
echo "Output: $eval_result"

if [ $eval_exit_code -eq 0 ]; then
    echo "✅ PUT request successful!"
    if [ -f response_body ]; then
        echo "Response body:"
        head -20 response_body
    fi
else
    echo "❌ PUT request failed!"
fi

# Clean up
rm -f response_body

echo ""
echo "=== PUT Test Complete ==="
