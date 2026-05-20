import socket
import hashlib
import os
import sys

VERSION = "1.0.1"

print("Installer Provider")

def calculate_md5(filepath):
    md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        while chunk := f.read(4096):
            md5.update(chunk)
    return md5.hexdigest()


def start_server(file_to_send, host='25.33.184.209', port=65432):
    file_size = os.path.getsize(file_to_send)
    file_hash = calculate_md5(file_to_send)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen(1)

        print(f"Serving {file_to_send}")
        print(f"Size: {file_size} bytes")
        print(f"MD5: {file_hash}")

        s.settimeout(1)
        connected = False
        conn = None
        addr = None
        while not connected:
            try:
                conn, addr = s.accept()
                connected = True
            except socket.timeout:
                continue
            except KeyboardInterrupt:
                print("Canceling server...")
        with open(file_to_send, 'rb') as f:
            print(f"Connected: {addr}")
            # ---- SEND VERSION CHECK ----
            conn.sendall(f"VERSION:{VERSION}\n".encode()) # type: ignore

            # ---- SEND HEADER ----
            header = f"SIZE:{file_size}\nMD5:{file_hash}\n\n"
            conn.sendall(header.encode()) # type: ignore

            # ---- SEND FILE ----
            while chunk := f.read(4096):
                conn.sendall(chunk) # type: ignore

            print("File sent successfully.")

if len(sys.argv) > 1:
    IP = sys.argv[1]
else:
    IP = input("Enter server IP (blank to send on all addresses): ")
start_server(__file__.replace("Installer_provider.py", "Client.py"), host=IP)
start_server(__file__.replace("Installer_provider.py", "Game.py"), host=IP)