import etcd3, string

# Antithesis SDK
from antithesis.random import (
    random_choice,
    get_random,
)

def put_request(c, key, value):
    try:
        c.put(key, value)
        return True, None
    except Exception as e:
        return False, e

def get_request(c, key):
    try:
        response = c.get(key)
        database_value = response[0].decode('utf-8')
        return True, None, database_value
    except Exception as e:
        return False, e, None

def connect_to_host():
    host = random_choice(["etcd0", "etcd1", "etcd2"])
    try:
        client = etcd3.client(host=host, port=2379)
        print(f"Client: connected to {host}")
        return client
    except Exception as e:
        print(f"Client: failed to connect to {host}. exiting")
        sys.exit(1)

def generate_random_string():
    random_str = []
    for _ in range(16):
        random_str.append(random_choice(list(string.ascii_letters + string.digits)))
    return "".join(random_str)

def generate_num_requests():
    return (get_random() % 100) + 1