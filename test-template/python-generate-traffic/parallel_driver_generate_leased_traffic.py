#!/usr/bin/env -S python3 -u

# This file serves as a parallel driver (https://antithesis.com/docs/test_templates/test_composer_reference/#parallel-driver). 
# It does between 1 and 100 random kv puts against a random etcd host in the cluster. We then check to see if successful puts persisted
# and are correct on another random etcd host.

# A key addition is testing the behaviour of leases, specifically to check that keys are wiped when a lease is revoked

# Antithesis SDK
from antithesis.assertions import (
    always,
    sometimes,
    reachable,
)

import sys
sys.path.append("/opt/antithesis/resources")
import helper

# ensures we can test the lease revoking behaviour without worrying about the lease expiring
TIME_INFINITY = 31536000

def simulate_traffic():
    """
        This function will first connect to an etcd host, then execute a certain number of put requests. 
        The key and value for each put request are generated using Antithesis randomness (check within the helper.py file). 
        We return the key/value pairs from successful requests.
    """
    client = helper.connect_to_host()
    num_requests = helper.generate_requests()
    
    lease = client.lease(ttl=TIME_INFINITY)
    kvs = []

    for _ in range(num_requests):

        # generating random str for the key and value
        key = helper.generate_random_string()
        value = helper.generate_random_string()

        # randomly decide whether to use the lease or not for each key
        use_lease = bool(helper.generate_requests() % 2)

        # response of the put request
        success, error = helper.put_request(client, key, value, lease=lease if use_lease else None)

        # Antithesis Assertion: sometimes put requests are successful. A failed request is OK since we expect them to happen.
        sometimes(success, "Client can make successful put requests", {"error":error})

        if success:
            # updated the structure to use a dictionary to better track the different variables
            kvs.append({"key": key, "value": value, "has_lease": use_lease})
            print(f"Client: successful put with key '{key}' and value '{value}' (has_lease: '{use_lease}')")
        else:
            print(f"Client: unsuccessful put with key '{key}', value '{value}', and error '{error}'")

    print(f"Client: traffic simulated!")
    return kvs, lease
    

def validate_puts(kvs):
    """
        This function will first connect to an etcd host, then perform a get request on each key in the key/value array. 
        For each successful response, we check that the get request value == value from the key/value array. 
        If we ever find a mismatch, we return it. 
    """
    client = helper.connect_to_host()

    for kv in kvs:
        key = kv["key"]
        value = kv["value"]

        success, error, database_value = helper.get_request(client, key)

        # Antithesis Assertion: sometimes get requests are successful. A failed request is OK since we expect them to happen.
        sometimes(success, "Client can make successful get requests", {"error":error})

        if not success:
            print(f"Client: unsuccessful get with key '{key}', and error '{error}'")
        elif value != database_value:
            print(f"Client: a key value mismatch! This shouldn't happen.")
            return False, (value, database_value)
            
        print(f"Client: Successful key-value match for key '{key}': expected value '{value}' matched the retrieved value '{database_value}'")

        # Antithesis Assertion: If at least one key value match pair exists, we should take note of it, 
        # in the event future iterations reveal a key value mismatch, which will end the function early
        reachable(f"Key value match", {"key": f"{key}", "value": f"{value}", "database_value": f"{database_value}"})

    print(f"Client: validation of puts ok!")
    return True, None


def validate_keys_with_revoked_lease(kvs):
    """
    Checks that keys associated with a revoked lease do not persist
    """
    
    client = helper.connect_to_host()
    
    for kv in kvs:
        key = kv["key"]
        has_lease = kv["has_lease"]
        
        # only want to test kv that have leases
        if not has_lease:
           continue
        
        success, error, database_value = helper.get_request(client, key)
        
        # Antithesis Assertion: sometimes get requests are successful. A failed request is OK since we expect them to happen.
        sometimes(success, "Client can make successful get requests", {"error":error})
        
        if database_value is not None:
            print(f"Client: the key has persisted despite being associated with a revoked lease!")
            return False, key
        
        print(f"Client: Successful key {key} was not in the database")

        # Antithesis Assertion: If at least one key with a revoked lease does not exist, we should take note of it, 
        # in the event future iterations reveal a key with a revoked lease that exists, which will end the function early
        reachable(f"Key with revoked license was not in the database", {"key": key})
    
    print(f"Client: validation of keys with revoked lease ok!")
    return True, None


def validate_keys_persist(kvs):
    """
    Checks that keys not associated with a revoked lease continue to persist
    """
    
    client = helper.connect_to_host()
    
    for kv in kvs:
        key = kv["key"]
        has_lease = kv["has_lease"]
        
        # now just testing kv that don't have leases
        if has_lease:
           continue
        
        success, error, database_value = helper.get_request(client, key)
        
        # Antithesis Assertion: sometimes get requests are successful. A failed request is OK since we expect them to happen.
        sometimes(success, "Client can make successful get requests", {"error":error})
        
        if not success:
            print(f"Client: unsuccessful get with key '{key}', and error '{error}'")
        elif database_value is None:
            print(f"Client: the key no longer exists despite not being associated with a revoked lease!")
            return False, key
        
        print(f"Client: Successful key '{key}' remained in the database")
        reachable(f"Key without revoked license remained in the database", {"key": key})
    
    print(f"Client: validation of keys without lease ok!")
    return True, None


if __name__ == "__main__":
    
    kvs, lease = simulate_traffic()
    values_stay_consistent, mismatch = validate_puts(kvs)

    # Antithesis Assertion: for all successful kv put requests, values from get requests should match for their respective keys 
    always(values_stay_consistent, "Database key values stay consistent", {"mismatch":mismatch})
    
    # now check the case where the lease is revoked
    lease.revoke()
    
    # first check keys associated with a revoked lease
    leased_keys_are_removed, key_not_removed  = validate_keys_with_revoked_lease(kvs)
    always(leased_keys_are_removed, "Keys with revoked leases are removed", {"persisted keys": key_not_removed})
    
    # next check keys not associated with the revoked lease
    unleased_keys_are_not_removed, removed_key = validate_keys_persist(kvs)
    always(unleased_keys_are_not_removed, "Keys with unrevoked leases persist", {"removed keys": removed_key})
    
