# Unraid Installation

[Unraid](https://unraid.net/) is a great solution to serve up both storage and applications throughout your house 24/7.  This combination makes it a particularly good choice to run the CHIA™ cryptocurrency network.

NOTE: *I have submitted Machinaris for inclusion in the Unraid Community Apps, but am still awaiting a response.*  Once that happens, you'll simply search for Machinaris under the *Apps* tab:

![](https://raw.githubusercontent.com/guydavis/machinaris-unraid/master/wiki/images/unraid-apps-tab.png)

For now however, to install Machinaris on Docker, one needs to add it to the Unraid *Docker* tab as described next.

## Migration from Official Docker

You can install Machinaris all by itself, but if you're already running the [official Docker](https://forums.unraid.net/topic/108203-support-partition-pixel-chia/), there is a quick way to copy the configuration over to Machinaris:

```
cp -r /mnt/user/appdata/chia /mnt/user/appdata/machinaris
```

## Manual Docker Creation on Unraid

Go to Unraid | Docker tab | Add Container and switch on Advanced View

```
Name: machinaris
Overview:  Building upon the official Chia docker image, this adds the Plotman CLI tool for concurrent plotting management and a WebUI for Unraid users.
Repository: ghcr.io/guydavis/machinaris
Docker Hub URL: https://hub.docker.com/repository/docker/guydavis/machinaris
Icon URL: https://raw.githubusercontent.com/guydavis/machinaris-unraid/master/machinaris.png
WebUI: http://[IP]:[PORT:5000]/
Extra Parameters: -t
Network Type: Host
```

```
Then create a Path named: appdata
Container Path: /root/.chia
Host Path: /mnt/user/appdata/machinaris

Create a Path named: plots
Container Path: /plots
Host Path: /mnt/user/data/PATH/TO/YOUR/PLOTS

Create a Path named: plotting
Container Path: /plotting
Host Path: /mnt/user/data/PATH/TO/YOUR/TEMP_PLOT_SPACE

Create a Port named: chia_rpc
Host Port: 8555
Connection Type: TCP

Create a Port named: chia_protocol
Host Port: 8444
Connection Type: TCP  

Create a Port named: web_ui
Host Port: 8926
Connection Type: TCP

Create a Variable named: keys
Key: keys
Value: /root/.chia/mnemonic.txt
```

# Post-Install Configuration

Once you have Machinaris installed on your Unraid, you should follow these generic post-install setup steps.

## Tips and Tricks

Please learn from my mistakes, regarding disks, shares, and hardware:

DO's:
* Use SSDs for your temporary plotting space.
* Use Unraid HDD array or unassigned HDD devices to store your completed plots. 

DON'T's:
* Don't use the Unraid HDD array for temporary plotting space.  This is super slow!

The project is still in beta, join the [Discord](https://discord.gg/mX4AtMTt87) for support and to help out.