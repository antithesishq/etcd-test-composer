#!/usr/bin/env -S python3 -u

# This file serves as the client's entrypoint. It signals "setupComplete" using the Antithesis SDK

import etcd3, time

from antithesis.lifecycle import (
    setup_complete,
)

print("Client [entrypoint]: cluster is healthy!")
# Here is the python format for setup_complete. At this point, our system is fully initialized and ready to test.
setup_complete({"Message":"ETCD cluster is healthy"})

# sleep infinity
time.sleep(31536000)