from flask import Flask, request, jsonify, send_from_directory

import threading
import requests
import logging
import hashlib
import random
import time

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NODES = {
    'node1': 'http://node1:5000',
    'node2': 'http://node2:5000'
}

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    file.save(f"./storage/{file.filename}")
    return jsonify({"status": "uploaded", "filename": file.filename})

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory('./storage', filename)

# Simple in-memory key-value store
kv_store = {}

def hash_key_to_node(key):
    h = hashlib.sha1(key.encode()).hexdigest()
    node_hash = int(h, 16) % len(NODES)
    return list(NODES.values())[node_hash]

@app.route('/kv', methods=['POST'])
def insert_kv():
    data = request.get_json()
    responsible_node = hash_key_to_node(data['key'])
    current_node = NODES['node1'] if 'node1' in request.host else NODES['node2']

    if responsible_node == current_node:
        # This node is responsible
        kv_store[data['key']] = data['value']
        return jsonify({"status": "stored", "key": data['key'], "value": data['value']})
    else:
        # Forward to responsible node
        res = requests.post(f"{responsible_node}/kv", json=data)
        return res.json()

@app.route('/kv/<key>', methods=['GET'])
def get_kv(key):
    responsible_node = hash_key_to_node(key)
    current_node = NODES['node1'] if 'node1' in request.host else NODES['node2']

    if responsible_node == current_node:
        if key in kv_store:
            logger.info(f"[KV] Returning local key {key}")
            return jsonify({"key": key, "value": kv_store[key]})
        else:
            logger.info(f"[KV] Key {key} not found locally")
            return jsonify({"error": "key not found"}), 404
    else:
        logger.info(f"[KV] Forwarding GET /kv/{key} to {responsible_node}")
        res = requests.get(f"{responsible_node}/kv/{key}")
        return res.json(), res.status_code

def forward_gossip(ttl):
    neighbors = list(NODES.values())
    current_host = request.host.split(':')[0] if request else 'node1'
    my_node_url = NODES['node1'] if 'node1' in current_host else NODES['node2']
    neighbors = [n for n in neighbors if n != my_node_url]

    if not neighbors:
        return

    target_node = random.choice(neighbors)
    logger.info(f"[GOSSIP] Forwarding gossip to {target_node} with ttl={ttl}")
    try:
        requests.post(f"{target_node}/gossip", json={
            "kv_store": kv_store,
            "ttl": ttl
        })
    except Exception as e:
        logger.info(f"[GOSSIP] Error forwarding gossip: {e}")

@app.route('/gossip', methods=['POST'])
def gossip():
    data = request.get_json()
    ttl = data.get('ttl', 0)
    incoming_store = data.get('kv_store', {})

    logger.info(f"[GOSSIP] Received gossip with ttl={ttl}. Keys: {list(incoming_store.keys())}")

    for key, value in incoming_store.items():
        if key not in kv_store:
            logger.info(f"[GOSSIP] Adding new key from gossip: {key}")
        kv_store[key] = value

    if ttl > 0:
        forward_gossip(ttl - 1)

    return jsonify({"status": "gossip received", "ttl": ttl})


def start_gossip_loop():
    def gossip_job():
        while True:
            time.sleep(180)  # every 3 minutes
            forward_gossip(ttl=2)  # initial TTL = 2

    t = threading.Thread(target=gossip_job, daemon=True)
    t.start()

if __name__ == '__main__':
    start_gossip_loop()
    app.run(host='0.0.0.0', port=5000)
