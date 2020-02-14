FROM stackhead/codedrunk_xero_base

# Run demo_xerouniclient, just issuing the "ping command" to the worker as quickly as possible, indefinitely

CMD ["demo_xerouniclient", "tcp://*:5550", "ping", "--count", "-1"]

