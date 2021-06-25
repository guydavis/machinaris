# machinaris

A Docker image for plotting and farming the Chia™ cryptocurrency on [one computer](https://github.com/guydavis/machinaris/wiki/Docker) or across [many](https://github.com/guydavis/machinaris/wiki/Workers).

![Home](https://raw.githubusercontent.com/guydavis/machinaris-unraid/master/docs/img/machinaris_home.png)

To get started with Machinaris, follow an install guide for your platform: [Windows](https://github.com/guydavis/machinaris/wiki/Windows), [Linux](https://github.com/guydavis/machinaris/wiki/Linux), [Macintosh](https://github.com/guydavis/machinaris/wiki/MacOS), [Unraid](https://github.com/guydavis/machinaris/wiki/Unraid), and [others](https://github.com/guydavis/machinaris/wiki/Docker).

## Plotting View

Plotting with both [MadMax](https://github.com/madMAx43v3r/chia-plotter) and [Chia™](https://github.com/Chia-Network/chia-blockchain) plotters is managed by [Plotman](https://github.com/ericaltendorf/plotman) through the Machinaris WebUI.

![Plotting](https://raw.githubusercontent.com/guydavis/machinaris-unraid/master/docs/img/machinaris_plotting.png)

## Farming View

Machinaris bundles the [latest Chia™ version](https://github.com/Chia-Network/chia-blockchain/wiki/INSTALL#ubuntudebian) inside the Docker image.

![Farming](https://raw.githubusercontent.com/guydavis/machinaris-unraid/master/docs/img/machinaris_farming.png)

## Alerts

[Chiadog](https://github.com/martomi/chiadog) provides monitoring of the log files, ensuring you get notified when important events occur across your farm:

![Alerts](https://raw.githubusercontent.com/guydavis/machinaris-unraid/master/docs/img/ChiaDog-1-Example.png)

## Setup

Simplified setup allows you to either import your existing key mnemonic or generate a new one directly in the Machinaris WebUI on first launch:

![Setup](https://raw.githubusercontent.com/guydavis/machinaris-unraid/master/docs/img/machinaris_setup.png)

That's for fullnode (default) and farmer modes. However, for [harvester](https://github.com/guydavis/machinaris/wiki/Docker#harvester-only) you only need the farmer's CA certificates and for [plotter](https://github.com/guydavis/machinaris/wiki/Docker#plotter-only) only your pool and farmer public keys.

## Configuration

Configuration updates for Chia, Plotman, and Chiadog are available in the WebUI.  

![Connections](https://raw.githubusercontent.com/guydavis/machinaris-unraid/master/docs/img/machinaris_settings.png)

Details on Blockchain and Connection status as well:

![Connections](https://raw.githubusercontent.com/guydavis/machinaris-unraid/master/docs/img/machinaris_network.png)

## Container CLI

While the WebUI is useful for quick and easy access, you also have the full power of a shell commandline (CLI) in the running Machinaris container.  All binaries are available to execute advanced commands:

![ContainerCLI](https://raw.githubusercontent.com/guydavis/machinaris-unraid/master/docs/img/machinaris_container_cli.png)

To enter an in-container shell, just type `docker exec -it machinaris bash` from the host OS.

## Worker Management

When Machinaris is [deployed to multiple systems](https://github.com/guydavis/machinaris/wiki/Workers) on your LAN, you can control each plotter, harvester, and farmer - all from a central WebUI on the Machinaris controller.  Configuration, monitoring, and alerting are all available in this centralized portal.

![Workers](https://raw.githubusercontent.com/guydavis/machinaris-unraid/master/docs/img/machinaris_workers.png)


## REST API

Machinaris includes a complete [REST API](api/machinaris.postman_collection.json) offering opportunities for integration and extension with other tools.

![Workers](https://raw.githubusercontent.com/guydavis/machinaris-unraid/master/docs/img/machinaris_api.png)

All project [contributions](.github/CONTRIBUTING.md) and [feedback](https://github.com/guydavis/machinaris/discussions) are welcomed!  

## Trademark Notice
CHIA NETWORK INC, CHIA™, the CHIA BLOCKCHAIN™, the CHIA PROTOCOL™, CHIALISP™ and the “leaf Logo” (including the leaf logo alone when it refers to or indicates Chia), are trademarks or registered trademarks of Chia Network, Inc., a Delaware corporation. *There is no affliation between this Machinaris project and the main Chia Network project.*
