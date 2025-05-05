#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2024 Mode Seven Ltd <info@modeseven.io>

echo "=== Testing Debug Mode Functionality ==="

# Test with debug=false (should show minimal output)
echo
echo "--- Testing with debug=false ---"
cd /Users/mwatkins/Repositories/modeseven-lfreleng-actions/http-api-verify-action || exit
export GITHUB_ACTIONS=true

# Simulate the action with debug=false
bash -c '
  # Simulate action inputs
  export GITHUB_OUTPUT=/tmp/test_output_false
  touch "$GITHUB_OUTPUT"

  # Extract the main logic from action.yaml
  debug="false"
  debug_lower=$(echo "$debug" | tr "[:upper:]" "[:lower:]")

  echo "Debug mode: $debug (normalized: $debug_lower)"

  # Test debug conditional
  if [ "f$debug_lower" = "ftrue" ]; then
    echo "🔍 This debug message should NOT appear"
  else
    echo "✅ Debug mode is OFF - debug messages hidden"
  fi
'

echo
echo "--- Testing with debug=true ---"

# Simulate the action with debug=true
bash -c '
  # Simulate action inputs
  export GITHUB_OUTPUT=/tmp/test_output_true
  touch "$GITHUB_OUTPUT"

  # Extract the main logic from action.yaml
  debug="true"
  debug_lower=$(echo "$debug" | tr "[:upper:]" "[:lower:]")

  echo "Debug mode: $debug (normalized: $debug_lower)"

  # Test debug conditional
  if [ "f$debug_lower" = "ftrue" ]; then
    echo "🔍 This debug message SHOULD appear"
  else
    echo "❌ Debug mode should be ON but conditional failed"
  fi
'

echo
echo "=== Debug Mode Test Complete ==="
