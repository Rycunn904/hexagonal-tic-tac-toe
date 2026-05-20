import hashlib

with open("Client.py", "rb") as f:
    code_bytes = f.read()
    client_hash = hashlib.md5(code_bytes).hexdigest()
    print(client_hash)
print(__file__)