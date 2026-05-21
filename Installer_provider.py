import socket
import hashlib
import os

VERSION = "1.0.0"

FILES_TO_SEND = [
    "Client.py",
    "Game.py"
]


def calculate_md5(filepath):
    md5 = hashlib.md5()

    with open(filepath, "rb") as f:
        while chunk := f.read(4096):
            md5.update(chunk)

    return md5.hexdigest()


def send_file(conn, filepath):
    filename = os.path.basename(filepath)
    filesize = os.path.getsize(filepath)
    filehash = calculate_md5(filepath)

    # FILE HEADER
    header = (
        f"FILE:{filename}\n"
        f"SIZE:{filesize}\n"
        f"MD5:{filehash}\n\n"
    )

    conn.sendall(header.encode())

    # FILE DATA
    with open(filepath, "rb") as f:
        while chunk := f.read(4096):
            conn.sendall(chunk)

    print(f"Sent {filename}")


def start_server(host="0.0.0.0", port=65432):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()

        print(f"Server listening on {host}:{port}")

        try:
            while True:
                conn, addr = s.accept()

                with conn:
                    print(f"Connected by {addr}")

                    # VERSION CHECK
                    client_version = conn.recv(1024).decode().strip()

                    if client_version != f"VERSION:{VERSION}":
                        print("Client version mismatch.")
                        conn.close()
                        return

                    # SEND NUMBER OF FILES
                    conn.sendall(f"COUNT:{len(FILES_TO_SEND)}\n\n".encode())

                    # SEND FILES
                    for file in FILES_TO_SEND:
                        send_file(conn, file)

                    print("Finished sending all files.\n")

        except KeyboardInterrupt:
            print("Server shutting down...")


start_server()