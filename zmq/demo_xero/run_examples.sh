#!/bin/bash

set -eu
set -o pipefail

./bin/demo_xerouniclient tcp://127.0.0.1:5550 ping
./bin/demo_xerouniclient tcp://127.0.0.1:5550 invalid_request
./bin/demo_xerouniclient tcp://127.0.0.1:5550 compare --args '"uno", "dos"'
./bin/demo_xerouniclient tcp://127.0.0.1:5550 compare --kwargs '"str1":"uno", "str2":"dos"'
./bin/demo_xerouniclient tcp://127.0.0.1:5550 return_none
./bin/demo_xerouniclient tcp://127.0.0.1:5550 take_too_long
./bin/demo_xerouniclient tcp://127.0.0.1:5550 slow_succeed --args 5 --timeout 20
./bin/demo_xerouniclient tcp://127.0.0.1:5550 slow_fail --args 5 --timeout 20

#./bin/demo_xerouniclient tcp://127.0.0.1:5550 cut_video --args '"table_cam.mp4", "./output/bleh.mp4", "00:00:00", "00:02:00"'

