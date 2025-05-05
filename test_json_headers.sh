#!/bin/bash

# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

# Test script to reproduce the JSON header processing issue

set -e

# Simulate the input that's causing the problem
request_headers='{"X-Custom-Header": "test-value", "X-Test-ID": "12345"}'

echo "Original request_headers: $request_headers"

# This is the current processing logic from action.yaml
if [ -n "$request_headers" ]; then
  echo "Adding custom send header JSON 📋"
  headers_output=$(echo "$request_headers" | jq -r 'to_entries[] | "-H \"" + .key + ": " + .value + "\""')
  echo "jq output:"
  echo "$headers_output"

  echo "Building curl command..."
  curl_cmd="curl -s --max-time 5 -X POST"
  curl_cmd="$curl_cmd $headers_output"

  echo "Final curl command: $curl_cmd"

  # Test URL formatting
  url="https://httpbin.org/post"
  echo "Testing with URL: $url"

  # This will likely fail with URL malformed error
  echo "Attempting to execute..."
  eval "$curl_cmd $url" || echo "Error executing curl command"
fi
