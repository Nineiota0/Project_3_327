import requests
import os

# Base URL of the node you're testing
NODE_URL = 'http://localhost:5001'

def test_upload_file():
    print("[*] Uploading file...")
    with open("mydoc.txt", "w") as f:
        f.write("Hello, this is a test document.")
    with open("mydoc.txt", "rb") as f:
        files = {'file': f}
        response = requests.post(f"{NODE_URL}/upload", files=files)
    print("Upload Response:", response.json())
    assert response.status_code == 200

def test_download_file():
    print("[*] Downloading file...")
    response = requests.get(f"{NODE_URL}/download/mydoc.txt")
    with open("downloaded_mydoc.txt", "wb") as f:
        f.write(response.content)
    print("Downloaded content:", response.content.decode())
    assert response.status_code == 200

def test_kv_insert_and_query():
    print("[*] Inserting key-value pair...")
    data = {'key': 'color', 'value': 'blue'}
    response = requests.post(f"{NODE_URL}/kv", json=data)
    print("Insert Response:", response.json())
    assert response.status_code == 200

    print("[*] Querying key-value pair...")
    response = requests.get(f"{NODE_URL}/kv/color")
    print("Query Response:", response.json())
    assert response.status_code == 200
    assert response.json().get("value") == "blue"

if __name__ == '__main__':
    test_upload_file()
    test_download_file()
    test_kv_insert_and_query()

    # Clean up test files
    os.remove("mydoc.txt")
    os.remove("downloaded_mydoc.txt")
