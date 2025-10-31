# Etcd-test-composer

## Purpose

This repo demonstrates the use of the [Antithesis platform](https://antithesis.com/product/what_is_antithesis/) to test [etcd](https://etcd.io/). 

## Setup

There are 4 containers running in this system: 3 that make up an etcd cluster (`etcd0`, `etcd1`, `etcd2`) and one that ["makes the system go"](https://antithesis.com/docs/getting_started/basic_test_hookup/)(`client`). 

The `client` container also runs the `entrypoint.py` script runs when it starts. This script confirms that all of the etcd hosts are available before [signaling the software is ready to test](https://antithesis.com/docs/getting_started/basic_test_hookup/#ready-signal). 

## Test Composer 

Antithesis' [Test Composer](https://antithesis.com/docs/test_templates/) framework enables you to define a *test template,* a guide that the system uses to generate thousands of test cases that will run over a multitude of system states. When you use this framework, the platform will handle varying things like parallelism, test length, and command order. 

You provide a set of *test commands,* executables which the framework detects based on [their absolute directory location and names](https://antithesis.com/docs/test_templates/first_test/#structuring-test-templates). 

In `test-template/Dockerfile`, you can see that four test commands get defined in the `client` container image: `/opt/antithesis/test/v1/main/parallel_driver_generate_traffic.py`, `/opt/antithesis/test/v1/main/serial_driver_delete_keys`, `/opt/antithesis/test/v1/main/eventually_health_check.sh`, and `/opt/antithesis/test/v1/main/finally_db_consistent_lines.sh`. 

*Drivers can be defined on any container in the system.* 

### Parallel Driver

`parallel_driver_generate_traffic.py` is a [parallel driver](https://antithesis.com/docs/test_templates/test_composer_reference/#parallel-driver) that submits puts against the etcd cluster. 0 to many of these can run at once. It then validates that these puts were persisted in the database by connecting to another node and submitting get requests. 

### Serial Driver

`serial_driver_delete_keys.go` is a [serial driver](https://antithesis.com/docs/test_templates/test_composer_reference/#serial-driver-command) that deletes half of the keys in the database and checks to make sure that these keys were deleted. No other drivers will run in parallel with this one. 

### Eventually

`eventually_health_check.sh` is an [eventually command](https://antithesis.com/docs/test_templates/test_composer_reference/#eventually-command) that checks the cluster health by pinging each node during a quiescent period.

### Finally

`finally_db_consistent_lines.sh` is a [finally command](https://antithesis.com/docs/test_templates/test_composer_reference/#finally-command) that asserts the existence of only 6 keys in the database. It first deletes all the keys, writes 6 keys, and then counts the number of entries. Eventually and finally commands do not overlap, so both will never be run in the same timeline.

## SDK Usage

This repository includes the use of Antithesis's Python, Go, Java, and Rust SDKs, to do the following: 

### setupComplete

The ["setupComplete"](https://antithesis.com/docs/generated/sdk/python/antithesis/lifecycle.html#setup_complete) signals that the system is ready to test. For example, in `entrypoint.py`: 

`setup_complete({"Message":"ETCD cluster is healthy"})`

### Assertions

Antithesis SDKs allow users to [express the properties their software should have,](https://antithesis.com/docs/properties_assertions/) by [adding assertions to their code](https://antithesis.com/docs/properties_assertions/assertions/). We use 4 types of assertions in this repo. 

#### Sometimes Assertions

[Sometimes assertions](https://antithesis.com/docs/properties_assertions/properties/#sometimes-properties) check that intended funcitonality *happens at least once in the course of testing* - in this case, that operations happen against the etcd cluster and that validation occurs. For example, in `parallel_driver_generate_traffic.py`: 

`sometimes(success, "Client can make successful get requests", None)`

#### Always Assertions

[Always assertions](https://antithesis.com/docs/properties_assertions/properties/#always-properties) check that something (like a guarantee) *always happens, on every execution history.* In this case, in `serial_driver_validate_operations.go` this line checks that the get response of a deleted key is empty: 

`assert.Always(resp.Count == 0, "Key was deleted correctly", map[string]interface{}{"key": k})`

#### Reachable Assertions

Reachable assertions will evaluate if that part of code was reached. In `EventuallyValidation.java`, we have the following line:

`reachable("Performing health check on the etcd cluster", null);`

If our test hits this line of code at least once, it will pass.

#### Unreachable Assertions

Unreachable assertions will evaluate if that part of code was not reached. They are written in places that we do not want to reach. An example would be in code sections for error handling. In `/opt/antithesis/resources/helper.py` we have the following assertion:

`unreachable("Client failed to connect to an etcd host", {"host":host, "error":e})`

We expect to always to connect to an etcd host. If this assertion is ever hit, then the property will fail.

### Randomness

Randomness is key for autonomous testing, since we want the software to follow many, unpredictable execution paths. [The Antithesis SDK](https://antithesis.com/docs/using_antithesis/sdk/#randomness) provides an easy interface to get structured random values while also providing valuable guidance to the Antithesis platform, which increases the efficiency of testing.

## Testing Locally

Before running your application on the Antithesis platform, it can be convenient to check your work locally before you kick off a full Antithesis test run.

This is a 3 step process, which is [described in greater detail here](https://antithesis.com/docs/test_templates/testing_locally/): 

1. Pull the bitnami/etcd:3.5 image using the following command: 

`docker pull bitnamilegacy/etcd:3.5`

2. Build the client image. From within the `/test-template` directory, run the following command: 

`docker build . -f Dockerfile.client -t etcd-client:latest`

3. run `docker-compose up` from the config directory to start all containers defined in `docker-compose.yml`

4. After the client container has signaled `setupComplete` (or printed `cluster is healthy`), you can run the parallel driver 1 to many times via `docker exec`: 

`docker exec client /opt/antithesis/test/v1/main/parallel_driver_generate_traffic.py`

5. After that completes, you can run the serial driver in the same fashion: 

`docker exec client /opt/antithesis/test/v1/main/serial_driver_delete_keys`

You should see a message: `Completion of a key deleting check`

6. Try running the other commands in the /opt/antithesis/test/v1/main directory and confirm that they work!

You've now validated that your test is ready to run on the Antithesis platform! (Note that SDK assertions won't be evaluated locally).

## Example Report

Using the three node etcd cluster and the `client` image built from this repository, we ran a 1 hour test. The resulting [triage report](https://antithesis.com/docs/reports/triage/) can be found [here](https://public.antithesis.com/report/f6oh7KZ6Pchcv9nGfo5oL9IU/lCbpXJUfNwfknLazqvV3mWD3CM37l89raJTdSXNBh3c.html), and [our docs](https://antithesis.com/docs/reports/triage/) show you how to interpret it. 
