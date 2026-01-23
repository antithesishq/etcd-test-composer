#!/usr/bin/env -S python3 -u

# This file serves as a parallel driver (https://antithesis.com/docs/test_templates/test_composer_reference/#parallel-driver).
# It acquires a distributed lock, writes a key/value, verifies concurrent acquisition is blocked, releases the lock,
# and then verifies the lock can be acquired again and the data is visible.

# Antithesis SDK
from antithesis.assertions import (
  always,
  sometimes,
)

import sys

sys.path.append("/opt/antithesis/resources")
import helper

SHORT_LOCK_TIMEOUT_SECONDS = 1

def format_error(error):
  if error is None:
    return None
  return str(error)

def attempt_lock_acquire(lock, timeout=None):
  try:
    if timeout is None:
      return lock.acquire(), None
    return lock.acquire(timeout=timeout), None
  except TypeError as e:
    # Known python-etcd3 + tenacity incompatibility: treat as acquisition failure.
    return False, e
  except Exception as e:
    return False, e

def get_lock_name(lock):
  if hasattr(lock, "name") and lock.name is not None:
    return lock.name
  if hasattr(lock, "antithesis_name"):
    return lock.antithesis_name
  return None

def acquire_lock_and_write():
  """
  This function will first connect to an etcd host, acquire a distributed lock, and then write a key/value pair.
  We return the lock, key, and value.
  """
  client = helper.connect_to_host()
  lock_name = f"antithesis_lock_{helper.generate_random_string()}"
  lock = client.lock(lock_name)
  lock.antithesis_name = lock_name

  acquired, error = attempt_lock_acquire(lock)
  sometimes(acquired, "Client can acquire distributed lock", {"lock_name":lock_name, "error":format_error(error)})

  if not acquired:
    print(f"Client: failed to acquire lock '{lock_name}' with error '{error}'")
    return lock, None, None

  key = helper.generate_random_string()
  value = helper.generate_random_string()
  success, error = helper.put_request(client, key, value)

  sometimes(success, "Client can write data while holding a lock", {"error":format_error(error)})

  if success:
    print(f"Client: successful put with key '{key}', value '{value}', and lock '{lock_name}'")
  else:
    print(f"Client: unsuccessful put with key '{key}', value '{value}', lock '{lock_name}', and error '{error}'")

  return lock, key, value

def try_acquire_lock(lock):
  """
  This function will connect to a different etcd host, try to acquire the same lock with a short timeout,
  and return whether it succeeded.
  """
  client = helper.connect_to_host()
  lock_name = get_lock_name(lock)
  if lock_name is None:
    print("Client: failed to determine lock name for acquisition attempt")
    return False

  attempt_lock = client.lock(lock_name)
  acquired, error = attempt_lock_acquire(attempt_lock, SHORT_LOCK_TIMEOUT_SECONDS)

  sometimes(acquired, "Client can acquire distributed lock", {"lock_name":lock_name, "error":format_error(error)})

  if acquired:
    print(f"Client: acquired lock '{lock_name}'")
    release_lock(attempt_lock)
  else:
    print(f"Client: could not acquire lock '{lock_name}' with timeout '{SHORT_LOCK_TIMEOUT_SECONDS}' and error '{error}'")

  return acquired

def release_lock(lock):
  """
  This function will release a distributed lock.
  """
  lock_name = get_lock_name(lock)
  try:
    lock.release()
    print(f"Client: released lock '{lock_name}'")
    return True, None
  except Exception as e:
    print(f"Client: failed to release lock '{lock_name}' with error '{e}'")
    return False, e

def validate_data_visible(key, value):
  """
  This function will connect to an etcd host, perform a get request on the key, and verify the value is visible.
  """
  if key is None or value is None:
    print("Client: missing key/value from lock write; validation failed")
    return False, (value, None)

  client = helper.connect_to_host()
  success, error, database_value = helper.get_request(client, key)

  # Antithesis Assertion: sometimes get requests are successful. A failed request is OK since we expect them to happen.
  sometimes(success, "Client can make successful get requests", {"error":error})

  if not success:
    print(f"Client: unsuccessful get with key '{key}', and error '{error}'")
    return False, (value, None)
  elif value != database_value:
    print(f"Client: a key value mismatch! This shouldn't happen.")
    return False, (value, database_value)

  print(f"Client: validation ok for key '{key}'")
  return True, None

if __name__ == "__main__":
  lock, key, value = acquire_lock_and_write()
  lock_name = get_lock_name(lock)

  concurrent_acquired = try_acquire_lock(lock)
  always(not concurrent_acquired, "Lock blocks concurrent acquisition", {"lock_name":lock_name})

  released, release_error = release_lock(lock)
  always(released, "Lock can be released", {"lock_name":lock_name, "error":format_error(release_error)})

  acquired_after_release = try_acquire_lock(lock)
  always(acquired_after_release, "Lock can be acquired after release", {"lock_name":lock_name})

  values_stay_consistent, mismatch = validate_data_visible(key, value)
  always(values_stay_consistent, "Database key values stay consistent under lock", {"mismatch":mismatch})
