import random, etcd3, string
import numpy as np

# Antithesis SDK
from antithesis.random import (
    random_choice,
    get_random,
)

# Antithesis SDK
from antithesis.assertions import (
    unreachable,
)

def put_request(c, key, value, lease=None):
    try:
        c.put(key, value, lease=lease)
        return True, None
    except Exception as e:
        return False, e

def get_request(c, key):
    try:
        response = c.get(key)
        if response[0] is None:
            return True, None, None
        database_value = response[0].decode('utf-8')
        return True, None, database_value
    except Exception as e:
        return False, e, None

def generate_requests():
    return (get_random() % 100) + 1

def generate_random_string():
    random_str = []
    for _ in range(8):
        random_str.append(random_choice(list(string.ascii_letters + string.digits)))
    return "".join(random_str)

def connect_to_host():
    host = random_choice(["etcd0", "etcd1", "etcd2"])
    try:
        client = etcd3.client(host=host, port=2379)
        print(f"Client: connected to {host}")
        return client
    except Exception as e:
        # Antithesis Assertion: client should always be able to connect to an etcd host
        unreachable("Client failed to connect to an etcd host", {"host":host, "error":e})
        print(f"Client: failed to connect to {host}. exiting")
        sys.exit(1)

def generate_lease(c, duration):
    try:
        lease = c.lease(duration)
        return True, None, lease
    except Exception as e:
        return False, str(e), None

def revoke_lease(c, lease):
    try:
        c.revoke_lease(lease.id)
        return True, None
    except Exception as e:
        return False, str(e)