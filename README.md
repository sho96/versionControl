## versionControl
A Github like system where you can upload and download files but with version specified

This project makes it easy for you to manage versions of your code and also
sharing the files with other computers


### Setup

1. get a computer that runs in your home 24-7 (it even runs smooth with raspberry pi zero w)
2. run server.py on the computer you prepared
3. Done!!

### How to use

1. run client.py
3. enter the ip of your home server and the specified port (the default is 54321) to connect to your home server
4. type "setproj" to set the current working project (the default curent working project is "versionControl")
5. use "save", "load", "saveall", "loadall" commands to upload and download files

* type "help" to see all available commands
* type "helpcmd" to see what a certain command does

* **recommended to add the directory containing client.py to the environment variable**

### Things you can do to fully utilize this system

* adding the directory containing client.py to the environment variable.
  - It makes it so that you can run client.py by just typing versionControl on your terminal on windows
(make sure to change the content of versionControl.bat depending on the environment of your computer)
* 