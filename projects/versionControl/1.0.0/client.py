import socket
import os

masterdirectory = "./projects/";

def sendhuge(client, data) -> None:
    length = len(data)
    client.send(f"{length}\n".encode("ascii"))
    client.sendall(data)

def recvhuge(client) -> bytes:
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
        precentage = totalLength/length*100
        print(f"\r{precentage} %", end="")
    print(f"\r100 %")
    return length

def sendfile(client, path):
    with open(path, "rb") as f:
        sendhuge(client, f.read())

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ip, port = "192.168." + input("ip: 192.168."), int(input("port: "))
client.connect((ip, port))

cwd = os.getcwd()

while True:
    cmd = input(">> ")
    sendhuge(client, cmd.encode("utf-8"))
    if cmd == "save":
        version = input("version: ")
        path = input("path: ")
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        filename = os.path.split(path)[1]
        sendhuge(client, version.encode("utf-8"))
        sendhuge(client, filename.encode("utf-8"))
        sendfile(client, path)
    if cmd == "load":
        version = input("version: ")
        filename = input("filename: ")
        sendhuge(client, version.encode("utf-8"))
        sendhuge(client, filename.encode("utf-8"))
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