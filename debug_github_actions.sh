#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2024 Mode Seven Ltd <info@modeseven.io>

# Debug script to simulate exact GitHub Actions environment
set -euo pipefail

echo "=== GitHub Actions Environment Debug Test ==="

# Set the exact environment variables from GitHub Actions
export INPUT_REQUEST_HEADERS='{"X-Custom-Header": "test-value", "X-Test-ID": "12345"}'

echo "Raw INPUT_REQUEST_HEADERS: '$INPUT_REQUEST_HEADERS'"

# Test jq parsing exactly as it appears in the action
echo "Testing jq parsing:"
echo "$INPUT_REQUEST_HEADERS" | jq -r 'to_entries[] | "-H \"" + .key + ": " + .value + "\""'

echo "=== Testing curl command construction ==="

# Build headers array exactly like the action
declare -a headers_array
while IFS= read -r header_flag; do
    headers_array+=("$header_flag")
    echo "Added header: $header_flag"
done < <(echo "$INPUT_REQUEST_HEADERS" | jq -r 'to_entries[] | "-H \"" + .key + ": " + .value + "\""')

echo "Headers array:"
for header in "${headers_array[@]}"; do
    echo "  $header"
done

# Build curl command
curl_cmd="curl --silent --show-error --location"
curl_cmd+=" --write-out '%{response_code}|%{size_header}|%{size_download}|%{time_total}'"
curl_cmd+=" --request POST"

# Add headers
for header in "${headers_array[@]}"; do
    curl_cmd+=" $header"
done

curl_cmd+=" -H \"Content-Type: application/json\""
curl_cmd+=" --data '{\"test\": \"data\", \"timestamp\": \"2025-05-28\"}'"
curl_cmd+=" \"https://httpbin.org/post\""

echo ""
echo "Final curl command:"
echo "$curl_cmd"

echo ""
echo "Executing..."
eval "$curl_cmd"
