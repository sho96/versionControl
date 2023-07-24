#1.0.10
import socket
import os
import sys
import time

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
    print(f"\r100.0 %  in {round(endTime - startTime, 3)}s")
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
    print(f"\r100.0 %  in {round(endTime-startTime, 3)}s")
    return length

def sendfile(client, path):
    with open(path, "rb") as f:
        sendhuge(client, f.read())

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ip, port = input("ip: "), int(input("port: "))
client.connect((ip, port))

cwd = os.getcwd()

localCommands = ["list", "changecwd", "cd", "getcwd"]

sendhuge(client, b'setproj')
sendhuge(client, b'versionControl')

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
            print(f"sending... {i+1} / {len(files)}")
            sendhuge(client, f"{file}".encode("utf-8"))
            sendfile(client, os.path.join(directory, file))

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
            print(f"recving... {i+1} / {numOfFiles}")
            filename = recvhuge(client).decode("utf-8")
            recvfile(client, os.path.join(cwd, filename))
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
    if cmd == "tree":
        print(recvhuge(client).decode("utf-8"))
    if cmd == "changecwd":
        cwd = input("cwd: ")
        if not os.path.exists(cwd):
            print("path does not exist")
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
    if cmd == "help":
        print(recvhuge(client).decode("utf-8"))
        print(f"available local commands: {localCommands}")
    if cmd == "update":
        recvfile(client, __file__)
    if cmd == "exit":
        sys.exit()