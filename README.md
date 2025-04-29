# Etcd-test-composer

## Purpose

This repo demonstrates the use of the [Antithesis platform](https://antithesis.com/product/what_is_antithesis/) to test [etcd](https://etcd.io/). Follow the step-by-step tutorial [here](https://antithesis.com/docs/tutorials/)

## Setup

4 containers running in this system: 3 that make up an etcd cluster (`etcd0`, `etcd1`, `etcd2`) and one `health-checker`. 

The `health-checker` container runs the `entrypoint.py` script which [signals that the system is ready for testing](https://antithesis.com/docs/tutorials/cluster-setup/#ready-signal). 
