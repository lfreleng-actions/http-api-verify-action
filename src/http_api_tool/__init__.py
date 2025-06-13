# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

"""
HTTP API Test Tool - A Python tool for HTTP/HTTPS API testing.

This package can be used both as a CLI tool (using Typer) and as a GitHub Action.
It uses pycurl for HTTP requests to avoid the shell escaping issues of the
original implementation.
"""

__version__ = "1.0.0"

from .cli import app, main
from .verifier import HTTPAPITester

__all__ = ["HTTPAPITester", "app", "main", "__version__"]
