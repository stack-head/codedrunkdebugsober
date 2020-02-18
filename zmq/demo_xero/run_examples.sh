#!/bin/bash

set -eu
set -o pipefail

# Simplest example-call RPC with no arguments and get single string as a reply
./bin/demo_xerouniclient tcp://127.0.0.1:5550 ping

# Similar, call RPC with no arguments and ensure the "reply" comes in, but no data returned
./bin/demo_xerouniclient tcp://127.0.0.1:5550 return_none

# Call an RPC that just does an equality comparison. Simple example to demonstrate how to pass arguments to worker RPC
./bin/demo_xerouniclient tcp://127.0.0.1:5550 compare --args '"apple", "orange"'

# Effectively the same thing, but showing how to use named arguments.
./bin/demo_xerouniclient tcp://127.0.0.1:5550 compare --kwargs '"str1":"apple", "str2":"orange"'

# Call an RPC that doesn't actually exist, and make sure the worker is able to handle the problem cleanly while returning
# the actual exception that is raised.
./bin/demo_xerouniclient tcp://127.0.0.1:5550 invalid_request

# The slow_ functions are serviced by an "actor" model. slow_succeed will succeed after the provided timeout,
# slow_fail will fail after the provided timeout.
./bin/demo_xerouniclient tcp://127.0.0.1:5550 slow_succeed --args 5 --timeout 20
./bin/demo_xerouniclient tcp://127.0.0.1:5550 slow_fail --args 5 --timeout 20


