import etcd3, string

# Antithesis SDK
from antithesis.random import (
    random_choice,
    get_random,
)

# Antithesis SDK
from antithesis.assertions import (
    unreachable,
)


def put_request(c, key, value, **kwargs):
    try:
        c.put(key, value, **kwargs)
        return True, None
    except Exception as e:
        return False, str(e)


# adjusted `get_request` to differentiate between connection failure and key not being available 
def get_request(c, key):
    try:
        response = c.get(key)

        # if the key is unavailable, then this returns None
        # Previously, this would result in an AttributeError, as None cannot be decoded
        if response[0] is None:
            return True, None, None
        
        database_value = response[0].decode('utf-8')
        return True, None, database_value
    except Exception as e:
        return False, str(e), None

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
