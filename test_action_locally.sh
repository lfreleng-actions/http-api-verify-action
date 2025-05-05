#!/bin/bash

# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

# Test script to run the action locally exactly as GitHub Actions would

set -e

echo "Testing GitHub Action locally with POST request and custom headers..."

# Export environment variables that GitHub Actions would set
export GITHUB_STEP_SUMMARY="/tmp/github_step_summary.txt"
export GITHUB_OUTPUT="/tmp/github_output.txt"

# Clean up previous runs
rm -f "$GITHUB_STEP_SUMMARY" "$GITHUB_OUTPUT"
touch "$GITHUB_STEP_SUMMARY" "$GITHUB_OUTPUT"

echo "🔧 Testing the exact same scenario as the failing GitHub Actions workflow"

# Set the inputs exactly as in the workflow
export INPUT_URL="https://httpbin.org/post"
export INPUT_SERVICE_NAME="HTTPBin POST Endpoint"
export INPUT_HTTP_METHOD="POST"
export INPUT_REQUEST_BODY='{"test": "data", "timestamp": "2025-05-28"}'
export INPUT_CONTENT_TYPE="application/json"
export INPUT_REQUEST_HEADERS='{"X-Custom-Header": "test-value", "X-Test-ID": "12345"}'
export INPUT_INCLUDE_RESPONSE_BODY="true"
export INPUT_DEBUG="true"

echo "Input values:"
echo "  URL: $INPUT_URL"
echo "  HTTP_METHOD: $INPUT_HTTP_METHOD"
echo "  REQUEST_HEADERS: $INPUT_REQUEST_HEADERS"
echo "  REQUEST_BODY: $INPUT_REQUEST_BODY"

# Run the validation step
echo ""
echo "=== Running Validation Step ==="
bash -c "$(sed -n '/- name.*Validate inputs/,/- name/p' action.yaml | sed '1d;$d' | sed 's/^        //')"

# Run the main check step
echo ""
echo "=== Running Main Check Step ==="
bash -c "$(sed -n '/- name.*Check API\/Service Availability/,/^$/p' action.yaml | sed '1,4d' | sed 's/^        //')"

echo ""
echo "=== Results ==="
echo "Step Summary:"
cat "$GITHUB_STEP_SUMMARY"
echo ""
echo "Outputs:"
cat "$GITHUB_OUTPUT"

# Clean up
rm -f "$GITHUB_STEP_SUMMARY" "$GITHUB_OUTPUT"
