# Etcd-test-composer

## Purpose

This repo demonstrates the use of the [Antithesis platform](https://antithesis.com/product/what_is_antithesis/) to test [etcd](https://etcd.io/) for violations against its [linearizability](https://etcd.io/docs/v3.5/learning/api_guarantees/) guarantee. 

## Setup

There are 4 containers running in this system: 3 that make up an etcd cluster (`etcd0`, `etcd1`, `etcd2`) and one that ["makes the system go"](https://antithesis.com/docs/getting_started/basic_test_hookup/)(`client`). 

The code in the `client` container takes operations against etcd and confirms those operations were linearizable. 

The `client` container also runs the `entrypoint.py` script runs when it starts. This script confirms that all of the etcd hosts are available before [signaling the software is ready to test](https://antithesis.com/docs/getting_started/basic_test_hookup/#ready-signal). 

## Test Composer 

Antithesis' [Test Composer](https://antithesis.com/docs/test_templates/) framework enables you to define a *test template,* a guide that the system uses to generate thousands of test cases that will run over a multitude of system states. When you use this framework, the platform will handle varying things like parallelism, test length, and command order. 

You provide a set of *test commands,* executables which the framework detects based on [their absolute directory location and names](https://antithesis.com/docs/test_templates/first_test/#structuring-test-templates). 

In `test-template/Dockerfile`, you can see that four test commands get defined in the `client` container image: `/opt/antithesis/test/v1/main/parallel_driver_generate_traffic.py`, `/opt/antithesis/test/v1/main/serial_driver_validate_operations`, `/opt/antithesis/test/v1/main/eventually_health_check.sh`, and `/opt/antithesis/test/v1/main/finally_db_consistent_lines.sh`. 

*Drivers can be defined on any container in the system.* 

### Parallel Driver

`parallel_driver_generate_traffic.py` is a [parallel driver](https://antithesis.com/docs/test_templates/test_composer_reference/#parallel-driver) that submits operations against the etcd cluster. 0 to many of these can run at once. 

### Serial Driver

`serial_driver_validate_operations.go` is a [serial driver](https://antithesis.com/docs/test_templates/test_composer_reference/#serial-driver-command) that validates the operations that have happened against the etcd cluster. No other drivers will run in parallel with this one. 

### Eventually

`eventually_health_check.sh` is an [eventually command](https://antithesis.com/docs/test_templates/test_composer_reference/#eventually-command) that checks the cluster health by pinging each node during a quiescent period.

### Finally

`finally_db_consistent_lines.sh` is a [finally command](https://antithesis.com/docs/test_templates/test_composer_reference/#finally-command) that checks the number of keys stored in the database. There should be a maximum of 6 keys (as defined in the parallel driver script) so we confirm that the total number of keys is less than or equal to 6. Eventually and finally commands do not overlap, so both will never be run in the same timeline.

## SDK Usage

This repository includes the use of Antithesis's Python, Go, Java, and Rust SDKs, to do the following: 

### setupComplete

The ["setupComplete"](https://antithesis.com/docs/generated/sdk/python/antithesis/lifecycle.html#setup_complete) signals that the system is ready to test. For example, in `entrypoint.py`: 

`setup_complete({"Message":"ETCD cluster is healthy"})`

### Assertions

Antithesis SDKs allow users to [express the properties their software should have,](https://antithesis.com/docs/properties_assertions/) by [adding assertions to their code](https://antithesis.com/docs/properties_assertions/assertions/). We use 4 types of assertions in this repo. 

#### Sometimes Assertions

[Sometimes assertions](https://antithesis.com/docs/properties_assertions/properties/#sometimes-properties) check that intended funcitonality *happens at least once in the course of testing* - in this case, that operations happen against the etcd cluster and that validation occurs. For example, in `parallel_driver_generate_traffic.py`: 

`sometimes(success,"client can make successful put requests",None)`

#### Always Assertions

[Always assertions](https://antithesis.com/docs/properties_assertions/properties/#always-properties) check that something (like a guarantee) *always happens, on every execution history.* In this case, in `serial_driver_validate_operations.go` this line checks that every operation is linearizable: 

`assert.Always(result == true, "Operations against the cluster are linearizable", nil)`

#### Reachable Assertions

Reachable assertions will evaluate if that part of code was reached. In `EventuallyValidation.java`, we have the following line:

`reachable("Performing health check on the etcd cluster", null);`

If our test hits this line of code at least once, it will pass.

#### Unreachable Assertions

Unreachable assertions will evaluate if that part of code was not reached. They are written in places that we do not want to reach. An example would be in code sections for error handling. In `parallel_driver_generate_traffic.py` we have the following assertion:

`unreachable("Client fails to connects to an etcd host", {"traffic_id":traffic_id, "host":host, "error":e})`

We expect to always to connect to an etcd host. If this assertion is ever hit, then the property will fail.

### Randomness

Randomness is key for autonomous testing, since we want the software to follow many, unpredictable execution paths. [The Antithesis SDK](https://antithesis.com/docs/using_antithesis/sdk/#randomness) provides an easy interface to get structured random values while also providing valuable guidance to the Antithesis platform, which increases the efficiency of testing.

## Testing Locally

Before running your application on the Antithesis platform, it can be convenient to check your work locally before you kick off a full Antithesis test run.

This is a 3 step process, which is [described in greater detail here](https://antithesis.com/docs/test_templates/testing_locally/): 

1. Pull the bitnami/etcd:3.5 image using the following command: 

`docker pull bitnami/etcd:3.5`

2. Build the client image. From within the `/test-template` directory, run the following command: 

`docker build . -t etcd-client:latest`

3. run `docker-compose up` from the root directory to start all containers defined in `docker-compose.yml`

4. After the client container has signaled `setupComplete` (or printed `cluster is healthy`), you can run the parallel driver 1 to many times via `docker exec`: 

`docker exec client /opt/antithesis/test/v1/main/parallel_driver_generate_traffic.py`

5. After that completes, you can run the serial driver in the same fashion: 

`docker exec client /opt/antithesis/test/v1/main/serial_driver_validate_operations`

You should see a message: `Client [serial_driver_validate]: validation complete done`

6. Run the other commands in the /opt/antithesis/test/v1/main directory. The eventually will print out `Client [eventually_validation]: all nodes are up during health check`. Running the finally afterwards could fail because the eventually was ran prior. The finally checks for a key space <= 6, but the eventually adds 3 keys to the database. Within Antithesis, a finally and eventually command will never be run within the same timeline. Instead, rerun the setup and execute the finally before the eventually. Now, we will see it pass.

You've now validated that your test is ready to run on the Antithesis platform! (Note that SDK assertions won't be evaluated locally).

## Example Report

Using the three node etcd cluster and the `client` image built from this repository, we ran a 3 hour test. The resulting [triage report](https://antithesis.com/docs/reports/triage/) can be found [here](https://public.antithesis.com/report/I3S-m-GVTlo4mZ0VmMi7KM36/j-Va1hEqG_lEbVw9qJfnAdflU2KyOt3gmr5Ge9myzZs.html), and [our docs](https://antithesis.com/docs/reports/triage/) show you how to interpret it. 
