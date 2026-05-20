import socket
import hashlib

# Version 1.0.1
VERSION = "1.0.0"

def calculate_md5(filepath):
    md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        while chunk := f.read(4096):
            md5.update(chunk)
    return md5.hexdigest()


def download_file(save_as, host='127.0.0.1', port=65432):
    save_as = __file__.replace("Client_installer.py", save_as)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((host, port))
        except Exception as e:
            print("Connection failed:", e)
            return False, host, port
        # ---- READ VERSION CHECK ----
        version_data = s.recv(1024).decode().strip()
        if not version_data == f"VERSION:{VERSION}":
            print("Invalid version from server:", version_data)
            return False, host, port

        # ---- READ HEADER ----
        buffer = ""
        while "\n\n" not in buffer:
            buffer += s.recv(1024).decode()

        header, remaining = buffer.split("\n\n", 1)

        lines = header.split("\n")
        file_size = int(lines[0].split(":")[1])
        expected_md5 = lines[1].split(":")[1]

        print(f"Expected Size: {file_size}")
        print(f"Expected MD5: {expected_md5}")

        # ---- RECEIVE FILE ----
        bytes_received = len(remaining.encode())
        with open(save_as, "wb") as f:
            f.write(remaining.encode())  # write leftover data

            while bytes_received < file_size:
                chunk = s.recv(4096)
                if not chunk:
                    break
                f.write(chunk)
                bytes_received += len(chunk)

        print("Download complete.")
        return True, host, port

    # ---- VERIFY MD5 ----
    actual_md5 = calculate_md5(save_as)
    print(f"Actual MD5: {actual_md5}")

    if actual_md5 == expected_md5:
        print("File integrity verified (no corruption)")
    else:
        print("File corrupted! MD5 mismatch")

IP = input("Enter server IP: ")
fail, ip, port = download_file("Client.py", host=IP)
if fail:
    download_file("Game.py", host=IP)
else:
    print(f"{ip} is not responding on port {port}. Please check the provider and try again.")