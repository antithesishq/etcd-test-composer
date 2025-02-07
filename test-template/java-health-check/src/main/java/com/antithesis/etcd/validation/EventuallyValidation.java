package com.antithesis.etcd.validation;

import static com.antithesis.sdk.Assert.*;
import io.etcd.jetcd.Client;
import io.etcd.jetcd.KV;
import io.etcd.jetcd.kv.PutResponse;
import io.etcd.jetcd.kv.GetResponse;
import io.etcd.jetcd.ByteSequence;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeUnit;
import java.nio.charset.StandardCharsets;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;


public class EventuallyValidation {

    static void connect(String etcdEndpoint, String key, String value) throws ExecutionException, InterruptedException{

        Client client = Client.builder().endpoints(etcdEndpoint).build();

        KV kvClient = client.getKVClient();

        ByteSequence keyInBytes = ByteSequence.from(key, StandardCharsets.UTF_8);
        ByteSequence valueInBytes = ByteSequence.from(value, StandardCharsets.UTF_8);

        kvClient.put(keyInBytes, valueInBytes).get();

        GetResponse getResponse = kvClient.get(keyInBytes).get();

        String retrievedValue = getResponse.getKvs().get(0).getValue().toString(StandardCharsets.UTF_8);

        System.out.println("Client [eventually_validation]: retrieved value for '" + key + "': " + retrievedValue);

        client.close();

        // We should NEVER go in this loop because that would mean we have a key value mismatch.
        if (!retrievedValue.equals(value)) {
            ObjectMapper mapper = new ObjectMapper();
            ObjectNode request_details = mapper.createObjectNode();
            request_details.put("key", key);
            request_details.put("value", value);
            request_details.put("retrieve_value", retrievedValue);
            unreachable("Data is inconsistent during health check", request_details);
        }
    }

    public static void main(String[] args) {

        // We should reach this code section while our software is under test.
        reachable("Performing health check on the etcd cluster", null);

        // When finally commands are run, the fault injector is turned off. Sleeping 15 seconds allows the system to recover.
        try {
            TimeUnit.SECONDS.sleep(15);
        } catch(InterruptedException e) {
            System.out.println("Interrupted exception was hit during health check");
            System.exit(1);
        }
        
        String[] etcdEndpoints = {"http://etcd0:2379", "http://etcd1:2379", "http://etcd2:2379"};

        String[] keys = {"foo1", "foo2", "foo3"};

        String[] values = {"bar1", "bar2", "bar3"};

        int nodesHealthy = 0;

        for (int i = 0; i < 3; i++) {
            try {
                connect(etcdEndpoints[i], keys[i], values[i]);
                nodesHealthy++;
            } catch(ExecutionException e) {
                unreachable("Execution exception was hit during health check", null);
            } catch(InterruptedException e) {
                unreachable("Interrupted exception was hit during health check", null);
            }
        }

        // After 15 second quiescent period, we should expect our system to have recovered and is available.
        // The always assertion below checks that all three nodes are available.
        ObjectMapper mapper = new ObjectMapper();
        ObjectNode healthy_node_details = mapper.createObjectNode();
        healthy_node_details.put("num_nodes_healthy", nodesHealthy);
        always(nodesHealthy == 3, "All nodes are up during health check", healthy_node_details);

        if (nodesHealthy == 3) {
            System.out.println("Client [eventually_validation]: all nodes are up during health check");
        } else {
            System.out.println("Client [eventually_validation]: at least one node is not available during health check");
        }
    }
}