#!/usr/bin/env -S python3 -u

# Antithesis SDK
from antithesis.assertions import (
    always,
    sometimes,
)

import sys
sys.path.append("/opt/antithesis/resources")
import helper

def simulate_traffic(prefix):
    """
        This function will first connect to an etcd host, then execute a certain number of put requests. 
        The key and value for each put request are generated using Antithesis randomness (check within the helper.py file). 
        We return the key/value pairs from successful requests.
    """
    client = helper.connect_to_host()
    num_requests = helper.generate_requests()
    kvs = []

    for _ in range(num_requests):

        # generating random str for the key and value
        key = prefix+helper.generate_random_string()
        value = helper.generate_random_string()

        # response of the put request
        success, error = helper.put_request(client, key, value)

        # Antithesis Assertion: sometimes put requests are successful. A failed request is OK since we expect them to happen.
        sometimes(success, "Client can make successful put requests", {"error":str(error)})
        sometimes(error!=None, "Client put requests can fail", None)

        if success:
            kvs.append((key, value))
            print(f"Client: successful put with key '{key}' and value '{value}'")
        else:
            print(f"Client: unsuccessful put with key '{key}', value '{value}', and error '{error}'")

    print(f"Client: traffic simulated!")
    return kvs

def validate_puts(kvs):
    """
        This function will first connect to an etcd host, then perform a get request on each key in the key/value array. 
        For each successful response, we check that the get request value == value from the key/value array. 
        If we ever find a mismatch, we return it. 
    """
    client = helper.connect_to_host()

    for kv in kvs:
        key, value = kv[0], kv[1]
        success, error, database_value = helper.get_request(client, key)

        # Antithesis Assertion: sometimes get requests are successful. A failed request is OK since we expect them to happen.
        sometimes(success, "Client can make successful get requests", {"error":str(error)})
        sometimes(error!=None, "Client get requests can fail", None)

        if not success:
            print(f"Client: unsuccessful get with key '{key}', and error '{error}'")
        elif value != database_value:
            print(f"Client: a key value mismatch! This shouldn't happen.")
            return False, (value, database_value)

    print(f"Client: validation ok!")
    return True, None

if __name__ == "__main__":
    prefix = helper.generate_random_string()
    kvs = simulate_traffic(prefix)
    values_stay_consistent, mismatch = validate_puts(kvs)

	# We expect that the values we put in the database stay consistent
    always(values_stay_consistent, "Database key values stay consistent", {"mismatch":mismatch})