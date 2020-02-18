#!/bin/bash

set -eu
set -o pipefail

docker-compose build && docker-compose up --abort-on-container-exit \
    codedrunk_xero_uniclient \
    codedrunk_xero_uniworker
