# machinaris

An easy-to-use, pure-Docker solution, for both plotting and farming the Chia™ cryptocurrency.  Currently in [*beta*](https://github.com/users/guydavis/packages/container/package/machinaris)!

![Home](https://raw.githubusercontent.com/guydavis/machinaris-unraid/master/docs/img/machinaris_home.png)

To get started with Machinaris, follow an install guide for your platform: [Windows](https://github.com/guydavis/machinaris/wiki/Windows), [Linux](https://github.com/guydavis/machinaris/wiki/Linux), [Macintosh](https://github.com/guydavis/machinaris/wiki/MacOS), [Unraid](https://github.com/guydavis/machinaris/wiki/Unraid), and [others](https://github.com/guydavis/machinaris/wiki/Docker).

## Plotting View

[Plotman](https://github.com/ericaltendorf/plotman) manages staggered/parallel plotting jobs, also exposed via the Machinaris web interface:

![Plotting](https://raw.githubusercontent.com/guydavis/machinaris-unraid/master/docs/img/machinaris_plotting.png)

## Farming View

Machinaris installs the [latest stable version](https://github.com/Chia-Network/chia-blockchain/wiki/INSTALL#ubuntudebian) and applies a [multithreading performance patch](https://github.com/xrobau/chiapos) for faster plotting.

![Farming](https://raw.githubusercontent.com/guydavis/machinaris-unraid/master/docs/img/machinaris_farming.png)

## Alerts

[Chiadog](https://github.com/martomi/chiadog) provides monitoring of the Chia™ log files, ensuring you get notified when important events occur on your system:

![Alerts](https://raw.githubusercontent.com/guydavis/machinaris-unraid/master/docs/img/ChiaDog-1-Example.png)

## Setup

Simplified setup allows you to either import your existing key mnemonic or generate a new one directly in the Machinaris WebUI on first launch:

![Setup](https://raw.githubusercontent.com/guydavis/machinaris-unraid/master/docs/img/machinaris_setup.png)

## Configuration

Configuration updates for Chia, Plotman, and Chiadog are available in the WebUI.  

![Connections](https://raw.githubusercontent.com/guydavis/machinaris-unraid/master/docs/img/machinaris_settings.png)

Details on Blockchain and Connection status as well:

![Connections](https://raw.githubusercontent.com/guydavis/machinaris-unraid/master/docs/img/machinaris_network.png)

## Container CLI

While the WebUI is useful for quick and easy access, you also have the full power of a shell commandline (CLI) in the running Machinaris container.  All binaries are available to execute advanced commands as shown below:

![ContainerCLI](https://raw.githubusercontent.com/guydavis/machinaris-unraid/master/docs/img/machinaris_container_cli.png)

## Worker Management

When Machinaris is [deployed to multiple systems](https://github.com/guydavis/machinaris/wiki/Workers) on your LAN, you can control each plotter, harvester, and farmer - all from a central WebUI on the Machinaris controller.  Configuration, monitoring, and alerting are all available in this centralized portal.

![Workers](https://raw.githubusercontent.com/guydavis/machinaris-unraid/master/docs/img/machinaris_workers.png)


## Trademark Notice
CHIA NETWORK INC, CHIA™, the CHIA BLOCKCHAIN™, the CHIA PROTOCOL™, CHIALISP™ and the “leaf Logo” (including the leaf logo alone when it refers to or indicates Chia), are trademarks or registered trademarks of Chia Network, Inc., a Delaware corporation. *There is no affliation between this Machinaris project and the main Chia Network project.*
