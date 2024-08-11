#1.2.3
import socket
import threading
import os
import shutil
import hashlib
from datetime import datetime
import numpy as np
import time
from math import ceil
import pickle

master_directory = "./projects/"

def sendhuge(client, data) -> None:
    length = len(data)
    client.send(f"{length}\n".encode("ascii"))
    client.sendall(data)


def sendhuge_secure(client, data, key, show_percentage=False) -> None:
    key_length = len(key)
    length = len(data)
    client.send(f"{length}\n".encode("ascii"))
    sending_bytes = b""
    packet_size = ceil((4096 - key_length * 2) / key_length) * key_length
    
    key_to_apply = np.frombuffer((key * ceil(length / key_length))[:packet_size], dtype=np.uint8)
    for i in range(0, length, packet_size):
        raw_bytes = np.frombuffer(data[i: i+packet_size], dtype=np.uint8)
        if i + packet_size >= length:
            sending_bytes = raw_bytes ^ key_to_apply[:len(raw_bytes)]
        else:
            sending_bytes = raw_bytes ^ key_to_apply
        client.sendall(sending_bytes)
        if show_percentage:
            precentage = i/length*100
            print(f"\r{precentage:.2f} %", end="")
    if show_percentage:
        print("\r100 %")

def log(message):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")
    
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
    print("\r100 %")
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
            recved += (np.frombuffer(buffer, dtype=np.uint8) ^ np.frombuffer(key_to_apply, dtype=np.uint8)).tobytes()
        elif length - len(recved) < optimal_packet_size and len(client.recv(length - len(recved), socket.MSG_PEEK)) == length - len(recved):
            buffer = client.recv(length - len(recved))
            key_to_apply = (key * ceil(len(buffer) / key_length))[:len(buffer)]
            recved += (np.frombuffer(buffer, dtype=np.uint8) ^ np.frombuffer(key_to_apply, dtype=np.uint8)).tobytes()
        if len(recved) == length:
            break
        precentage = len(recved)/length*100
        print(f"\r{precentage} %", end="")
    print("\r100 %")
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
        print(f"\r{precentage:.2f} %", end="")
    print("\r100 %")
    return length

