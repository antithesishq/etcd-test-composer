#!/usr/bin/env -S python3 -u

# This file serves as a parallel driver (https://antithesis.com/docs/test_templates/test_composer_reference/#parallel-driver). 
# It does N(40, 25) random puts against a random etcd host in the cluster. We then check to see if these puts were persisted on a
# different etcd node

import string, time
import numpy as np

from antithesis.assertions import (
    always,
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
import helper

MEAN = 40
STANDARD_DEV = 25
REQUEST_PROBABILITIES = {
    "put": 0.1,
    "get": 0.0
}


def generate_random_string():
    random_str = []
    for _ in range(8):
        random_str.append(random_choice(list(string.ascii_letters + string.digits)))
    return "".join(random_str)


def simulate_traffic():
    client = helper.connect_to_host()
    requests = helper.generate_requests(MEAN, STANDARD_DEV, REQUEST_PROBABILITIES)
    kvs = []

    for request_type in requests:
        if request_type == "put":

            key = generate_random_string()
            value = generate_random_string()
            success, error = helper.put_request(client, key, value)

            # We expect that sometimes the requests are successful. A failed request is OK since we expect them to happen sometimes.
            sometimes(success, "Client can make successful put requests", None)

            if success:
                kvs.append((key, value))
                print(f"Client [parallel_driver_generate_traffic]: successful put with key '{key}' and value '{value}'")
            else:
                print(f"Client [parallel_driver_generate_traffic]: unsuccessful put with key '{key}', value '{value}', and error '{error}'")

        else:
            # We should never be here because we only have put request types
            unreachable("Unknown request type", {"request_type":request_type})
            print(f"Client [parallel_driver_generate_traffic]: unknown request name. this should never happen")
            return None

    reachable("Completion of traffic simulation", None)
    print(f"Client [parallel_driver_generate_traffic]: traffic simulation completed")
    return kvs
    

def validate_puts(kvs):
    time.sleep(2)
    client = helper.connect_to_host()

    for kv in kvs:
        key, value = kv[0], kv[1]
        success, error, database_value = helper.get_request(client, key)

        # We expect that sometimes the requests are successful. A failed request is OK since we expect them to happen sometimes.
        sometimes(success, "Client can make successful get requests", None)

        if not success:
            print(f"Client [parallel_driver_generate_traffic]: unsuccessful get with key '{key}', and error '{error}'")
        elif value != database_value:
            return False, (value, database_value)

    reachable("Completion of put validation", None)
    print(f"Client [parallel_driver_generate_traffic]: put validation completed")
    return True, None


if __name__ == "__main__":
    kvs = simulate_traffic()
    values_stay_consistent, mismatch = validate_puts(kvs)

    # We expect that the values we put in the database stay consistent
    always(values_stay_consistent, "Database key values stay consistent", {"mismatch":mismatch})