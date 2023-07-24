#1.0.9
import socket
import threading
import os
import shutil

masterdirectory = "/home/pi/Desktop/versionControl/projects/";

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

def treeDir(path) -> str:
    result = ""
    tab = "    "
    for root, dirs, files in os.walk(path):
        level = root.replace(path, '').count(os.sep)
        result += f"{tab * level}{'-'+os.path.basename(root)}\n"
        for f in files:
            result += f"{tab * (level+1)}{f}\n"
    return result

def createDir(path):
    try:
        os.mkdir(path)
    except FileExistsError:
        return True
    return False

def createSets(master, proj, ver):
    createDir(os.path.join(master, proj))
    createDir(os.path.join(os.path.join(master, proj), ver))

def findLatest(master, proj):
    return sorted(os.listdir(os.path.join(master, proj)))[-1]

def handleClient(client, address):
    projName = ""
    while True:
        try:
            recved = recvhuge(client)
            print(recved)
            if recved == b'':
                raise BrokenPipeError()
            if recved == b"save":
                version = recvhuge(client).decode("utf-8")
                filename = recvhuge(client).decode("utf-8")
                createSets(masterdirectory, projName, version)
                recvfile(client, os.path.join(masterdirectory, projName, version, filename))
            if recved == b"saveall":
                version = recvhuge(client).decode("utf-8")
                numOfFiles = int(recvhuge(client).decode("utf-8"))
                for i in range(numOfFiles):
                    filename = recvhuge(client).decode("utf-8")
                    createSets(masterdirectory, projName, version)
                    recvfile(client, os.path.join(masterdirectory, projName, version, filename))
            if recved == b"load":
                version = recvhuge(client).decode("utf-8")
                filename = recvhuge(client).decode("utf-8")
                with open(os.path.join(masterdirectory, projName, version, filename), "rb") as f:
                    sendhuge(client, f.read())
            if recved == b'loadall':
                version = recvhuge(client).decode("utf-8")
                parentDir = os.path.join(masterdirectory, projName, version)
                sendhuge(client, f"{len(os.listdir(parentDir))}".encode("utf-8"))
                for filename in os.listdir(parentDir):
                    abspath = os.path.join(parentDir, filename)
                    sendhuge(client, filename.encode("utf-8"))
                    with open(abspath, "rb") as f:
                        sendhuge(client, f.read())
            if recved == b"delv":
                version = recvhuge(client).decode("utf-8")
                shutil.rmtree(os.path.join(masterdirectory, projName, version))
            if recved == b"delf":
                version = recvhuge(client).decode("utf-8")
                filename = recvhuge(client).decode("utf-8")
                os.remove(os.path.join(masterdirectory, projName, version, filename))
            if recved == b"delp":
                proj = recvhuge(client).decode("utf-8")
                shutil.rmtree(os.path.join(masterdirectory, proj))
            if recved == b"setproj":
                projName = recvhuge(client).decode("utf-8")
            if recved == b"getcwproj":
                sendhuge(client, projName.encode("utf-8"))
            if recved == b"tree":
                treestr = treeDir(masterdirectory)
                sendhuge(client, treestr.encode("utf-8"))
            if recved == b"exit":
                raise BrokenPipeError()
            if recved == b'update':
                latestVersion = findLatest(masterdirectory, "versionControl")
                with open(os.path.join(masterdirectory, "versionControl", latestVersion, "client.py"), "rb") as f:
                    sendhuge(client, f.read())
            if recved == b'updateserver':
                latestVersion = findLatest(masterdirectory, "versionControl")
                with open(os.path.join(masterdirectory, "versionControl", latestVersion, "server.py"), "rb") as f:
                    content = f.read()
                with open(__file__, "wb") as f:
                    f.write(content)
            if recved == b'help':
                sendhuge(client, f"available commands {availableCommands}".encode("utf-8"))
        except BrokenPipeError:
            print(address, "disconnected.")
            client.close()
            break
        
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ip, port = f'192.168.{input("ip: 192.168.")}', int(input("port: "))
server.bind((ip, port))
server.listen()

print(f"server running with ip: {ip} and port: {port}")

availableCommands = [
    "save",
    "saveall",
    "load",
    "loadall",
    "delv",
    "delf",
    "delp",
    "setproj",
    "getcwproj",
    "tree",
    "help",
    "update",
    "updateserver",
    "exit"
]

while True:
    client, address = server.accept()
    thread = threading.Thread(target=handleClient, args=(client, address))
    thread.start()
    print(address, "connected")
