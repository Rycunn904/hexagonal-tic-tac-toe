import socket
import hashlib
import os

VERSION = "1.0.0"


def calculate_md5(filepath):
    md5 = hashlib.md5()

    with open(filepath, "rb") as f:
        while chunk := f.read(4096):
            md5.update(chunk)

    return md5.hexdigest()


def recv_until(sock, delimiter=b"\n\n"):
    data = b""

    while delimiter not in data:
        chunk = sock.recv(1024)

        if not chunk:
            break

        data += chunk

    return data


def download_files(host="127.0.0.1", port=65432):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

        try:
            s.connect((host, port))

        except Exception as e:
            print("Connection failed:", e)
            return

        # VERSION CHECK
        s.sendall(f"VERSION:{VERSION}\n".encode())

        # FILE COUNT
        count_data = recv_until(s).decode()

        file_count = int(
            count_data.split("COUNT:")[1]
            .split("\n")[0]
        )

        print(f"Receiving {file_count} files...\n")

        for _ in range(file_count):

            # READ FILE HEADER
            header_data = recv_until(s)

            header, remaining = header_data.split(b"\n\n", 1)

            lines = header.decode().split("\n")

            filename = lines[0].split(":")[1]
            filesize = int(lines[1].split(":")[1])
            expected_md5 = lines[2].split(":")[1]

            print(f"Receiving: {filename}")
            print(f"Size: {filesize}")
            print(f"MD5: {expected_md5}")

            save_path = os.path.join(
                os.path.dirname(__file__),
                filename
            )

            bytes_received = len(remaining)

            with open(save_path, "wb") as f:

                f.write(remaining)

                while bytes_received < filesize:
                    chunk = s.recv(4096)

                    if not chunk:
                        break

                    f.write(chunk)
                    bytes_received += len(chunk)

            # VERIFY HASH
            actual_md5 = calculate_md5(save_path)

            if actual_md5 == expected_md5:
                print(f"{filename} verified.\n")

            else:
                print(f"{filename} corrupted!\n")


IP = input("Enter server IP: ")

download_files(host=IP)