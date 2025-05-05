<!--
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# 🛠️ Check HTTP API Service Availability

Tests an HTTP/HTTPS API endpoint for service availability.

## http-api-verify-action

## Usage Example

<!-- markdownlint-disable MD046 -->

```yaml
steps:
  - name: 'Check HTTP/HTTP API service'
    uses: lfreleng-actions/http-api-verify-action@main
    with:
      url: 'http://127.0.0.1:8080/index.yaml'
      auth_string: "-u chartmuseum:${{ secrets.github_token }}"
```

<!-- markdownlint-enable MD046 -->

## Inputs

<!-- markdownlint-disable MD013 -->

| Name         | Required | Default     | Description                                             |
| ------------ | -------- | ----------- | ------------------------------------------------------- |
| url          | True     |             | URL of HTTP/HTTPS API server to check                   |
| auth_string  | False    |             | Authentication string in cURL format                    |
| service_name | False    | API Service | Friendly name for tested HTTP/HTTPS API service         |
| delay        | False    | 1           | Time in seconds between API service connection attempts |
| retries      | False    | 90          | Number of retries before declaring service unavailable  |
| http_code    | False    | 200         | HTTP response code to accept from the API service       |
| regex        | False    |             | Verify server response with regular expression          |

<!-- markdownlint-enable MD013 -->

## Outputs

<!-- markdownlint-disable MD013 -->

| Name      | Description                                           |
| --------- | ----------------------------------------------------- |
| retries   | Number of retries until server became available       |
| http_code | Final HTTP response code received from the API server |

<!-- markdownlint-enable MD013 -->

## Implementation Details

Uses: [cURL](https://curl.se/)

A command line tool and library for transferring data with URLs.
