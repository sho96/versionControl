#1.2.1
import socket
import os
import sys
import time
import json
import hashlib
from math import ceil
from getpass import getpass
import numpy as np
import pickle

config_file_path = os.path.join(os.getcwd(), ".versionControl")

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
            sending_bytes = raw_bytes + key_to_apply[:len(raw_bytes)]
        else:
            sending_bytes = raw_bytes + key_to_apply
        client.sendall(sending_bytes)
        if show_percentage:
            precentage = i/length*100
            print(f"\r{precentage:.3f} %", end="")
    if show_percentage:
        print("\r100 %")
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
        elif length - len(recved) < optimal_packet_size and len(client.recv(length - len(recved), socket.MSG_PEEK)) == length - len(recved):
            buffer = client.recv(length - len(recved))
            key_to_apply = (key * ceil(len(buffer) / key_length))[:len(buffer)]
            recved += (np.frombuffer(buffer, dtype=np.uint8) - np.frombuffer(key_to_apply, dtype=np.uint8)).tobytes()
        if len(recved) == length:
            break
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

    start_time = time.perf_counter()
    
    length = int(length)
    print(f"receiving {length} bytes")
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
    print(f"\rreceived {length} bytes in {time.perf_counter() - start_time:.3f}s\n")
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
                file.write((np.frombuffer(buffer, dtype=np.uint8) - np.frombuffer(key_to_apply, dtype=np.uint8)).tobytes())
            elif length - total_length < optimal_packet_size and len(client.recv(length - total_length, socket.MSG_PEEK)) == length - total_length:
                buffer = client.recv(length - total_length)
                total_length += len(buffer)
                key_to_apply = (key * ceil(len(buffer) / key_length))[:len(buffer)]
                file.write((np.frombuffer(buffer, dtype=np.uint8) - np.frombuffer(key_to_apply, dtype=np.uint8)).tobytes())
            if total_length == length:
                break
            precentage = total_length/length*100
            print(f"\r{precentage:.2f} %", end="")
    print(f"\rreceived {length} bytes in {time.perf_counter() - start_time:.3f}s")
    return length

def sendfile(client, path):
    with open(path, "rb") as f:
        sendhuge(client, f.read())

def sendfile_secure(client, path, key):
    with open(path, "rb") as f:
        sendhuge_secure(client, f.read(), key, show_percentage=True)

def update_config(key, value):
    with open(config_file_path, "r") as f:
        current_config = json.loads(f.read())
    with open(config_file_path, "w") as f:
        current_config[key] = value
        f.write(json.dumps(current_config))

def load_config_values(key):
    with open(config_file_path, "r") as f:
        current_config = json.loads(f.read())
    return current_config[key]

def create_config_file(path, default_values):
    if os.path.exists(path):
        return False
    with open(path, "w") as f:
        f.write(json.dumps(default_values))

create_config_file(config_file_path, {"proj": "versionControl", "ip": "not set", "port": 0})

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.settimeout(3)

ip = input("ip (leave blank for default): ")
if ip == "":
    ip = load_config_values("ip")
    if ip == "not set":
        print("default ip still not specified")
        sys.exit()
    port = load_config_values("port")
    
else:
    port = int(input("port: "))
ip = ip.replace("lan", "192.168")

try:
    client.connect((ip, port))
except socket.timeout:
    print(f"no response from {ip}:{port}")
    sys.exit()
client.settimeout(None)
cwd = os.getcwd()


localCommands = {
    "cd": " Change cwd ",
    "mkdir": " Create directory ",
    "ls": " List files in cwd ",
    "getcwd": " Show current working directory ",
}

update_config("ip", ip)
update_config("port", port)

hasAuth = recvhuge(client).decode("utf-8") == "auth"
encryption_key = b"0"
if hasAuth:
    print("this server requires password authentication")
    encryption_key = getpass().encode("utf-8")
    sendhuge(client, hashlib.sha256(encryption_key).hexdigest().encode("utf-8"))
    authResult = recvhuge(client).decode("utf-8")
    print(authResult)
    if authResult == "denied":
        sys.exit()

cwproj = load_config_values("proj")

sendhuge_secure(client, b'setproj', encryption_key)
sendhuge_secure(client, cwproj.encode("utf-8"), encryption_key)
print()
print("---------- connected -----------")
print(f" server:  {ip}:{port}")
print(f" project: {cwproj}")
print()

