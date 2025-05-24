<!--
# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation
-->

# 🛠️ Check API/Service Availability

Tests an HTTP/HTTPS API endpoint for service availability.

## http-api-verify-action

## Usage Example

<!-- markdownlint-disable MD046 -->

```yaml
steps:
  - name: 'Check API service availability'
    uses: lfreleng-actions/http-api-verify-action@main
    with:
      url: 'http://127.0.0.1:8080/index.yaml'
      auth_string: "chartmuseum:${{ secrets.github_token }}"
```

<!-- markdownlint-enable MD046 -->

## Inputs

<!-- markdownlint-disable MD013 -->

| Name               | Required | Default     | Description                                              |
| ------------------ | -------- | ----------- | -------------------------------------------------------- |
| url                | False    |             | URL of API server/interface to check                     |
| auth_string        | False    |             | Authentication string, colon separated username/password |
| service_name       | False    | API Service | Name of HTTP/HTTPS API service tested                    |
| initial_sleep_time | False    | 1           | Time in seconds between API service connection attempts  |
| retries            | False    | 60          | Number of retries before declaring service unavailable   |
| expected_http_code | False    | 200         | HTTP response code to accept from the API service        |
| regex              | False    |             | Verify server response with regular expression           |
| show_header_json   | False    | false       | Dumps headers as jq/colourised JSON output               |
| debug              | False    | false       | Enables cURL/action debugging                            |

## Notes on Inputs

You can provide the URL as either an explicit input, or from the environment
variable HTTP_API_URL. The regex input passes an extended regular expression
to grep using "-E"

### Authentication

Provide credentials either as an input or embedded in the URL string.

Pass the auth_string input in the format used natively by cURL, e.g.:

`username:password`

<!-- markdownlint-enable MD013 -->

## Outputs

<!-- markdownlint-disable MD013 -->

| Name                 | Description                                             |
| -------------------- | ------------------------------------------------------- |
| startup_delay        | Number of seconds waiting for availability/failure      |
| response_http_code   | HTTP response code received from the server             |
| response_header      | HTTP response header received from the server           |
| response_header_json | HTTP response header received from the server as JSON   |
| response_header_size | HTTP response header size in bytes                      |
| response_body_size   | HTTP response body size in bytes                        |
| regex_match          | Whether the regular expression matched the server reply |

<!-- markdownlint-enable MD013 -->

## Implementation Details

Refer to the homepage/documentation: [https://curl.se/](https://curl.se/)

A command line tool and library for transferring data with URLs.
