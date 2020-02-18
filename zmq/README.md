# Demo Xero

See https://codedrunkdebugsober.com/pyzmq-paranoid-pirate/ for more explanation.

demo_xero and the xero library include a simple version of the ZMQ Paranoid Pirate pattern, it's primarily meant for teaching/demonstration.
There are a few departures from the true Paranoid Pirate pattern. The primary difference is the example only supports one worker -this is done for clarity, a full example would support multiple workers. Additionally, the full paranoid pirate would support sending out multiple messages before a response arrives. This implementation only supports one response at a time, this is done to enforce an RPC style interface.

run_demo_xero_in_docker_env.sh will build docker containers to demonstrate running this sample in a controlled docker environment.

If you want to run the samples directly on your dev machine, install both xero and demo_xero via:
pip3 install -e ./xero
pip3 install -e ./demo_xero

In one terminal, run the worker:
./bin/demo_xerouniworker tcp://127.0.0.1:5550

In a second terminal, run any of the commands in run_examples.sh
