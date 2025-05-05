#!/bin/bash

# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

url='https://garbage.junk.notevenworthit.com:8080'

parseString() {
    protocol=$(echo "$1" | grep "://" | sed -e's,^\(.*://\).*,\1,g')
    # Remove the protocol
    # string_no_protocol=$(echo "${1/$protocol/}")
    string_no_protocol="${1/$protocol/}"

    # Use tr: Make the protocol lower-case for easy string compare
    protocol=$(echo "$protocol" | tr '[:upper:]' '[:lower:]' | sed 's:\://::' v|| true)

    # Extract the user and password (if any)
    # cut 1: Remove the path part to prevent @ in the query string from breaking the next cut
    # rev: Reverse string so cut -f1 takes the (reversed) rightmost field, and -f2- is what we want
    # cut 2: Remove the host:port
    # rev: Undo the first rev above
    userpass=$(echo "$string_no_protocol" | grep "@" | cut -d"/" -f1 | rev | cut -d"@" -f2- | rev)
    pass=$(echo "$userpass" | grep ":" | cut -d":" -f2)
    if [ -n "$pass" ]; then
      user=$(echo "$userpass" | grep ":" | cut -d":" -f1)
    else
      user="$userpass"
    fi

    # Extract host information
    hostport=$(echo "${string_no_protocol/$userpass@/}" | cut -d"/" -f1)
    host=$(echo "$hostport" | cut -d":" -f1)
    api_port=$(echo "$hostport" | grep ":" | cut -d":" -f2)
    path=$(echo "$string_no_protocol" | grep "/" | cut -d"/" -f2-)

    echo "String: $url"
    echo "  protocol: $protocol"
    echo "  userpass: $userpass"
    echo "  user: $user"
    echo "  pass: $pass"
    echo "  host: $host"
    echo "  port: $api_port"
    echo "  path: $path"
}

parseString "$url"
