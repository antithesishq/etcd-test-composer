#!/usr/bin/env -S python3 -u

# This file serves as a parallel driver (https://antithesis.com/docs/test_templates/test_composer_reference/#parallel-driver). 
# It does N(40, 25) random operations against a random etcd host in the cluster
# The operations and their responses are saved to disk as "model" data.

import etcd3, string
import numpy as np

from antithesis.assertions import (
    sometimes,
    unreachable,
    reachable
)

from antithesis.random import (
    get_random,
    random_choice
)

import sys
sys.path.append("/opt/antithesis/resources")

import local_file_helper, request

MEAN = 40
STANDARD_DEV = 25
REQUEST_PROBABILITIES = {
    "put": 0.5,
    "get": 0.5
}
HOSTS = ["etcd0", "etcd1", "etcd2"]
KEYS = ["a","b","c","d","e","f"]


def generate_random_value():
    random_val = []
    for _ in range(8):
        random_val.append(random_choice(list(string.ascii_letters + string.digits)))
    return "".join(random_val)


def format_operation(traffic_id, request_type, start, end, key, value=None, response=None, success=True, revision=None):
    operation = f"{traffic_id},{request_type},{start},{end},{key},{value},{response},{success},{revision}"
    print(f"Client [parallel_driver_generate_traffic] ({traffic_id}): operation recorded: {operation}")
    return operation


def execute_requests(client, traffic_id, requests):
    operations = []

    for request_type in requests:
        if request_type == "put":

            key = random_choice(KEYS)
            value = generate_random_value()
            success, start, end, response, error = request.put_request(client, key, value)

            sometimes(success,"Client can make successful put requests", None)

            if success:
                revision = response.header.revision
                revision_str = f"{{Put_Revision:{revision}}}"
                operation = format_operation(traffic_id, request_type, start, end, key, value, revision=revision_str)
                operations.append(operation)
            else:
                operation = format_operation(traffic_id, request_type, start, end, key, value, success=False)
                operations.append(operation)
                print(f"Client [parallel_driver_generate_traffic] ({traffic_id}): unknown response for a {request_type} with key '{key}' and value '{value}' with error '{error}' and end timeout '{end}'")

        elif request_type == "get":

            key = random_choice(KEYS)
            success, start, end, response, error = request.get_request(client, key)
            
            sometimes(success,"Client can make successful get requests", None)

            if success:
                value = response[0].decode('utf-8') if response[0] else None
                get_revision = response[1].response_header.revision if response[1] else None
                key_created = response[1].create_revision if response[1] else None
                key_modified = response[1].mod_revision if response[1] else None
                key_version = response[1].version if response[1] else None
                revision_str = f"{{Get_Revision:{get_revision};Key_Created:{key_created};Key_Modified:{key_modified};Key_Version:{key_version}}}"
                operation = format_operation(traffic_id, request_type, start, end, key, response=value, revision=revision_str)
                operations.append(operation)
            else:
                print(f"Client [parallel_driver_generate_traffic] ({traffic_id}): failed to do a client get for key '{key}' with error '{error}'")

        else:
            unreachable("unknown request type", {"traffic_id":traffic_id, "request_type":request_type})
            print(f"Client [parallel_driver_generate_traffic] ({traffic_id}): unknown request name. this should never happen")
    
    local_file_helper.write_operations(operations)
    reachable("Completion of a traffic execution script", None)
    print(f"Client [parallel_driver_generate_traffic] ({traffic_id}): traffic script completed")


def simulate_traffic():
    traffic_id = local_file_helper.generate_traffic_id()
    requests = request.generate_requests(MEAN, STANDARD_DEV, REQUEST_PROBABILITIES)
    try:
        host = random_choice(HOSTS)
        client = etcd3.client(host=host, port=2379)
        reachable("Client connects to an etcd host", None)
        print(f"Client [parallel_driver_generate_traffic] ({traffic_id}): connected to {host}")
        execute_requests(client, traffic_id, requests)
    except Exception as e:
        unreachable("Client fails to connects to an etcd host", {"traffic_id":traffic_id, "host":host, "error":e})
        print(f"Client [parallel_driver_generate_traffic] ({traffic_id}): failed to connect to {host}. no requests attempted")


if __name__ == "__main__":
    simulate_traffic()
