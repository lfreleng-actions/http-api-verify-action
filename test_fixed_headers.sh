#!/bin/bash

# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

# Test the fixed JSON header processing

set -e

echo "Testing fixed JSON header processing..."

# Simulate the input
request_headers='{"X-Custom-Header": "test-value", "X-Test-ID": "12345"}'

# Test the fixed logic
curl_cmd="curl -s --max-time 5 -X POST"

if [ -n "$request_headers" ]; then
  echo "Adding custom send header JSON 📋"
  # Process headers one by one to avoid command line issues
  while IFS= read -r header_arg; do
    curl_cmd="$curl_cmd $header_arg"
  done < <(echo "$request_headers" | jq -r 'to_entries[] | "-H \"" + .key + ": " + .value + "\""')
fi

echo "Final curl command: $curl_cmd"

# Test with a simple request to verify the command is well-formed
echo "Testing command syntax..."
url="https://httpbin.org/post"
echo "Running: $curl_cmd -d '{\"test\": \"data\"}' $url"

# Execute the command
eval "$curl_cmd -d '{\"test\": \"data\"}' $url" | head -20
echo "✅ Command executed successfully!"
