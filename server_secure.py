#1.1.3
import socket
import threading
import os
import shutil
import hashlib
from datetime import datetime
import numpy as np
from math import ceil

master_directory = "./projects/"

def sendhuge(client, data) -> None:
    length = len(data)
    client.send(f"{length}\n".encode("ascii"))
    client.sendall(data)


def sendhuge_secure(client, data, key) -> None:
    key_length = len(key)
    length = len(data)
    client.send(f"{length}\n".encode("ascii"))
    sending_bytes = b""
    packet_size = ceil((4096 - key_length * 2) / key_length) * key_length
    
    key_to_apply = np.frombuffer((key * ceil(length / key_length))[:packet_size], dtype=np.uint8)
    for i in range(0, length, packet_size):
        raw_bytes = np.frombuffer(data[i: i+packet_size], dtype=np.uint8)
        if i + packet_size >= length:
            sending_bytes = raw_bytes + key_to_apply[:len(raw_bytes)]
        else:
            sending_bytes = raw_bytes + key_to_apply
        client.sendall(sending_bytes)
        precentage = i/length*100
        print(f"\r{precentage} %", end="")
    

def log(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    
def recvhuge(client) -> bytes:
    length = b""
    while True:
        if client.recv(1, socket.MSG_PEEK) == 0:
            continue
        recved = client.recv(1)
        if recved == b'\n':
            break
        if recved == b'':
            return b""
        length += recved
    length = int(length)
    recved = b''
    while True:
        recved += client.recv(length - len(recved))
        if len(recved) == length:
            break
        precentage = len(recved)/length*100
        print(f"\r{precentage} %", end="")
    print(f"\r100 %")
    return recved

def recvhuge_secure(client, key) -> bytes:
    length = b""
    while True:
        if client.recv(1, socket.MSG_PEEK) == 0:
            continue
        recved = client.recv(1)
        if recved == b'\n':
            break
        if recved == b'':
            return b""
        length += recved
    length = int(length)
    key_length = len(key)
    recved = b""
    buffer = b""
    optimal_packet_size = ceil((4096 - key_length * 2) / key_length) * key_length
    while True:
        if len(client.recv(length - len(recved), socket.MSG_PEEK)) >= optimal_packet_size:
            buffer = client.recv(optimal_packet_size)
            key_to_apply = key * (len(buffer) // key_length)
            recved += (np.frombuffer(buffer, dtype=np.uint8) - np.frombuffer(key_to_apply, dtype=np.uint8)).tobytes()
        if length - len(recved) < optimal_packet_size and len(client.recv(length - len(recved), socket.MSG_PEEK)) == length - len(recved):
            buffer = client.recv(optimal_packet_size)
            key_to_apply = (key * ceil(len(buffer) / key_length))[:len(buffer)]
            recved += (np.frombuffer(buffer, dtype=np.uint8) - np.frombuffer(key_to_apply, dtype=np.uint8)).tobytes()
        if len(recved) == length:
            break
        precentage = len(recved)/length*100
        print(f"\r{precentage} %", end="")
    print(f"\r100 %")
    return recved

def recvfile(client, path) -> int:
    length = b""
    while True:
        if client.recv(1, socket.MSG_PEEK) == 0:
            continue
        recved = client.recv(1)
        if recved == b'\n':
            break
        if recved == b'':
            return b""
        length += recved
    length = int(length)
    file = open(path, "wb")
    total_length = 0
    while True:
        packet = client.recv(length - total_length)
        file.write(packet)
        total_length += len(packet)
        if total_length == length:
            break
        precentage = total_length/length*100
        print(f"\r{precentage} %", end="")
    print(f"\r100 %")
    return length

def recvfile_secure(client, path, key) -> bytes:
    length = b""
    while True:
        if client.recv(1, socket.MSG_PEEK) == 0:
            continue
        recved = client.recv(1)
        if recved == b'\n':
            break
        if recved == b'':
            return b""
        length += recved
    length = int(length)
    key_length = len(key)
    recved = b""
    buffer = b""
    optimal_packet_size = ceil((4096 - key_length * 2) / key_length) * key_length
    total_length = 0
    with open(path, "wb") as file:
        while True:
            if len(client.recv(length - len(recved), socket.MSG_PEEK)) >= optimal_packet_size:
                buffer = client.recv(optimal_packet_size)
                total_length += len(buffer)
                key_to_apply = key * (len(buffer) // key_length)
                file.write((np.frombuffer(buffer, dtype=np.uint8) - np.frombuffer(key_to_apply, dtype=np.uint8)).tobytes())
            if length - len(recved) < optimal_packet_size and len(client.recv(length - len(recved), socket.MSG_PEEK)) == length - len(recved):
                buffer = client.recv(optimal_packet_size)
                total_length += len(buffer)
                key_to_apply = (key * ceil(len(buffer) / key_length))[:len(buffer)]
                file.write((np.frombuffer(buffer, dtype=np.uint8) - np.frombuffer(key_to_apply, dtype=np.uint8)).tobytes())
            if total_length == length:
                break
            precentage = len(recved)/length*100
            print(f"\r{precentage} %", end="")
    print(f"\r100 %")
    return recved

def tree_dir(path) -> str:
    result = ""
    tab = "    "
    for root, dirs, files in os.walk(path):
        level = root.replace(path, '').count(os.sep)
        result += f"{tab * level}{'-'+os.path.basename(root)}\n"
        for f in files:
            result += f"{tab * (level+1)}{f}\n"
    return result

def create_dir(path):
    try:
        os.mkdir(path)
    except FileExistsError:
        return True
    return False

def create_sets(master, proj, ver):
    create_dir(os.path.join(master, proj))
    create_dir(os.path.join(os.path.join(master, proj), ver))

def find_max_length(arr):
    a = []
    for elem in arr:
        a.append(len(elem))
    return max(a)
def find_max_in_column(arr, column):
    a = []
    for elem in arr:
        if len(elem) <= column:
            continue
        a.append(elem[column])
    return max(a)
def find_latest(master, proj):
    separated = []
    for version in os.listdir(os.path.join(master, proj)):
       if not version.replace(".", "").isdigit():
           continue
       separated.append([int(elem) for elem in version.split(".")])
    chosen = separated
    for i in range(find_max_length(separated)):
        if find_max_length(chosen) <= i:
            continue
        maximum = find_max_in_column(chosen, i)
        left = []
        for elem in chosen:
            if len(elem) <= i:
                left.append(elem)
                continue
            if elem[i] == maximum:
                left.append(elem)
        chosen = list(left)
    return ".".join([str(char) for char in chosen[0]])


def handle_client(client, address):
    if hashed_password != hashlib.sha256(b"").hexdigest():
        sendhuge(client, b"auth")
        try:
            log(f"waiting for password auth for client: {address}")
            received_hashed_password = recvhuge(client).decode("utf-8")
        except ValueError:
            log(f"unknown format encountered with client: {address}")
            client.close()
            return
        if received_hashed_password != hashed_password:
            sendhuge(client, b"denied")
            client.close()
            return
        sendhuge(client, b"granted")
    else:
        sendhuge(client, b"no auth")
    
    project_name = ""
    while True:
        try:
            try:
                recved = recvhuge_secure(client, encryption_key)
            except ValueError:
                log(f"unknown format encountered with client: {address}\n{recved[:100]}")
                client.close()
                raise BrokenPipeError()
            log(f"{address}: {recved}")
            if recved == b'':
                raise BrokenPipeError()
            if recved == b"save":
                version = recvhuge_secure(client, encryption_key).decode("utf-8")
                filename = recvhuge_secure(client, encryption_key).decode("utf-8")
                create_sets(master_directory, project_name, version)
                recvfile_secure(client, os.path.join(master_directory, project_name, version, filename), encryption_key)
            if recved == b"saveall":
                version = recvhuge_secure(client, encryption_key).decode("utf-8")
                n_files = int(recvhuge_secure(client, encryption_key).decode("utf-8"))
                for _ in range(n_files):
                    filename = recvhuge_secure(client, encryption_key).decode("utf-8")
                    create_sets(master_directory, project_name, version)
                    recvfile_secure(client, os.path.join(master_directory, project_name, version, filename), encryption_key)
            if recved == b"load":
                version = recvhuge_secure(client, encryption_key).decode("utf-8")
                filename = recvhuge_secure(client, encryption_key).decode("utf-8")
                with open(os.path.join(master_directory, project_name, version, filename), "rb") as f:
                    sendhuge_secure(client, f.read(), encryption_key)
            if recved == b'loadall':
                version = recvhuge_secure(client, encryption_key).decode("utf-8")
                parent_dir = os.path.join(master_directory, project_name, version)
                sendhuge_secure(client, f"{len(os.listdir(parent_dir))}".encode("utf-8"), encryption_key)
                for filename in os.listdir(parent_dir):
                    abspath = os.path.join(parent_dir, filename)
                    sendhuge_secure(client, filename.encode("utf-8"), encryption_key)
                    with open(abspath, "rb") as f:
                        sendhuge_secure(client, f.read(), encryption_key)
            if recved == b"delv":
                version = recvhuge_secure(client, encryption_key).decode("utf-8")
                shutil.rmtree(os.path.join(master_directory, project_name, version))
            if recved == b"delf":
                version = recvhuge_secure(client, encryption_key).decode("utf-8")
                filename = recvhuge_secure(client, encryption_key).decode("utf-8")
                os.remove(os.path.join(master_directory, project_name, version, filename))
            if recved == b"delp":
                proj = recvhuge_secure(client, encryption_key).decode("utf-8")
                if proj == "versionControl":
                    continue
                shutil.rmtree(os.path.join(master_directory, proj))
            if recved == b"setproj":
                project_name = recvhuge_secure(client, encryption_key).decode("utf-8")
            if recved == b"getcwproj":
                sendhuge_secure(client, project_name.encode("utf-8"), encryption_key)
            if recved == b"tree":
                treestr = tree_dir(master_directory)
                sendhuge_secure(client, treestr.encode("utf-8"), encryption_key)
            if recved == b"listproj":
                treestr = tree_dir(os.path.join(master_directory, project_name))
                sendhuge_secure(client, treestr.encode("utf-8"), encryption_key)
            if recved == b"listprojs":
                projects = sorted(os.listdir(master_directory))
                sendhuge_secure(client, "\n".join(projects).encode("utf-8"), encryption_key)
            if recved == b"exit":
                raise BrokenPipeError()
            if recved == b'update':
                latest_version = find_latest(master_directory, "versionControl")
                with open(os.path.join(master_directory, "versionControl", latest_version, "client.py"), "rb") as f:
                    sendhuge_secure(client, f.read(), encryption_key)
            if recved == b'updateserver':
                latest_version = find_latest(master_directory, "versionControl")
                with open(os.path.join(master_directory, "versionControl", latest_version, "server.py"), "rb") as f:
                    content = f.read()
                with open(__file__, "wb") as f:
                    f.write(content)
            if recved == b'help':
                sendhuge_secure(client, f"available commands {list(available_commands.keys())}".encode("utf-8"), encryption_key)
            if recved == b'helpcmd':
                cmd = recvhuge_secure(client, encryption_key).decode("utf-8")
                if cmd not in available_commands:
                    sendhuge_secure(client, "not found".encode("utf-8"), encryption_key)
                    continue
                sendhuge_secure(client, available_commands[cmd].encode("utf-8"), encryption_key)
        except BrokenPipeError:
            log(f"{address} disconnected.")
            client.close()
            break

hashed_password = hashlib.sha256(b"").hexdigest()
encryption_key = b"0"
if os.path.exists("./.password"):
    with open("./.password", "r") as f:
        encryption_key = f.read().replace("\n", "").replace(" ", "").encode("utf-8")
        hashed_password = hashlib.sha256(encryption_key).hexdigest()
    log("password loaded")

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
ip = s.getsockname()[0]
s.close()
port = 62000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
log(f"binding server with {ip}:{port}")
server.bind((ip, port))
server.listen()

log(f"server running with ip: {ip} and port: {port}")

create_dir(master_directory)

available_commands = {
    "save":"upload a file to the server",
    "saveall":"upload files in a selected directory to the server",
    "load":"download a file from the server",
    "loadall":"download files from a selected version",
    "delv":"delete version",
    "delf":"delete file",
    "delp":"delete project",
    "setproj":"set current working project",
    "getcwproj":"get current working project",
    "tree":"trees all the projects",
    "listproj":"list files inside the current working project",
    "listprojs":"list all projects",
    "help":"displays all available commands",
    "helpcmd":"displays what a certain command does",
    "update":"downloads the latest client file",
    "updateserver":"updates the server to the latest version",
    "exit":"exit",
}

while True:
    client, address = server.accept()
    thread = threading.Thread(target=handle_client, args=(client, address))
    thread.start()
    log(f"{address} connected")
