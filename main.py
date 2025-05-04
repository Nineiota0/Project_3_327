from flask import Flask, request, jsonify, send_from_directory
import hashlib
import requests

app = Flask(__name__)

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
            return jsonify({"key": key, "value": kv_store[key]})
        else:
            return jsonify({"error": "key not found"}), 404
    else:
        res = requests.get(f"{responsible_node}/kv/{key}")
        return res.json(), res.status_code

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)