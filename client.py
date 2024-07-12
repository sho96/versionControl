#1.2.2
import socket
import os
import sys
import time
import json
import hashlib
from math import ceil
from getpass import getpass
import pickle
import numpy as np
import colorama
from colorama import Fore, Style
from tqdm import tqdm
from enum import Enum

colorama.init()

config_file_path = os.path.join(os.getcwd(), ".versionControl")

class Colors(Enum):
    SUCCESS = Fore.LIGHTGREEN_EX
    FAILED = Fore.LIGHTRED_EX
    INFO = Fore.LIGHTMAGENTA_EX
    WARNING = Fore.LIGHTYELLOW_EX
    PROMPT = Fore.LIGHTBLUE_EX
    PROMPT_SUB = Fore.CYAN
    
PROGRESS_BAR_FORMAT = '{l_bar}{bar:20}{r_bar}'

def print_success(message):
    print(f"{Colors.SUCCESS.value}{Style.BRIGHT}{message}{Style.RESET_ALL}")

def print_failed(message):
    print(f"{Colors.FAILED.value}{Style.BRIGHT}{message}{Style.RESET_ALL}")

def print_info(message, bold=False):
    if bold:
        print(f"{Colors.INFO.value}{Style.BRIGHT}{message}{Style.RESET_ALL}")
    else:
        print(f"{Colors.INFO.value}{message}{Style.RESET_ALL}")

def input_prompt(message, sub=False):
    value = input(f"{Colors.PROMPT_SUB.value if sub else Colors.PROMPT.value}{Style.BRIGHT}{message}")
    print(Style.RESET_ALL, end="")
    return value

def input_files(message="enter path (leave blank to continue): ", not_found="File not found"):
    files = []
    cwd = os.getcwd()
    while True:
        print()
        print("selected files: ")
        for i, file in enumerate(files):
            print(f"    {i+1}. {file}")
        print()

        path = input_prompt(message, sub=True)
        if path == "":
            break
        if os.path.isabs(path):
            if not os.path.exists(path):
                print_warning(not_found)
                continue
        else:
            if not os.path.exists(os.path.join(cwd, path)):
                print_warning(not_found)
                continue
        files.append(path)

    return [os.path.abspath(path) for path in files]

def print_warning(message, bold=False):
    if bold:
        print(f"{Colors.WARNING.value}{Style.BRIGHT}{message}{Style.RESET_ALL}")
    else:
        print(f"{Colors.WARNING.value}{message}{Style.RESET_ALL}")

def print_colored(message, color, bold=False, end="\n"):
    print(f"{color}{Style.BRIGHT if bold else ''}{message}{Style.RESET_ALL}", end=end)

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

    if show_percentage:
        p_bar = tqdm(total=length, bar_format=PROGRESS_BAR_FORMAT, unit="B", unit_scale=True, unit_divisor=1024)
        for i in range(0, length, packet_size):
            raw_bytes = np.frombuffer(data[i: i+packet_size], dtype=np.uint8)
            if i + packet_size >= length:
                sending_bytes = raw_bytes + key_to_apply[:len(raw_bytes)]
            else:
                sending_bytes = raw_bytes + key_to_apply

            p_bar.update(len(sending_bytes))

            client.sendall(sending_bytes)
        p_bar.close()
    else:
        for i in range(0, length, packet_size):
            raw_bytes = np.frombuffer(data[i: i+packet_size], dtype=np.uint8)
            if i + packet_size >= length:
                sending_bytes = raw_bytes + key_to_apply[:len(raw_bytes)]
            else:
                sending_bytes = raw_bytes + key_to_apply
            client.sendall(sending_bytes)
    if show_percentage:
        print_success(f"sent {length} bytes")
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
    with tqdm(total=length, bar_format=PROGRESS_BAR_FORMAT, unit="B", unit_scale=True, unit_divisor=1024) as pbar:
        while True:
            packet = client.recv(length - total_length)
            file.write(packet)
            total_length += len(packet)
            
            pbar.n = total_length
            pbar.refresh()
            
            if total_length == length:
                break
    print_success(f"\rreceived {length} bytes in {time.perf_counter() - start_time:.3f}s\n")
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
    with tqdm(total=length, bar_format=PROGRESS_BAR_FORMAT, unit="B", unit_scale=True, unit_divisor=1024) as pbar:
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
                
                pbar.n = total_length
                pbar.refresh()

                if total_length == length:
                    break
    print_success(f"\rreceived {length} bytes in {time.perf_counter() - start_time:.3f}s")
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

ip = input_prompt("ip (leave blank for previous connection): ")
if ip == "":
    ip = load_config_values("ip")
    if ip == "not set":
        print_info("no previous connection found")
        sys.exit()
    port = load_config_values("port")
