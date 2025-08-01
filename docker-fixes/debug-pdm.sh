#!/bin/bash
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

# Debug script to diagnose PDM segmentation fault issues
# This script helps identify the root cause of PDM crashes during Docker builds

set -e

echo "=== PDM Segfault Debug Script ==="
echo "Timestamp: $(date)"
echo "Host: $(hostname)"
echo "User: $(whoami)"
echo

# Check system resources
echo "=== System Information ==="
echo "Memory:"
free -h
echo
echo "Disk space:"
df -h
echo
echo "CPU info:"
nproc
echo

# Check Python environment
echo "=== Python Environment ==="
echo "Python version:"
python3 --version
python3 -c "import sys; print(f'Python executable: {sys.executable}')"
echo
echo "Python path:"
python3 -c "import sys; print('\n'.join(sys.path))"
echo

# Check PDM installation
echo "=== PDM Information ==="
if command -v pdm >/dev/null 2>&1; then
    echo "PDM version:"
    pdm --version
    echo
    echo "PDM info:"
    pdm info
    echo
    echo "PDM cache location:"
    pdm config cache_dir
else
    echo "PDM not found in PATH"
fi
echo

# Check for existing virtual environments
echo "=== Virtual Environment Check ==="
if [ -d "/app/.venv" ]; then
    echo "Virtual environment exists at /app/.venv"
    ls -la /app/.venv/
else
    echo "No virtual environment found at /app/.venv"
fi
echo

# Check project files
echo "=== Project Files ==="
echo "Current directory: $(pwd)"
echo "Files in current directory:"
ls -la
echo
if [ -f "pyproject.toml" ]; then
    echo "pyproject.toml exists"
    echo "Python version requirement:"
    grep -A5 "requires-python" pyproject.toml || echo "requires-python not found"
else
    echo "pyproject.toml not found"
fi
echo
if [ -f "pdm.lock" ]; then
    echo "pdm.lock exists"
    echo "Lock file size: $(wc -l < pdm.lock) lines"
    echo "Lock file version:"
    head -10 pdm.lock | grep -E "(lock_version|content_hash)" || echo "Version info not found"
else
    echo "pdm.lock not found"
fi
echo

# Check dependencies that might cause issues
echo "=== Dependency Analysis ==="
if [ -f "pyproject.toml" ]; then
    echo "Dependencies from pyproject.toml:"
    grep -A10 "dependencies" pyproject.toml | grep -E "(pycurl|typer|certifi|requests)" || echo "Core dependencies not found"
fi
echo

# Test basic PDM commands
echo "=== PDM Command Tests ==="
export PDM_IGNORE_SAVED_PYTHON=1
export PDM_USE_VENV=1
export PDM_PYTHON=/usr/local/bin/python3.11

echo "Testing PDM info (should not crash):"
if timeout 30 pdm info >/dev/null 2>&1; then
    echo "✓ PDM info command works"
else
    echo "✗ PDM info command failed or timed out"
fi

echo "Testing PDM list (with timeout):"
if timeout 30 pdm list >/dev/null 2>&1; then
    echo "✓ PDM list command works"
else
    echo "✗ PDM list command failed or timed out"
fi

echo "Testing PDM install --dry-run:"
if timeout 60 pdm install --dry-run --prod --no-isolation --no-self >/dev/null 2>&1; then
    echo "✓ PDM dry-run works"
else
    echo "✗ PDM dry-run failed or timed out"
fi
echo

# Check for known problematic packages
echo "=== Package Compatibility Check ==="
echo "Checking for packages known to cause segfaults:"
if [ -f "pdm.lock" ]; then
    echo "Checking for numpy/scipy (can cause memory issues):"
    grep -i "numpy\|scipy" pdm.lock || echo "No numpy/scipy found"
    echo "Checking for pycurl version:"
    grep -A5 "name = \"pycurl\"" pdm.lock || echo "pycurl not found in lock"
fi
echo

# Memory and limits check
echo "=== Resource Limits ==="
echo "Current ulimits:"
ulimit -a
echo
echo "Available memory:"
grep -E "(MemTotal|MemAvailable|MemFree)" /proc/meminfo
echo

# Suggest fixes
echo "=== Suggested Fixes ==="
echo "1. Clear PDM cache: rm -rf ~/.cache/pdm/* /root/.cache/pdm/*"
echo "2. Use memory limits: ulimit -v 2097152"
echo "3. Use timeout: timeout 300 pdm install ..."
echo "4. Try pip fallback: pip install pycurl typer[all] certifi requests"
echo "5. Use --no-lock flag to avoid lock file corruption"
echo "6. Check if running out of memory during pycurl compilation"
echo

echo "=== End Debug Report ==="
