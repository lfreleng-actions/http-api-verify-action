#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2024 Mode Seven Ltd <info@modeseven.io>

# Test script that exactly mimics the action's curl command construction
set -euo pipefail

echo "=== Testing Action's Exact Curl Command Construction ==="

# Simulate exact GitHub Actions inputs
url="https://httpbin.org/post"
curl_timeout="5"
http_method="POST"
request_body='{"test": "data", "timestamp": "2025-05-28"}'
content_type="application/json"
request_headers='{"X-Custom-Header": "test-value", "X-Test-ID": "12345"}'

echo "Input variables:"
echo "  url: $url"
echo "  http_method: $http_method"
echo "  request_body: $request_body"
echo "  content_type: $content_type"
echo "  request_headers: $request_headers"

echo ""
echo "=== Building curl command exactly like the action ==="

# Base command with core options (exactly like action.yaml line 328)
curl_cmd="curl -s --max-time $curl_timeout -X $http_method"
echo "1. Base command: $curl_cmd"

# Request body and content type (like action.yaml lines 330-334, but fixed)
if [ -n "$request_body" ]; then
  echo "::add-mask::$request_body"
  curl_cmd="$curl_cmd -H 'Content-Type: $content_type'"
  curl_cmd="$curl_cmd -d '$request_body'"
  echo "2. After adding body: $curl_cmd"
fi

# Custom headers (exactly like action.yaml lines 336-342)
if [ -n "$request_headers" ]; then
  echo "Adding custom send header JSON 📋"
  # Process headers one by one to avoid command line issues
  while IFS= read -r header_arg; do
    curl_cmd="$curl_cmd $header_arg"
    echo "   Added header: $header_arg"
  done < <(echo "$request_headers" | jq -r 'to_entries[] | "-H \"" + .key + ": " + .value + "\""')
  echo "3. After adding headers: $curl_cmd"
fi

# Add SSL options (like the action)
curl_cmd="$curl_cmd -L"
echo "4. After adding redirects: $curl_cmd"

# Output format string for parsing response data
output_string="TOTAL_TIME:%{time_total}|CONNECT_TIME:%{time_connect}|HTTP_CODE:%{http_code}|BODY_SIZE:%{size_download}|HEADER_SIZE:%{size_header}|HEADER_JSON:%{header_json}"

echo ""
echo "=== Final command construction ==="
final_cmd="$curl_cmd -w \"$output_string\" \"$url\" -o response_body"
echo "Full command: $final_cmd"

echo ""
echo "=== Executing the command ==="
# Run the command exactly as the action would
curl_output=$(eval "$final_cmd" 2>/dev/null)
curl_exit_code=$?

echo "Exit code: $curl_exit_code"
if [ $curl_exit_code -eq 0 ]; then
  echo "✅ SUCCESS! Command executed without URL malformed error"
  echo "Response data: $curl_output"
  if [ -f response_body ]; then
    echo "Response body received:"
    head -20 response_body
  fi
else
  echo "❌ FAILED with exit code: $curl_exit_code"
  case $curl_exit_code in
    3) echo "Error: URL malformed ❌" ;;
    *) echo "Error: Other curl error" ;;
  esac
fi

# Clean up
rm -f response_body
