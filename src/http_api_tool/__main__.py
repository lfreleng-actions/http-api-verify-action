#!/usr/bin/env python3

# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
Entry point script for http-api-tool.

This script provides the main entry point that can be used both as a CLI tool
and as a GitHub Action.
"""

from http_api_tool import main

if __name__ == "__main__":
    main()
