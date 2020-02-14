FROM stackhead/codedrunk_xero_base

# Run demo_xerouniworker in a docker container.
# The string codedrunk_xero_uniclient will be recognized as the network address of the "client" docker container
CMD ["demo_xerouniworker", "tcp://codedrunk_xero_uniclient:5550"]
