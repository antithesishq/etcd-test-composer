#!/usr/bin/env python3

import subprocess
import time
from antithesis.lifecycle import setup_complete

def wait_for_etcd_health():
    while True:
        try:
            response = subprocess.check_output([
                "curl", "-sf", "http://etcd:2379/health"
            ]).decode()
            if '"health":"true"' in response:
                break
        except subprocess.CalledProcessError:
            print("[health-checker] waiting for etcd...")
        time.sleep(1)

wait_for_etcd_health()

print("[health-checker] cluster is healthy!")
setup_complete({"Message": "ETCD cluster is healthy"})
