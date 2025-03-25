#!/usr/bin/env -S python3 -u

#Uses Hypothesis (https://hypothesis.readthedocs.io/en/latest/index.html) to fuzz inputs sent to etcd cluster

import string, time
from hypothesis import example, given, settings, strategies as st
import sys
sys.path.append("/opt/antithesis/resources")
import helper

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

REQUEST_PROBABILITIES = {
    "put": 0.1,
    "get": 0.0
}

@given(key=st.text(), value=st.text())
@settings(backend="hypothesis-urandom", deadline=None)
def test_etcd(key, value):
    try: 
        client = helper.connect_to_host()
        print(f'key is {key}')
        print(f'value is {value}')
        # etcd can't handle empty keys/values
        if value == '' or key == '':
            return
        requests = helper.generate_requests(1, 0, REQUEST_PROBABILITIES)
        for request in requests: 
            success, error = helper.put_request(client, key, value) 
            sometimes(success, "Client can make successful input-fuzzed put requests", None)
            if not success: 
                print(f"Client [parallel_driver_hypothesis]: unsuccessful put with key '{key}', value '{value}', and error '{error}'")
    except Exception as e:
        print(f"Client [parallel_driver_hypothesis]: Exception {e}")

if __name__ == '__main__':
    try:
        test_etcd()
    except Exception as e:
        print(f"Client [parallel_driver_hypothesis]: Exception {e}")
