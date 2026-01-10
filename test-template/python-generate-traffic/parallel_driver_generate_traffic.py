#!/usr/bin/env -S python3 -u

# This file serves as a parallel driver (https://antithesis.com/docs/test_templates/test_composer_reference/#parallel-driver). 
# It does between 1 and 100 random kv puts against a random etcd host in the cluster. We then check to see if successful puts persisted
# and are correct on another random etcd host.

# Antithesis SDK
from antithesis.assertions import (
    always,
    sometimes,
)

import sys
sys.path.append("/opt/antithesis/resources")
import helper

FRACTION_TO_UPDATE = 2

def simulate_traffic():
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
        key = helper.generate_random_string()
        value = helper.generate_random_string()

        # response of the put request
        success, error = helper.put_request(client, key, value)

        # Antithesis Assertion: sometimes put requests are successful. A failed request is OK since we expect them to happen.
        sometimes(success, "Client can make successful put requests", {"error":error})

        if success:
            kvs.append((key, value))
            print(f"Client: successful put with key '{key}' and value '{value}'")
        else:
            print(f"Client: unsuccessful put with key '{key}', value '{value}', and error '{error}'")

    print(f"Client: traffic simulated!")
    return kvs

def simulate_update_traffic(kvs):
    """
        This function will first connect to an etcd host, then execute a put request for approximately half the keys in the key/value array.
        The key and value for each put request are generated using Antithesis randomness (check within the helper.py file).
        We return the updated list of key/value pairs. For any failed put requests, we return the key/value pairs that were not updated.
    """
    client = helper.connect_to_host()
    new_kvs = []

    for kv in kvs:
        if helper.get_random() % FRACTION_TO_UPDATE == 0:

            key, value = kv[0], kv[1]
            # generating a new random str for the value
            new_value = helper.generate_random_string()

            # response of the put request
            success, error = helper.put_request(client, key, new_value)

            # Antithesis Assertion: sometimes put requests are successful. A failed request is OK since we expect them to happen.
            sometimes(success, "Client can make successful put requests for existing keys", {"error":error})
            
            if success:
                new_kvs.append((key, new_value))
                print(f"Client: successful put with key '{key}' and new value '{new_value}'")
            else:
                new_kvs.append((key, value))
                print(f"Client: unsuccessful put with key '{key}', new value '{new_value}', and error '{error}'")
        else:
            new_kvs.append(kv)
    return new_kvs

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
        sometimes(success, "Client can make successful get requests", {"error":error})

        if not success:
            print(f"Client: unsuccessful get with key '{key}', and error '{error}'")
        elif value != database_value:
            print(f"Client: a key value mismatch! This shouldn't happen.")
            return False, (value, database_value)

    print(f"Client: validation ok!")
    return True, None


if __name__ == "__main__":    
    kvs = simulate_traffic()
    values_stay_consistent, mismatch = validate_puts(kvs)

    # Antithesis Assertion: for all successful kv put requests, values from get requests should match for their respective keys 
    always(values_stay_consistent, "Database key values stay consistent", {"mismatch":mismatch})

    updated_kvs = simulate_update_traffic(kvs)
    values_stay_consistent, mismatch = validate_puts(updated_kvs)
    
    # Antithesis Assertion: for all successful kv put requests, updated values from get requests should match for their respective keys 
    always(values_stay_consistent, "Updated database key values stay consistent", {"mismatch":mismatch})
