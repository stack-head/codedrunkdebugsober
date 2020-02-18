# Demo Xero

demo_dero and the xero library include a simple version of the ZMQ Paranoid Pirate pattern, it's primarily meant for teaching/demonstration.
There are a few departures from the true Paranoid Pirate pattern. The primary difference is the example only supports one worker -this is done for clarity, a full example would support multiple workers. Additionally, the full paranoid pirate would support sending out multiple messages before a response arrives. This implementation only supports one response at a time, this is done to enforce an RPC style interface.