def recvfile_secure(client, path, key) -> int:
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
    print(f"receiving {length} bytes")
    start_time = time.perf_counter()
    key_length = len(key)
    buffer = b""
    optimal_packet_size = ceil((4096 - key_length * 2) / key_length) * key_length
    total_length = 0
    with open(path, "wb") as file:
        while True:
            #print(f"length: {length} total: {total_length}", end="\r")
            if len(client.recv(length - total_length, socket.MSG_PEEK)) >= optimal_packet_size:
                buffer = client.recv(optimal_packet_size)
                total_length += len(buffer)
                key_to_apply = key * (len(buffer) // key_length)
                file.write((np.frombuffer(buffer, dtype=np.uint8) ^ np.frombuffer(key_to_apply, dtype=np.uint8)).tobytes())
            elif length - total_length < optimal_packet_size and len(client.recv(length - total_length, socket.MSG_PEEK)) == length - total_length:
                buffer = client.recv(length - total_length)
                total_length += len(buffer)
                key_to_apply = (key * ceil(len(buffer) / key_length))[:len(buffer)]
                file.write((np.frombuffer(buffer, dtype=np.uint8) ^ np.frombuffer(key_to_apply, dtype=np.uint8)).tobytes())
            if total_length == length:
                break
            precentage = total_length/length*100
            print(f"\r{precentage:.2f} %", end="")
    print(f"\r100 % in {round(time.perf_counter() - start_time, 3)}s\n")
    return length

def sendfile(client, path) -> None:
    length = os.path.getsize(path)
    client.send(f"{length}\n".encode("ascii"))
    with open(path, "rb") as f:
        while True:
            data = f.read(4096)
            if not data:
                break
            client.sendall(data)

def sendfile_secure(client, path, key, show_percentage=False) -> None:
    key_length = len(key)
    length = os.path.getsize(path)
    client.send(f"{length}\n".encode("ascii"))
    sending_bytes = b""
    packet_size = ceil((4096 - key_length * 2) / key_length) * key_length
    
    key_to_apply = np.frombuffer((key * ceil(length / key_length))[:packet_size], dtype=np.uint8)
    with open(path, "rb") as f:
        for i in range(0, length, packet_size):
            data = f.read(packet_size)
            raw_bytes = np.frombuffer(data, dtype=np.uint8)
            if i + packet_size >= length:
                sending_bytes = raw_bytes ^ key_to_apply[:len(raw_bytes)]
            else:
                sending_bytes = raw_bytes ^ key_to_apply
            client.sendall(sending_bytes)
            if show_percentage:
                precentage = i/length*100
                print(f"\r{precentage:.2f} %", end="")
    if show_percentage:
        print("\r100 %")
def tree_dir(path) -> str:
    result = ""
    tab = "    "
    for root, dirs, files in os.walk(path):
        level = root.replace(path, '').count(os.sep)
        result += f"{tab * level}{'-'+os.path.basename(root)}\n"
        for f in sorted(files):
            result += f"{tab * (level+1)}{f}\n"
    return result

def tree_dir_ordered(path, level=0, show_top_dir=False) -> str:
    result = ""
    tab = "    "
    if not os.path.exists(path):
        return ""
    if show_top_dir:
        result += f"{tab * level}-{os.path.basename(path)}\n"
        level += 1
    all_pathes = sorted(os.listdir(path))
    dirs = [name for name in all_pathes if os.path.isdir(os.path.join(path, name))]
    files = [name for name in all_pathes if os.path.isfile(os.path.join(path, name))]
    for d in dirs:
        result += f"{tab * level}-{d}\n"
        result += tree_dir_ordered(os.path.join(path, d), level+1)
    for f in files:
        result += f"{tab * level} {f}\n"
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

def prevent_path_injection(path) -> str:
    parts = path.split(os.sep)
    symbols_to_avoid = ("..", "~", ".", "*", "**")
    parts = [part for part in parts if part not in symbols_to_avoid]
    return (os.sep).join(parts)


def handle_client(client, address):
    if hashed_password != hashlib.sha256(b"\x00").hexdigest():
        sendhuge(client, b"auth")
        try:
            log(f"waiting for password auth for client: {address}")
            received_hashed_password = recvhuge(client).decode("utf-8")
        except ValueError as e:
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
            except ValueError as e:
                log(f"unknown format encountered with client: {address}")
                print(e)
                client.close()
                raise BrokenPipeError()
            
            log(f"{address}: {recved}")
            if recved == b'':
                raise BrokenPipeError()
            if recved == b"save":
                version = recvhuge_secure(client, encryption_key).decode("utf-8")
                filename = recvhuge_secure(client, encryption_key).decode("utf-8")
                create_sets(master_directory, project_name, version)
                recvfile_secure(client, prevent_path_injection(os.path.join(master_directory, project_name, version, filename)), encryption_key)
            if recved == b"saveall" or recved == b"savechosen":
                version = recvhuge_secure(client, encryption_key).decode("utf-8")
                n_files = int(recvhuge_secure(client, encryption_key).decode("utf-8"))
                for _ in range(n_files):
                    filename = recvhuge_secure(client, encryption_key).decode("utf-8")
                    create_sets(master_directory, project_name, version)
                    recvfile_secure(client, prevent_path_injection(os.path.join(master_directory, project_name, version, filename)), encryption_key)
            if recved == b"!save":
                version = recvhuge(client).decode("utf-8")
                filename = recvhuge(client).decode("utf-8")
                create_sets(master_directory, project_name, version)
                recvfile(client, prevent_path_injection(os.path.join(master_directory, project_name, version, filename)))
            if recved == b"!saveall" or recved == b"!savechosen":
                version = recvhuge(client).decode("utf-8")
                n_files = int(recvhuge(client).decode("utf-8"))
                for _ in range(n_files):
                    filename = recvhuge(client).decode("utf-8")
                    create_sets(master_directory, project_name, version)
                    recvfile(client, prevent_path_injection(os.path.join(master_directory, project_name, version, filename)))
            if recved == b"load":
                version = recvhuge_secure(client, encryption_key).decode("utf-8")
                filename = recvhuge_secure(client, encryption_key).decode("utf-8")
                abs_path = prevent_path_injection(os.path.join(master_directory, project_name, version, filename))
                sendfile_secure(client, abs_path, encryption_key, True)
            if recved == b'loadall':
                version = recvhuge_secure(client, encryption_key).decode("utf-8")
                parent_dir = prevent_path_injection(os.path.join(master_directory, project_name, version))
                sendhuge_secure(client, f"{len(os.listdir(parent_dir))}".encode("utf-8"), encryption_key)
                for filename in os.listdir(parent_dir):
                    abs_path = prevent_path_injection(os.path.join(parent_dir, filename))
                    sendhuge_secure(client, filename.encode("utf-8"), encryption_key)
                    sendfile_secure(client, abs_path, encryption_key, True)
            if recved == b"!load":
                version = recvhuge(client).decode("utf-8")
                filename = recvhuge(client).decode("utf-8")
                abs_path = prevent_path_injection(os.path.join(master_directory, project_name, version, filename))
                sendfile(client, abs_path)
            if recved == b'!loadall':
                version = recvhuge(client).decode("utf-8")
                parent_dir = prevent_path_injection(os.path.join(master_directory, project_name, version))
                sendhuge(client, f"{len(os.listdir(parent_dir))}".encode("utf-8"))
                for filename in os.listdir(parent_dir):
                    abs_path = prevent_path_injection(os.path.join(parent_dir, filename))
                    sendhuge(client, filename.encode("utf-8"))
                    sendfile(client, abs_path)
            if recved == b"delv":
                version = recvhuge_secure(client, encryption_key).decode("utf-8")
                shutil.rmtree(prevent_path_injection(os.path.join(master_directory, project_name, version)))
            if recved == b"delf":
                version = recvhuge_secure(client, encryption_key).decode("utf-8")
                filename = recvhuge_secure(client, encryption_key).decode("utf-8")
                os.remove(prevent_path_injection(os.path.join(master_directory, project_name, version, filename)))
            if recved == b"delp":
                proj = recvhuge_secure(client, encryption_key).decode("utf-8")
                if proj == "versionControl":
                    continue
                shutil.rmtree(prevent_path_injection(os.path.join(master_directory, proj)))
            if recved == b"setproj":
                project_name = recvhuge_secure(client, encryption_key).decode("utf-8")
            if recved == b"getcwproj":
                sendhuge_secure(client, project_name.encode("utf-8"), encryption_key)
            if recved == b"tree":
                treestr = tree_dir_ordered(master_directory)
                sendhuge_secure(client, treestr.encode("utf-8"), encryption_key)
            if recved == b"listproj":
                treestr = tree_dir_ordered(prevent_path_injection(os.path.join(master_directory, project_name)), show_top_dir=True)
                sendhuge_secure(client, treestr.encode("utf-8"), encryption_key)
            if recved == b"listprojs":
                projects = sorted(os.listdir(master_directory))
                sendhuge_secure(client, "\n".join(projects).encode("utf-8"), encryption_key)
            if recved == b"exit":
                raise BrokenPipeError()
            if recved == b'update':
                latest_version = find_latest(master_directory, "versionControl")
                abs_path = os.path.join(master_directory, "versionControl", latest_version, "client.py")
                sendfile_secure(client, abs_path, encryption_key)
            if recved == b'updateserver':
                latest_version = find_latest(master_directory, "versionControl")
                with open(os.path.join(master_directory, "versionControl", latest_version, "server.py"), "rb") as f:
                    content = f.read()
                found_n_bytes = len(content)
                with open(__file__, "rb") as f:
                    content = f.read()
                top_line = content.decode("utf-8").split("\n")[0]
                current_n_bytes = len(content)
                sendhuge_secure(client, pickle.dumps(((top_line, current_n_bytes), (latest_version, found_n_bytes))), encryption_key)
                if recvhuge_secure(client, encryption_key).decode("utf-8") == "y":
                    with open(os.path.join(master_directory, "versionControl", latest_version, "server.py"), "rb") as f:
                        content = f.read()
                    with open(__file__, "wb") as f:
                        f.write(content)
                    sendhuge_secure(client, "updated".encode("utf-8"), encryption_key)
                else:
                    sendhuge_secure(client, "not updated".encode("utf-8"), encryption_key)
            if recved == b'help':
                sendhuge_secure(client, pickle.dumps(available_commands), encryption_key)
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

hashed_password = hashlib.sha256(b"\x00").hexdigest()
encryption_key = b"\x00"
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
    "save": " Upload a file to the server ",
    "savechosen": "Upload selected files to the server",
    "saveall": " Upload all files in the cwd to the server ",
    "load": " Download a file from the server ",
    "loadall": " Download files from a selected version to cwd ",
    "!save": " fast but insecure version of `save` ",
    "!savechosen": " fast but insecure version of `savechosen` ",
    "!saveall": " fast but insecure version of `saveall` ",
    "!load": " fast but insecure version of `load` ",
    "!loadall": " fast but insecure version of `loadall` ",
    "setproj": " Set the current working project ",
    "exit": " Exit ",
    "delv": " Delete version in the current project ",
    "delf": " Delete file in the current project ",
    "delp": " Delete project with project name specified ",
    "listproj": " Show project tree ",
    "listprojs": " Show all projects ",
    "tree": " Show the entire tree ",
    "getcwproj": " Show the current working project ",
    "help": " List all commands ",
    "helpcmd": " See what the provided command does ",
    "update": " Download and update client.py file ",
    "updateserver": " Update the server to the latest version ",
}

while True:
    client, address = server.accept()
    thread = threading.Thread(target=handle_client, args=(client, address))
    thread.start()
    log(f"{address} connected")
