import string, time
from hypothesis import example, given, strategies as st
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
def test_etcd(key, value):
    client = helper.connect_to_host()
    print(f'key is {key}')
    print(f'value is {value}')
    # etcd can't handle empty value
    if value == '':
        return
    requests = helper.generate_requests(1, 0, REQUEST_PROBABILITIES)
    for request in requests: 
        success, error = helper.put_request(client, key, value) 
        sometimes(success, "Client can make successful input-fuzzed put requests", None)
        if not success: 
            print(f"Client [parallel_driver_hypothesis]: unsuccessful put with key '{key}', value '{value}', and error '{error}'")

if __name__ == '__main__':
    globals()[sys.argv[1]]()
