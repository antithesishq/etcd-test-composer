package com.antithesis.etcd.validation;

// TODO: import Java SDK
import static com.antithesis.sdk.Assert.*;
import io.etcd.jetcd.Client;
import io.etcd.jetcd.KV;
import io.etcd.jetcd.kv.PutResponse;
import io.etcd.jetcd.kv.GetResponse;
import io.etcd.jetcd.ByteSequence;
import java.util.concurrent.ExecutionException;
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

        System.out.println("Retrieved value for '" + key + "': " + retrievedValue);

        client.close();

        //unreachable because key & value should always be consistent here
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

        // always assertion for nodesHealthy == 3
        ObjectMapper mapper = new ObjectMapper();
        ObjectNode healthy_node_details = mapper.createObjectNode();
        healthy_node_details.put("num_nodes_healthy", nodesHealthy);
        System.out.println("All nodes are up during health check");
        always(nodesHealthy == 3, "All nodes are up during health check", healthy_node_details);
    }
}