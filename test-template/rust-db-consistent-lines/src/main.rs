use std::thread;
use std::time::Duration;
use etcd_client::*;
use tokio;
use serde_json::{json};
use antithesis_sdk::{assert_always, antithesis_init};

#[tokio::main]
async fn main() -> Result<(), Error> {

    antithesis_init();

    // When finally commands are run, the fault injector is turned off. Sleeping 15 seconds allows the system to recover.
    let duration = Duration::new(15, 0);
    thread::sleep(duration);

    let mut client = Client::connect(["http://etcd0:2379"], None).await?;

    // Delete all keys
    println!("Deleting all keys...");
    client.delete("", Some(DeleteOptions::new().with_all_keys())).await?;

    // Sleep 1 second
    let duration = Duration::new(1, 0);
    thread::sleep(duration);

    // Connect to a different etcd node
    let mut client = Client::connect(["http://etcd1:2379"], None).await?;

    // Get all the keys that are in the etcd cluster
    let response = client.get("", Some(GetOptions::new().with_all_keys())).await?;

    // Count the number of keys that we received
    let count = response.kvs().len();

    println!("Number of entries in etcd: {}", count);

    // Always assertion that the number of key values in the database is 0.
    let details = json!({"key_space_size": count});
    assert_always!(count == 0, "When all keys are deleted, there are 0 keys in the database", &details);

    // Define 6 key values
    let keys = vec![
        ("k1", "v1"),
        ("k2", "v2"),
        ("k3", "v3"),
        ("k4", "v4"),
        ("k5", "v5"),
        ("k6", "v6"),
    ];

    // Write 6 key values to the etcd database
    for (key, value) in keys {
        println!("Writing key: {} with value: {}", key, value);
        client.put(key, value, None).await?;
    }

    // Sleep 1 second
    let duration = Duration::new(1, 0);
    thread::sleep(duration);

    // Connect to a different etcd node
    let mut client = Client::connect(["http://etcd2:2379"], None).await?;

    // Get all keys to verify
    println!("Verifying keys...");
    let response = client.get("", Some(GetOptions::new().with_all_keys())).await?;
    let count = response.kvs().len();
    
    println!("There are {} keys in the database.", count);

    // Always assertion that the number of key values in the database is 6.
    let details = json!({"key_count": count});
    assert_always!(count == 6, "There should only be 6 kv pairs in the database", &details);

    Ok(())
}