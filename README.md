# Etcd-test-composer

## Purpose

This repo demonstrates the use of the [Antithesis platform](https://antithesis.com/product/what_is_antithesis/) to test [etcd](https://etcd.io/). Follow the step by step tutorial [here](https://antithesis.com/docs/tutorials/)

## Setup

There are 4 containers running in this system: 3 that make up an etcd cluster (`etcd0`, `etcd1`, `etcd2`) and one that `client`. 

The `client` container runs the `entrypoint.py` script runs when it starts. This script confirms that all of the etcd hosts are available before [signaling the software is ready to test](https://antithesis.com/docs/tutorials/cluster-setup/#ready-signal). 
