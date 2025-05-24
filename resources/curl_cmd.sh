#!/usr/bin/env bash

# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

# Sample script forms the basis of the cURL/action code

curl_cmd=$(which curl || true)
if [ ! -x "$curl_cmd" ]; then
  echo 'Error: cURL command not found ❌'; exit 1
fi

# Function to compare version numbers
# https://unix.stackexchange.com/questions/285924/how-to-compare-a-programs-version-in-a-shell-script

# Utility function to compare version strings
compare_versions()
{
  for i in 1 2 3
  do
    part1=$(echo "$1" | cut -d "." -f $i)
    part2=$(echo "$2" | cut -d "." -f $i)
    if [ "$part1" -lt "$part2" ]
    then
      return 0
    fi
  done
  return 1
}

# Ensure cURL version at least 8.3.0
curl_version=$(curl --version | head -1 | awk '{print $2}')

if (compare_versions "$curl_version" "8.3.0"); then
  echo "Error: runner must have cURL version >= 8.3.0 ❌"; exit 1
else
  echo "cURL version: $curl_version ✅"
fi

url="https://www.linuxfoundation.org"

# Parameters/metadata to capture with cURL in addition to the response body
# header_json - header as JSON output
# http_code - web server HTTP response code (e.g., 200, 404, etc.)
# size_download - total bytes downloaded; the size of the body/data without headers
# size_header - total amount of bytes of the downloaded headers
cleanupTempFiles() {
  rm -f header_json http_code size_download size_header response_body
  echo "Cleaned up temporary files"
}
trap "cleanupTempFiles" EXIT ERR

curl -si -w \
  "%output{header_json}%{header_json}%output{http_code}%{http_code}%output{size_download}%{size_download}%output{size_header}%{size_header}" \
  "${url}" -o response_body
http_code=$(<http_code)
size_download=$(<size_download)
size_header=$(<size_header)
echo "http_code: $http_code"
echo "size_download: $size_download"
echo "size_header: $size_header"
# Disabled except when degugging
# header=$(head -c "$size_header" response_body)
# body=$(tail -c "$size_download" response_body)

# Show header (smaller, but demonstrates most of the above is working)
echo "Header JSON:"
jq -r '.' header_json