else:
    port = int(input_prompt("port: "))
ip = ip.replace("lan", "192.168")

print()

try:
    print(f"connecting to {ip}:{port}")
    client.connect((ip, port))
except socket.timeout:
    print_failed("no response")
    sys.exit()
client.settimeout(10)

localCommands = {
    "cd": " Change cwd",
    "mkdir": " Create directory",
    "ls": " List files in cwd",
    "getcwd": " Show current working directory",
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
    if authResult != "granted":
        print_failed("authentication failed")
        sys.exit()

cwd = os.getcwd()
cwproj = load_config_values("proj")

sendhuge_secure(client, b'setproj', encryption_key)
sendhuge_secure(client, cwproj.encode("utf-8"), encryption_key)
print()
print_success("---------- connected -----------")
print_success(f" server:  {ip}:{port}")
print_success(f" project: {cwproj}")
print()

while True:
    cmd = input_prompt(">> ")
    if cmd == "":
        continue
    sendhuge_secure(client, cmd.encode("utf-8"), encryption_key)
    if cmd == "save":
        version = input_prompt("version: ", sub=True)
        path = input_prompt("path: ", sub=True)
        if not os.path.isabs(path):
            path = os.path.join(cwd, path)
        filename = os.path.split(path)[1]
        sendhuge_secure(client, version.encode("utf-8"), encryption_key)
        sendhuge_secure(client, filename.encode("utf-8"), encryption_key)
        sendfile_secure(client, path, encryption_key)
    if cmd == "savechosen":
        version = input_prompt("version: ", sub=True)
        files = input_files()
        sendhuge_secure(client, version.encode("utf-8"), encryption_key)
        sendhuge_secure(client, f"{len(files)}".encode("utf-8"), encryption_key)
        for i, file in enumerate(files):
            print(f"sending... {i+1}/{len(files)} {file}")
            sendhuge_secure(client, f"{os.path.basename(file)}".encode("utf-8"), encryption_key)
            sendfile_secure(client, file, encryption_key)
            print()
        print_success(f"sent {len(files)} files")
    if cmd == "saveall":
        version = input_prompt("version: ", sub=True)
        directory = input_prompt("directory: ", sub=True)
        if directory == "":
            directory = cwd
        files = [file for file in os.listdir(directory) if os.path.isfile(os.path.join(directory, file))]
        sendhuge_secure(client, version.encode("utf-8"), encryption_key)
        sendhuge_secure(client, f"{len(files)}".encode("utf-8"), encryption_key)
        for i, file in enumerate(files):
            print(f"sending... {i+1}/{len(files)} {file}")
            sendhuge_secure(client, f"{file}".encode("utf-8"), encryption_key)
            sendfile_secure(client, os.path.join(directory, file), encryption_key)
            print()
        print_success(f"sent {len(files)} files")
    if cmd == "!save":
        version = input_prompt("version: ", sub=True)
        path = input_prompt("path: ", sub=True)
        if not os.path.isabs(path):
            path = os.path.join(cwd, path)
        filename = os.path.split(path)[1]
        sendhuge(client, version.encode("utf-8"))
        sendhuge(client, filename.encode("utf-8"))
        sendfile(client, path)
    if cmd == "!savechosen":
        version = input_prompt("version: ", sub=True)
        files = input_files()
        sendhuge(client, version.encode("utf-8"))
        sendhuge(client, f"{len(files)}".encode("utf-8"))
        for i, file in enumerate(files):
            print(f"sending... {i+1}/{len(files)} {file}")
            sendhuge(client, f"{os.path.basename(file)}".encode("utf-8"))
            sendfile(client, file)
            print()
        print_success(f"sent {len(files)} files")
    if cmd == "!saveall":
        version = input_prompt("version: ", sub=True)
        directory = input_prompt("directory: ", sub=True)
        if directory == "":
            directory = cwd
        files = [file for file in os.listdir(directory) if os.path.isfile(os.path.join(directory, file))]
        sendhuge(client, version.encode("utf-8"))
        sendhuge(client, f"{len(files)}".encode("utf-8"))
        for i, file in enumerate(files):
            print(f"sending... {i+1}/{len(files)} {file}")
            sendhuge(client, f"{file}".encode("utf-8"))
            sendfile(client, os.path.join(directory, file))
            print()
        print_success(f"sent {len(files)} files")
    if cmd == "load":
        version = input_prompt("version: ", sub=True)
        filename = input_prompt("filename: ", sub=True)
        sendhuge_secure(client, version.encode("utf-8"), encryption_key)
        sendhuge_secure(client, filename.encode("utf-8"), encryption_key)
        recvfile_secure(client, os.path.join(cwd, filename), encryption_key)
    if cmd == "loadall":
        version = input_prompt("version: ", sub=True)
        directory = input_prompt("directory: ", sub=True)
        if directory == "":
            directory = cwd
        sendhuge_secure(client, version.encode("utf-8"), encryption_key)
        numOfFiles = int(recvhuge_secure(client, encryption_key).decode("utf-8"))
        for i in range(numOfFiles):
            filename = recvhuge_secure(client, encryption_key).decode("utf-8")
            print(f"receiving {filename} ({i+1}/{numOfFiles})")
            recvfile_secure(client, os.path.join(cwd, filename), encryption_key)
            print()
        print_success(f"loaded {numOfFiles} files")
    if cmd == "!load":
        version = input_prompt("version: ", sub=True)
        filename = input_prompt("filename: ", sub=True)
        sendhuge(client, version.encode("utf-8"))
        sendhuge(client, filename.encode("utf-8"))
        recvfile(client, os.path.join(cwd, filename))
    if cmd == "!loadall":
        version = input_prompt("version: ", sub=True)
        directory = input_prompt("directory: ", sub=True)
        if directory == "":
            directory = cwd
        sendhuge(client, version.encode("utf-8"))
        numOfFiles = int(recvhuge(client).decode("utf-8"))
        for i in range(numOfFiles):
            filename = recvhuge(client).decode("utf-8")
            print(f"receiving... {filename} {i+1} / {numOfFiles}")
            recvfile(client, os.path.join(cwd, filename))
            print()
        print_success(f"loaded {numOfFiles} files")
    if cmd == "delf":
        version = input_prompt("version: ", sub=True)
        filename = input_prompt("filename: ", sub=True)
        sendhuge_secure(client, version.encode("utf-8"), encryption_key)
        sendhuge_secure(client, filename.encode("utf-8"), encryption_key)
    if cmd == "delv":
        version = input_prompt("version: ", sub=True)
        sendhuge_secure(client, version.encode("utf-8"), encryption_key)
    if cmd == "delp":
        projName = input_prompt("project name: ", sub=True)
        sendhuge_secure(client, projName.encode("utf-8"), encryption_key)
    if cmd == "setproj":
        projName = input_prompt("project name: ", sub=True)
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
        for element in sorted(os.listdir(cwd)):
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
        targetDir = input_prompt("cd to -> ", sub=True)
        if targetDir == "..":
            cwd = os.path.dirname(cwd)
            continue
        result = os.path.join(cwd, targetDir)
        if os.path.isdir(result):
            cwd = result
        else:
            print_failed("path does not exist")
    if cmd == "getcwproj":
        print(recvhuge_secure(client, encryption_key).decode("utf-8"))
    if cmd == "getcwd":
        print(cwd)
    if cmd == "mkdir":
        dirname = input_prompt("dirname: ", sub=True)
        if dirname in os.listdir(cwd):
            print_failed("the name already exists in the directory")
            continue
        os.mkdir(os.path.join(cwd, dirname))
    if cmd == "help":
        server_cmds = pickle.loads(recvhuge_secure(client, encryption_key))
        print_info("available server commands:")
        for cmd in server_cmds:
            print_info(f"    {cmd:<20}{server_cmds[cmd]}")
        print_info("available local commands:")
        for cmd in localCommands:
            print_info(f"    {cmd:<20}{localCommands[cmd]}")
    if cmd == "helpcmd":
        command = input_prompt("command: ", sub=True)
        sendhuge_secure(client, command.encode("utf-8"), encryption_key)
        help = recvhuge_secure(client, encryption_key).decode("utf-8")
        if help != "not found":
            print(help)
            continue
        if command not in localCommands:
            print_info("command not found")
            continue
        print(localCommands[command])
    if cmd == "update":
        recvfile_secure(client, __file__, encryption_key)
        print_info("updated")
        sendhuge_secure(client, "exit".encode("utf-8"), encryption_key)
        sys.exit()
    if cmd == "updateserver":
        (top_line, current_n_bytes), (latest_version, latest_n_bytes) = pickle.loads(recvhuge_secure(client, encryption_key))
        print_warning(f"update server?\nCurrent version: {top_line} {current_n_bytes}B\nFound latest version: {latest_version} {latest_n_bytes}B")
        sendhuge_secure(client, input_prompt("(y/n) -> ", sub=True).encode("utf-8"), encryption_key)
        print_info(recvhuge_secure(client, encryption_key).decode("utf-8"))
    if cmd == "exit":
        sys.exit()
        
    print()
