#1.1.0
import socket
import threading
import os
import shutil

masterdirectory = "./projects/"

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

def findMaxLength(arr):
    a = []
    for elem in arr:
        a.append(len(elem))
    return max(a)
def findMaxInColumn(arr, column):
    a = []
    for elem in arr:
        if len(elem) <= column:
            continue
        a.append(elem[column])
    return max(a)
def findLatest(master, proj):
    separated = []
    for version in os.listdir(os.path.join(master, proj)):
       if not version.replace(".", "").isdigit():
           continue
       separated.append([int(elem) for elem in version.split(".")])
    chosen = separated
    for i in range(findMaxLength(separated)):
        if findMaxLength(chosen) <= i:
            continue
        maximum = findMaxInColumn(chosen, i)
        left = []
        for elem in chosen:
            if len(elem) <= i:
                left.append(elem)
                continue
            if elem[i] == maximum:
                left.append(elem)
        chosen = list(left)
    return ".".join([str(char) for char in chosen[0]])


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
            if recved == b"listproj":
                treestr = treeDir(os.path.join(masterdirectory, projName))
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
                sendhuge(client, f"available commands {list(availableCommands.keys())}".encode("utf-8"))
            if recved == b'helpcmd':
                cmd = recvhuge(client).decode("utf-8")
                if not cmd in availableCommands:
                    sendhuge(client, "not found".encode("utf-8"))
                    continue
                sendhuge(client, availableCommands[cmd].encode("utf-8"))
        except BrokenPipeError:
            print(address, "disconnected.")
            client.close()
            break

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
ip = s.getsockname()[0]
print(ip)
s.close()
port = int(input("port: "))

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print(f"binding server with {ip}:{port}")
server.bind((ip, port))
server.listen()

print(f"server running with ip: {ip} and port: {port}")

availableCommands = {
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
    "help":"displays all available commands",
    "helpcmd":"displays what a certain command does",
    "update":"downloads the latest client file",
    "updateserver":"updates the server to the latest version",
    "exit":"exit",
}

while True:
    client, address = server.accept()
    thread = threading.Thread(target=handleClient, args=(client, address))
    thread.start()
    print(address, "connected")
