See https://codedrunkdebugsober.com/pyzmq-paranoid-pirate/ for more explanation.

run_demo_xero_in_docker_env.sh will build docker containers to demonstrate running this sample in a controlled docker environment.

If you want to run the samples directly on your dev machine, install both xero and demo_xero via:
pip3 install -e ./xero
pip3 install -e ./demo_xero

In one terminal, run the worker:
./bin/demo_xerouniworker tcp://127.0.0.1:5550

In a second terminal, run any of the commands in run_examples.sh
