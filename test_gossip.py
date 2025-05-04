import requests
import time

def test_gossip():
    node1 = "http://localhost:5001"
    node2 = "http://localhost:5002"

    # Trigger initial gossip from node1
    res = requests.post(f"{node1}/gossip", json={
        "peers": [node1],
        "ttl": 2
    })
    print(f"Gossip sent: {res.json()}")

    # Wait a bit for gossip to propagate
    time.sleep(5)

    # Check known peers at node2
    res = requests.post(f"{node2}/gossip", json={
        "peers": [node2],
        "ttl": 0
    })
    print(f"Gossip received at node2: {res.json()}")

if __name__ == '__main__':
    test_gossip()
