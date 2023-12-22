#1.1.3
import socket
import os
import sys
import time
import json
import hashlib
from getpass import getpass

settingsPath = os.path.join(os.getcwd(), ".versionControl")

def sendhuge(client, data) -> None:
    length = len(data)
    client.send(f"{length}\n".encode("ascii"))
    client.sendall(data)

def recvhuge(client) -> bytes:
    startTime = time.perf_counter()
    length = b""
    while True:
        if client.recv(1, socket.MSG_PEEK) == 0:
            continue
        recved = client.recv(1)
        if recved == b'\n':
            break
        length += recved
    length = int(length)
    recved = b''
    while True:
        recved += client.recv(length - len(recved))
        if len(recved) == length:
            break
        precentage = len(recved)/(length/100)
        print(f"\r{round(precentage, 1)} %", end="")
    endTime = time.perf_counter()
    print(f"\r100.0 % in {round(endTime - startTime, 3)}s")
    return recved

def recvfile(client, path) -> int:
    startTime = time.perf_counter()
    length = b""
    while True:
        if client.recv(1, socket.MSG_PEEK) == 0:
            continue
        recved = client.recv(1)
        if recved == b'\n':
            break
        length += recved
    length = int(length)
    print(f"receiving {length} bytes")
    file = open(path, "wb")
    totalLength = 0
    while True:
        packet = client.recv(length - totalLength)
        file.write(packet)
        totalLength += len(packet)
        if totalLength == length:
            break
        precentage = totalLength/(length/100)
        print(f"\r{round(precentage, 1)} %", end="")
    endTime = time.perf_counter()
    print(f"\r100.0 % in {round(endTime-startTime, 3)}s")
    return length

def sendfile(client, path):
    with open(path, "rb") as f:
        sendhuge(client, f.read())

def updateSettings(key, value):
    with open(settingsPath, "r") as f:
        currentSettings = json.loads(f.read())
    with open(settingsPath, "w") as f:
        currentSettings[key] = value
        f.write(json.dumps(currentSettings))

def loadSettingValue(key):
    with open(settingsPath, "r") as f:
        currentSettings = json.loads(f.read())
    return currentSettings[key]

def createSettingsFile(path, defaultValues):
    if os.path.exists(path):
        return False
    with open(path, "w") as f:
        f.write(json.dumps(defaultValues))

createSettingsFile(settingsPath, {"proj": "versionControl", "ip": "not set", "port": 0})

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.settimeout(3)

ip = input("ip (leave blank for default): ")
if ip == "":
    ip = loadSettingValue("ip")
    if ip == "not set":
        print("default ip still not specified")
        sys.exit()
    port = loadSettingValue("port")
    
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
    "list":"list files and folders in current working dire1ctory", 
    "cd":"change directory", 
    "getcwd":"get current working directory", 
    "mkdir":"make directory",
}

updateSettings("ip", ip)
updateSettings("port", port)

hasAuth = recvhuge(client).decode("utf-8") == "auth"
if hasAuth:
    print("this server requires password authentication")
    sendhuge(client, hashlib.sha256(getpass().encode("utf-8")).hexdigest().encode("utf-8"))
    authResult = recvhuge(client).decode("utf-8")
    print(authResult)
    if authResult == "denied":
        sys.exit()

cwproj = loadSettingValue("proj")

sendhuge(client, b'setproj')
sendhuge(client, cwproj.encode("utf-8"))
print()
print("---------- connected -----------")
print(f" server:  {ip}:{port}")
print(f" project: {cwproj}")
print()

while True:
    cmd = input(">> ")
    sendhuge(client, cmd.encode("utf-8"))
    if cmd == "save":
        version = input("version: ")
        path = input("path: ")
        if not os.path.isabs(path):
            path = os.path.join(cwd, path)
        filename = os.path.split(path)[1]
        sendhuge(client, version.encode("utf-8"))
        sendhuge(client, filename.encode("utf-8"))
        sendfile(client, path)
    if cmd == "saveall":
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
        sendhuge(client, version.encode("utf-8"))
        sendhuge(client, filename.encode("utf-8"))
        recvfile(client, os.path.join(cwd, filename))
    if cmd == "loadall":
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
        sendhuge(client, version.encode("utf-8"))
        sendhuge(client, filename.encode("utf-8"))
    if cmd == "delv":
        version = input("version: ")
        sendhuge(client, version.encode("utf-8"))
    if cmd == "delp":
        projName = input("project name: ")
        sendhuge(client, projName.encode("utf-8"))
    if cmd == "setproj":
        projName = input("project name: ")
        sendhuge(client, projName.encode("utf-8"))
        updateSettings("proj", projName)
    if cmd == "tree":
        print(recvhuge(client).decode("utf-8"))
    if cmd == "listproj":
        print(recvhuge(client).decode("utf-8"))
    if cmd == "listprojs":
        print(recvhuge(client).decode("utf-8"))
    if cmd == "list":
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
        print(recvhuge(client).decode("utf-8"))
    if cmd == "getcwd":
        print(cwd)
    if cmd == "mkdir":
        dirname = input("dirname: ")
        if dirname in os.listdir(cwd):
            print("the name already exists in the directory")
            continue
        os.mkdir(os.path.join(cwd, dirname))
    if cmd == "help":
        print(recvhuge(client).decode("utf-8"))
        print(f"available local commands: {list(localCommands.keys())}")
    if cmd == "helpcmd":
        command = input("command: ")
        sendhuge(client, command.encode("utf-8"))
        help = recvhuge(client).decode("utf-8")
        if help != "not found":
            print(help)
            continue
        if not command in localCommands:
            print("command not found")
            continue
        print(localCommands[command])
    if cmd == "update":
        recvfile(client, __file__)
        print("updated")
        sendhuge(client, "exit".encode("utf-8"))
        sys.exit()
    if cmd == "exit":
        sys.exit()
