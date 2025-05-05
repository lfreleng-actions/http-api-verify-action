#!/bin/bash

# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

# Test script to verify the POST request fix
# This simulates the exact scenario from the GitHub Actions workflow

set -e

echo "Testing POST request with JSON headers and body - FIXED VERSION 🔧"

# Simulate the exact inputs from the failing GitHub Actions test
request_headers='{"X-Custom-Header": "test-value", "X-Test-ID": "12345"}'
request_body='{"test": "data", "timestamp": "2025-05-28"}'
content_type='application/json'
http_method='POST'
curl_timeout=5

echo "Test inputs:"
echo "  request_headers: $request_headers"
echo "  request_body: $request_body"
echo "  content_type: $content_type"
echo "  http_method: $http_method"

# Build the curl command exactly as the action.yaml does (with the fix)
curl_cmd="curl -s --max-time $curl_timeout -X $http_method"

# Request body and content type
if [ -n "$request_body" ]; then
  curl_cmd="$curl_cmd -H 'Content-Type: $content_type' -d '$request_body'"
fi

# Custom headers (using the FIXED syntax)
if [ -n "$request_headers" ]; then
  echo "Adding custom send header JSON 📋"
  # Process headers one by one to avoid command line issues
  while IFS= read -r header_arg; do
    curl_cmd="$curl_cmd $header_arg"
  done < <(echo "$request_headers" | jq -r 'to_entries[] | "-H \"" + .key + ": " + .value + "\""')
fi

echo ""
echo "Generated curl command:"
echo "$curl_cmd"

# Test with httpbin.org endpoint
url="https://httpbin.org/post"
echo ""
echo "Testing with URL: $url"

# Execute the command
echo "Executing curl command..."
if eval "$curl_cmd $url" >/dev/null 2>&1; then
  echo ""
  echo "✅ SUCCESS: POST request with JSON headers completed successfully!"
  echo "✅ The curl command is properly formed and executed without URL malformation errors"
  echo ""
  echo "Sample output:"
  eval "$curl_cmd $url" | head -10
else
  echo ""
  echo "❌ FAILED: POST request failed"
  exit 1
fi
