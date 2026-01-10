#!/usr/bin/env -S python3 -u

# This file serves as a parallel driver (https://antithesis.com/docs/test_templates/test_composer_reference/#parallel-driver). 
# It does between 1 and 100 random kv leases against a random etcd host in the cluster. We then check to see if successful leases persisted.
# Leases are set for either 1 second or indefinitely. We then check if the leases are still valid on another random etcd host.

# Antithesis SDK
from antithesis.assertions import (
  always,
  sometimes,
)
import sys
import time

sys.path.append("/opt/antithesis/resources")
import helper

SHORT_LEASE_DURATION_SECONDS = 10
LONG_LEASE_DURATION_SECONDS = 31536000

def create_lease(duration):
  """
  This function will first connect to an etcd host, then create a lease with the specified duration.
  We return the lease.
  """
  client = helper.connect_to_host()
  success, error, lease = helper.generate_lease(client, duration)

  sometimes(success, "Client can create a lease", {"error":error})
  if error:
    print(f"Client: failed to create short lease with error '{error}'")
  
  return lease

def simulate_leased_traffic_and_expire(lease_duration):
  """
  This function will first connect to an etcd host, then execute a certain number of put requests with the specified lease duration.
  The key and value for each put request are generated using Antithesis randomness (check within the helper.py file).
  We then wait for the lease to expire. We then return the key/value pairs from successful requests.
  """
  lease = create_lease(lease_duration)
  client = helper.connect_to_host()
  num_requests = helper.generate_requests()
  kvs = []

  for _ in range(num_requests):
    key = helper.generate_random_string()
    value = helper.generate_random_string()
    success, error = helper.put_request(client, key, value, lease)

    sometimes(success, "Client can make successful put requests with a lease", {"error":error})

    if success:
      kvs.append((key, value))
      print(f"Client: successful put with key '{key}', value '{value}', and lease '{lease.id}'")
    else:
      print(f"Client: unsuccessful put with key '{key}', value '{value}', lease '{lease.id}', and error '{error}'")

  time.sleep(lease_duration + 1)

  return kvs

def simulate_leased_traffic_and_revoke(lease_duration):
  """
  This function will first connect to an etcd host, then execute a certain number of put requests with the specified lease.
  The key and value for each put request are generated using Antithesis randomness (check within the helper.py file).
We then revoke the lease. We return the key/value pairs from successful requests.
  """
  lease = create_lease(lease_duration)
  client = helper.connect_to_host()
  num_requests = helper.generate_requests()
  kvs = []

  for _ in range(num_requests):
    key = helper.generate_random_string()
    value = helper.generate_random_string()
    success, error = helper.put_request(client, key, value, lease)

    sometimes(success, "Client can make successful put requests with a lease", {"error":error})

    if success:
      kvs.append((key, value))
      print(f"Client: successful put with key '{key}', value '{value}', and lease '{lease.id}'")
    else:
      print(f"Client: unsuccessful put with key '{key}', value '{value}', lease '{lease.id}', and error '{error}'")

  success, error = helper.revoke_lease(client, lease)
  sometimes(success, "Client can revoke a lease", {"error":error})
  if error:
    print(f"Client: failed to revoke lease with error '{error}'")

  return kvs

def validate_leased_puts_deleted(kvs):
    """
      This function will first connect to an etcd host, then perform a get request on each key in the key/value array.
      For each successful response, we check that the key was deleted.
      If we ever find a key that was not deleted, we return it.
    """
    client = helper.connect_to_host()

    for kv in kvs:
      key, value = kv[0], kv[1]
      success, error, database_value = helper.get_request(client, key)

      # Antithesis Assertion: sometimes get requests are successful. A failed request is OK since we expect them to happen.
      sometimes(success, "Client can make successful get requests", {"error":error})

      if not success:
        print(f"Client: unsuccessful get with key '{key}', and error '{error}'")
      elif database_value is not None:
        print(f"Client: A key/value found that should have been deleted! This shouldn't happen.")
        return False, (key, value, database_value)

    print(f"Client: Validation of deleted keys ok!")
    return True, None

if __name__ == "__main__":
  kvs = simulate_leased_traffic_and_expire(SHORT_LEASE_DURATION_SECONDS)
  values_stay_consistent, mismatch = validate_leased_puts_deleted(kvs)
  always(values_stay_consistent, "Database keys are deleted after lease expiry.", {"mismatch":mismatch})

  kvs = simulate_leased_traffic_and_revoke(LONG_LEASE_DURATION_SECONDS)
  values_stay_consistent, mismatch = validate_leased_puts_deleted(kvs)
  always(values_stay_consistent, "Database keys are deleted after lease revoked.", {"mismatch":mismatch})