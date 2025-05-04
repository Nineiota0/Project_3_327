from flask import Flask, request, jsonify, send_from_directory
import hashlib
import requests
import random
import threading
import time

app = Flask(__name__)

# Known peer addresses
NODES = {
    'node1': 'http://node1:5000',
    'node2': 'http://node2:5000'
}
PEERS = set(NODES.values())

kv_store = {}

# --- Distributed Hashing ---
def hash_key_to_node(key):
    h = hashlib.sha1(key.encode()).hexdigest()
    node_hash = int(h, 16) % len(NODES)
    return list(NODES.values())[node_hash]

# --- File Handling ---
@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    file.save(f"./storage/{file.filename}")
    return jsonify({"status": "uploaded", "filename": file.filename})

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory('./storage', filename)

# --- Key-Value Store ---
@app.route('/kv', methods=['POST'])
def insert_kv():
    data = request.get_json()
    responsible_node = hash_key_to_node(data['key'])
    current_node = get_current_node_url()

    if responsible_node == current_node:
        kv_store[data['key']] = data['value']
        return jsonify({"status": "stored", "key": data['key'], "value": data['value']})
    else:
        res = requests.post(f"{responsible_node}/kv", json=data)
        return res.json()

@app.route('/kv/<key>', methods=['GET'])
def get_kv(key):
    responsible_node = hash_key_to_node(key)
    current_node = get_current_node_url()

    if responsible_node == current_node:
        if key in kv_store:
            return jsonify({"key": key, "value": kv_store[key]})
        else:
            return jsonify({"error": "key not found"}), 404
    else:
        res = requests.get(f"{responsible_node}/kv/{key}")
        return res.json(), res.status_code

# --- Gossip Protocol ---
@app.route('/gossip', methods=['POST'])
def gossip():
    data = request.get_json()
    new_peers = set(data.get("peers", []))
    ttl = data.get("ttl", 2)

    # Update known peers
    PEERS.update(new_peers)

    # Forward gossip to a random peer if TTL > 0
    if ttl > 0:
        ttl -= 1
        forward_peers = list(PEERS - {get_current_node_url()})
        if forward_peers:
            neighbor = random.choice(forward_peers)
            try:
                requests.post(f"{neighbor}/gossip", json={
                    "peers": list(PEERS),
                    "ttl": ttl
                }, timeout=1)
            except requests.exceptions.RequestException:
                pass

    return jsonify({"status": "gossip received", "known_peers": list(PEERS)})

def gossip_loop():
    def gossip_task():
        while True:
            time.sleep(10)
            if PEERS:
                peer = random.choice(list(PEERS - {get_current_node_url()}))
                try:
                    requests.post(f"{peer}/gossip", json={
                        "peers": list(PEERS),
                        "ttl": 2
                    }, timeout=1)
                except requests.exceptions.RequestException:
                    pass
    thread = threading.Thread(target=gossip_task, daemon=True)
    thread.start()

def get_current_node_url():
    host = request.host.split(':')[0]
    for name, url in NODES.items():
        if name in host or url in request.host_url:
            return url
    return list(NODES.values())[0]  # fallback

if __name__ == '__main__':
    gossip_loop()
    app.run(host='0.0.0.0', port=5000)
