# Version Control
<ul>
  <li><h3>Save your project on your home server 🗄️</h3></li>
  <li><h3>Share files among computers 🔗</h3></li>
  <li><h3>Port-foward to access your files from anywhere 🌐</h3></li>
</ul>

## Setup
1. Get your home server that runs 24/7 (comfirmed to work on Raspberry Pi) <br>
2. Install numpy on your server with ```pip install numpy``` and make sure the version is over 1.20.0
2. Run ```server.py```<br>
3. Done!! 🚀<br>

## How to use
1. Install dependencies by ```pip install -r client_requirements.txt``` (this will install all dependencies written in requirements.txt)<br>
  Or manually install with ```pip install numpy tqdm colorama```. Make sure numpy version is over 1.20.0
2. Run ```client.py``` on your computer (not your server)
3. Follow the prompted instructions to login to the server
4. You can now enter commands! 🎉

Basic Commands: 
| Command | Description |
| --- | --- |
| `save` | Upload a file to the server |
| `savechosen` | Upload selected files to the server |
| `saveall` | Upload all files in the cwd to the server |
| `load` | Download a file from the server |
| `loadall` | Download files from a selected version to cwd |
| `listproj` | Show project tree |
| `setproj` | Set the current working project |
| `cd` | Change cwd |
| `exit` | Exit |

See below for list of all available commands


## Fully utilize Version Control
⚙️ Adding ```client.py``` to the environment variable 
  - This will make running ```client.py``` on the terminal much easier<br>
  I've prepared a snippet: ```versionControl.bat```(Windows), ```versionControl.sh```(Mac & Linux). <br>
  Edit the file accordingly to your environment
  - Add the path of the directory containing ```versionControl.bat``` to the environment variable<br>
  - > See [here](https://www.twilio.com/en-us/blog/how-to-set-environment-variables-html) for detailed instructions

🔐 Adding the file named ```.password``` to the directory containing ```server.py```
  - Store the password inside ```.password``` and put it in the same directory as ```server.py```.
  - This will make the server password locked. **Strongly recommended when exposing the server to the internet**

🌐 Port-fowarding your server to the internet
  - This will make the server accessible from the internet
  - The name of the setting may differ depending on your router. <br>
  Common setting names are: "Port fowarding", "Port mapping", "Punch through", etc...<br>
  - > See [here](https://www.lifewire.com/how-to-port-forward-4163829) for detailed instructions

## List of commands 
<span style="color: gray">You can also see this list with the ```help``` command</span>

| Command | Description |
| --- | --- |
| | 
| Save & Load |
| `save` | Upload a file to the server |
| `savechosen` | Upload selected files to the server |
| `saveall` | Upload all files in the cwd to the server |
| `load` | Download a file from the server |
| `loadall` | Download files from a selected version to cwd |
| `!save` | fast but insecure version of `save` |
| `!savechosen` | fast but insecure version of `savechosen` |
| `!saveall` | fast but insecure version of `saveall` |
| `!load` | fast but insecure version of `load` |
| `!loadall` | fast but insecure version of `loadall` |
| | 
| Others |
| `setproj` | Set the current working project |
| `exit` | Exit |
| `delv` | Delete version in the current project |
| `delf` | Delete file in the current project |
| `delp` | Delete project with project name specified |
| `listproj` | Show project tree |
| `listprojs` | Show all projects |
| `tree` | Show the entire tree |
| `getcwproj` | Show the current working project |
| `help` | List all commands |
| `helpcmd` | See what the provided command does |
| | 
| `cd` | Change cwd |
| `mkdir` | Create directory |
| `ls` | List files in cwd |
| `getcwd` | Show current working directory |
| | 
| Use if you want |  
| `update` | Download & Update ```client.py``` to the latest version |
| `updateserver` | Update the server to the latest version |