while True:
    cmd = input(">> ")
    if cmd == "":
        continue
    sendhuge_secure(client, cmd.encode("utf-8"), encryption_key)
    if cmd == "save":
        version = input("version: ")
        path = input("path: ")
        if not os.path.isabs(path):
            path = os.path.join(cwd, path)
        filename = os.path.split(path)[1]
        sendhuge_secure(client, version.encode("utf-8"), encryption_key)
        sendhuge_secure(client, filename.encode("utf-8"), encryption_key)
        sendfile_secure(client, path, encryption_key)
    if cmd == "saveall":
        version = input("version: ")
        directory = input("directory: ")
        if directory == "":
            directory = cwd
        files = [file for file in os.listdir(directory) if os.path.isfile(os.path.join(directory, file))]
        sendhuge_secure(client, version.encode("utf-8"), encryption_key)
        sendhuge_secure(client, f"{len(files)}".encode("utf-8"), encryption_key)
        for i, file in enumerate(files):
            print(f"sending... {file} {i+1} / {len(files)}")
            sendhuge_secure(client, f"{file}".encode("utf-8"), encryption_key)
            sendfile_secure(client, os.path.join(directory, file), encryption_key)
        print("sent")
    if cmd == "save!":
        version = input("version: ")
        path = input("path: ")
        if not os.path.isabs(path):
            path = os.path.join(cwd, path)
        filename = os.path.split(path)[1]
        sendhuge(client, version.encode("utf-8"))
        sendhuge(client, filename.encode("utf-8"))
        sendfile(client, path)
    if cmd == "saveall!":
        version = input("version: ")
        directory = input("directory: ")
        if directory == "":
            directory = cwd
        files = [file for file in os.listdir(directory) if os.path.isfile(os.path.join(directory, file))]
        sendhuge(client, version.encode("utf-8"))
        sendhuge(client, f"{len(files)}".encode("utf-8"))
        for i, file in enumerate(files):
            print(f"sending... {file} {i+1} / {len(files)}")
            sendhuge(client, f"{file}".encode("utf-8"))
            sendfile(client, os.path.join(directory, file))
        print("sent")
    if cmd == "load":
        version = input("version: ")
        filename = input("filename: ")
        sendhuge_secure(client, version.encode("utf-8"), encryption_key)
        sendhuge_secure(client, filename.encode("utf-8"), encryption_key)
        recvfile_secure(client, os.path.join(cwd, filename), encryption_key)
    if cmd == "loadall":
        version = input("version: ")
        directory = input("directory: ")
        if directory == "":
            directory = cwd
        sendhuge_secure(client, version.encode("utf-8"), encryption_key)
        numOfFiles = int(recvhuge_secure(client, encryption_key).decode("utf-8"))
        for i in range(numOfFiles):
            filename = recvhuge_secure(client, encryption_key).decode("utf-8")
            print(f"receiving... {filename} {i+1} / {numOfFiles}")
            recvfile_secure(client, os.path.join(cwd, filename), encryption_key)
            print()
    if cmd == "load!":
        version = input("version: ")
        filename = input("filename: ")
        sendhuge(client, version.encode("utf-8"))
        sendhuge(client, filename.encode("utf-8"))
        recvfile(client, os.path.join(cwd, filename))
    if cmd == "loadall!":
        version = input("version: ")
        directory = input("directory: ")
        if directory == "":
            directory = cwd
        sendhuge(client, version.encode("utf-8"))
        numOfFiles = int(recvhuge(client).decode("utf-8"))
        for i in range(numOfFiles):
            filename = recvhuge(client).decode("utf-8")
            print(f"receiving... {filename} {i+1} / {numOfFiles}")
            recvfile(client, os.path.join(cwd, filename))
            print()
    if cmd == "delf":
        version = input("version: ")
        filename = input("filename: ")
        sendhuge_secure(client, version.encode("utf-8"), encryption_key)
        sendhuge_secure(client, filename.encode("utf-8"), encryption_key)
    if cmd == "delv":
        version = input("version: ")
        sendhuge_secure(client, version.encode("utf-8"), encryption_key)
    if cmd == "delp":
        projName = input("project name: ")
        sendhuge_secure(client, projName.encode("utf-8"), encryption_key)
    if cmd == "setproj":
        projName = input("project name: ")
        sendhuge_secure(client, projName.encode("utf-8"), encryption_key)
        update_config("proj", projName)
    if cmd == "tree":
        print(recvhuge_secure(client, encryption_key).decode("utf-8"))
    if cmd == "listproj":
        print(recvhuge_secure(client, encryption_key).decode("utf-8"))
    if cmd == "listprojs":
        print(recvhuge_secure(client, encryption_key).decode("utf-8"))
    if cmd == "ls":
        print()
        dirs = []
        files = []
        for element in os.listdir(cwd):
            if os.path.isfile(os.path.join(cwd, element)):
                files.append(element)
            else:
                dirs.append(element)
        for dir in dirs:
            print(f"   -{dir}")
        for file in files:
            print(f"    {file}")
        print()
    if cmd == "cd":
        targetDir = input("cd to -> ")
        if targetDir == "..":
            cwd = os.path.dirname(cwd)
            continue
        result = os.path.join(cwd, targetDir)
        if os.path.isdir(result):
            cwd = result
        else:
            print("path does not exist")
    if cmd == "getcwproj":
        print(recvhuge_secure(client, encryption_key).decode("utf-8"))
    if cmd == "getcwd":
        print(cwd)
    if cmd == "mkdir":
        dirname = input("dirname: ")
        if dirname in os.listdir(cwd):
            print("the name already exists in the directory")
            continue
        os.mkdir(os.path.join(cwd, dirname))
    if cmd == "help":
        server_cmds = pickle.loads(recvhuge_secure(client, encryption_key))
        print("available server commands:")
        for cmd in server_cmds:
            print(f"    {cmd:<20}{server_cmds[cmd]}")
        print("available local commands:")
        for cmd in localCommands:
            print(f"    {cmd:<20}{localCommands[cmd]}")
    if cmd == "helpcmd":
        command = input("command: ")
        sendhuge_secure(client, command.encode("utf-8"), encryption_key)
        help = recvhuge_secure(client, encryption_key).decode("utf-8")
        if help != "not found":
            print(help)
            continue
        if command not in localCommands:
            print("command not found")
            continue
        print(localCommands[command])
    if cmd == "update":
        recvfile_secure(client, __file__, encryption_key)
        print("updated")
        sendhuge_secure(client, "exit".encode("utf-8"), encryption_key)
        sys.exit()
    if cmd == "updateserver":
        top_line, latest_version = pickle.loads(recvhuge_secure(client, encryption_key))
        print(f"update server?\nCurrent version: {top_line}Found latest version: {latest_version}")
        sendhuge_secure(client, input("(y/n) -> ").encode("utf-8"), encryption_key)
        print(recvhuge_secure(client, encryption_key).decode("utf-8"))
    if cmd == "exit":
        sys.exit()
