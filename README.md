# Setup Instructions

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Start the Network:

To start the P2P network, use the provided `run.py` script. This script automates the creation of the Docker network, starts the bootstrap node, launches peer nodes, and checks their registration.

```bash
python run.py
```
This will:
* Create a docker network (p2p_network)
* Start the bootstrap node
* Launch 100 peer nodes
* Wait for nodes to reigster and discover peers

**Check Peer Registration**
-The script automatically checks peer registration by querying the /peers endpoint of the bootstrap node. You can manually verify it by running:
```bash
curl http://localhost:5000/peers
```
Expected Output:
```bash
{"peers": ["http://node1:5000", "http://node2:5000"]}
```

## Usage

### Start Multiple Nodes

You can manually start individual nodes using Docker. Here is how to start two nodes:

```bash
docker run -d --name node1 -p 5001:5000 p2p-node
docker run -d --name node2 -p 5002:5000 p2p-node
```

### File Upload and Download (Phase 1)
File upload and download are supported with local storage on each node.

1. Upload a file to a node:
```bash
curl -F 'file=@mydoc.txt' http://localhost:5001/upload
```

2. Download a file from a node:
Visit `http://localhost:5001/download/mydoc.txt` in your browser, or use:
```bash
curl http://localhost:5001/download/mydoc.txt -o downloaded_file.txt
```

### Key-Value Store (Phase 2)
The system supports an in-memory key-value store on each node.

1. Store a key-value pair:
```bash
curl -X POST http://localhost:5001/kv -H "Content-Type: application/json" -d '{"key": "color", "value": "blue"}'
```

2. Retrieve a value by key:
```bash
curl http://localhost:5001/kv/color
```

### DHT-Based Routing for Storage (Phase 3)
The system now uses distributed hash table (DHT) for routing key-value storage requests to the appropriate node.

1. How it works:
   - SHA-1 hashing is used to determine which node is responsible for a key
   - Requests are automatically forwarded to the responsible node
   - The node responsible for a key is determined by consistent hashing

2. Benefits:
   - Evenly distributes storage responsibilities across all nodes
   - Any node can handle requests for any key
   - No central coordinator required

### Send a Message Between Nodes
```bash
curl -X POST http://localhost:5002/message -H "Content-Type:
application/json" -d '{"sender_id": "Node1", "message": "Hello Node2!"}'
```
* Logs will display the following message:
```bash
Received message from Node1: Hello Node2!
```
* Receiving node will display the following message:
```bash
{"status": "received"}
```

### Endpoint testing
This test script will run a series of automated tests to verify functionality of the various endpoints in the distributed system. The tests will check the ability to upload and download files as well as perform key-value insertions and queries.
To execute these tests, simply run the script:
```bash
python test_main_endpoints.py
```

The result should look like this:
```bash
$ python test_main_endpoints.py
[*] Uploading file...
Upload Response: {'filename': 'mydoc.txt', 'status': 'uploaded'}
[*] Downloading file...
Downloaded content: Hello, this is a test document.
[*] Inserting key-value pair...
Insert Response: {'key': 'color', 'status': 'stored', 'value': 'blue'}
[*] Querying key-value pair...
Query Response: {'key': 'color', 'value': 'blue'}
```
### Option 3: Gossip Protocol
• Periodically share peer lists with random neighbors.
• Limit message flooding using TTL (time-to-live) metadata.

To test this run:
```bash
python test_gossip.py
```

The message received should be:
```bash
Gossip sent: {'known_peers': ['http://node1:5000', 'http://localhost:5001', 'http://node2:5000'], 'status': 'gossip received'}
Gossip received at node2: {'known_peers': ['http://node1:5000', 'http://localhost:5002', 'http://node2:5000'], 'status': 'gossip received'}
```
