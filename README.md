# machinaris

A Docker image for plotting and farming the Chia™ cryptocurrency on [one computer](https://github.com/guydavis/machinaris/wiki/Docker) or across [many](https://github.com/guydavis/machinaris/wiki/Workers).  Try the easy install using the [Launch Wizard](https://machinaris.app).

![Home](https://raw.githubusercontent.com/guydavis/machinaris-unraid/master/docs/img/machinaris_home.png)

For details, see your particular platform: [Windows](https://github.com/guydavis/machinaris/wiki/Windows), [Linux](https://github.com/guydavis/machinaris/wiki/Linux), [Macintosh](https://github.com/guydavis/machinaris/wiki/MacOS), [Unraid](https://github.com/guydavis/machinaris/wiki/Unraid), [Synology](https://github.com/guydavis/machinaris/wiki/Synology) and [others](https://github.com/guydavis/machinaris/wiki/Docker).  *For support, start a [Discussion](https://github.com/guydavis/machinaris/discussions) or join our [Discord](https://discord.gg/mX4AtMTt87)*.

## Plotting View

Plotting with the [MadMax](https://github.com/guydavis/machinaris/wiki/Madmax)/[Gigahorse](https://github.com/guydavis/machinaris/wiki/Gigahorse) and [Bladebit](https://github.com/guydavis/machinaris/wiki/Bladebit) plotters, with optional GPU, is managed by [Plotman](https://github.com/guydavis/machinaris/wiki/Plotman) through the Machinaris WebUI across many machines:

![Plotting](https://raw.githubusercontent.com/guydavis/machinaris-unraid/master/docs/img/machinaris_plotting.png)

Track your plotter machines performance as you fine-tune your plotting, graphed for each k-size you plot.

![Speed](https://raw.githubusercontent.com/guydavis/machinaris-unraid/master/docs/img/plotting_speed_chart.png)

Archive your new plots to their final destination on local drives or on remote harvesters (via rsync):

![Transfers](https://raw.githubusercontent.com/guydavis/machinaris-unraid/master/docs/img/archiving_transfers.png)

## Farming View

Machinaris bundles the [latest Chia™ version](https://github.com/Chia-Network/chia-blockchain/wiki/INSTALL#ubuntudebian) inside the Docker image.

![Farming](https://raw.githubusercontent.com/guydavis/machinaris-unraid/master/docs/img/machinaris_farming.png)

Machinaris also optionally farms your plots to other blockchains including [BPX](https://github.com/guydavis/machinaris/wiki/BPX), [Chives](https://github.com/guydavis/machinaris/wiki/Chives), [Ecostake](https://github.com/guydavis/machinaris/wiki/Ecostake), [Flax](https://github.com/guydavis/machinaris/wiki/Flax), [HDDCoin](https://github.com/guydavis/machinaris/wiki/HDDCoin), [MMX](https://github.com/guydavis/machinaris/wiki/MMX), and [many others](https://github.com/guydavis/machinaris/wiki/Forks).

## Alerts

[Chiadog](https://github.com/guydavis/machinaris/wiki/ChiaDog) provides monitoring of the log files, ensuring you get notified when important events occur across your farm:

![Alerts](https://raw.githubusercontent.com/guydavis/machinaris-unraid/master/docs/img/ChiaDog-1-Example.png)

[Drive health](https://github.com/guydavis/machinaris/wiki/Drives) is monitored as with `smartctl` on Linux. Notifications can be sent to e-mail, telegram, discord, slack, etc.

![Drives](https://raw.githubusercontent.com/guydavis/machinaris-unraid/master/docs/img/drives_grid.png)

## Setup

Simplified setup allows you to either import your existing key mnemonic or generate a new one directly in the Machinaris WebUI on first launch:

![Setup](https://raw.githubusercontent.com/guydavis/machinaris-unraid/master/docs/img/machinaris_setup.png)

That's for fullnode (default) and farmer modes. However, for [harvester](https://github.com/guydavis/machinaris/wiki/Docker#harvester-only) you only need the farmer's CA certificates and for [plotter](https://github.com/guydavis/machinaris/wiki/Docker#plotter-only) only your pool and farmer public keys.

Immediately on setup, a [fast blockchain download](https://github.com/guydavis/machinaris/wiki/Keys#blockchain-initialization) will get you synced and farming in just hours, rather than the days required by the official GUI client.

## Configuration

Configuration updating for Chia, Plotman, and Chiadog directly from the WebUI.  

![Settings](https://raw.githubusercontent.com/guydavis/machinaris-unraid/master/docs/img/machinaris_settings.png)

Summary and details for connections and blockchains highlights your farm's status:

![Connections](https://raw.githubusercontent.com/guydavis/machinaris-unraid/master/docs/img/geolocation.png)

## Container CLI

While the WebUI is useful for quick and easy access, you also have the full power of a shell commandline (CLI) in the running Machinaris container.  All binaries are available to execute advanced commands:

![ContainerCLI](https://raw.githubusercontent.com/guydavis/machinaris-unraid/master/docs/img/machinaris_container_cli.png)

To enter an in-container shell, just type `docker exec -it machinaris bash` from the host OS.

## Worker Management

When Machinaris is [deployed to multiple systems](https://github.com/guydavis/machinaris/wiki/Workers) on your LAN, you can control each plotter, harvester, and farmer - all from a central WebUI on the Machinaris controller.  Configuration, monitoring, and alerting are all available in this centralized portal.

![Workers](https://raw.githubusercontent.com/guydavis/machinaris-unraid/master/docs/img/machinaris_workers.png)

Each worker will run one Machinaris container per blockchain: Chia, Flax, MMX, etc as a fullnode, harvester, or plotter.

## REST API

Machinaris includes a complete [REST API](api/machinaris.postman_collection.json) offering opportunities for integration and extension with other tools.

![Workers](https://raw.githubusercontent.com/guydavis/machinaris-unraid/master/docs/img/machinaris_api.png)

All project [contributions](.github/CONTRIBUTING.md) and [feedback](https://github.com/guydavis/machinaris/discussions) are welcomed!  

## Trademark Notice
CHIA NETWORK INC, CHIA™, the CHIA BLOCKCHAIN™, the CHIA PROTOCOL™, CHIALISP™ and the “leaf Logo” (including the leaf logo alone when it refers to or indicates Chia), are trademarks or registered trademarks of Chia Network, Inc., a Delaware corporation. *There is no affliation between this Machinaris project and the main Chia Network project.*
