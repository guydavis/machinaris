# Changelog

All notable changes to this project will be documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.5] - 2021-09-? 

- Plotman - Avoid use of tty for container platforms such as TrueNAS to allow plotting without `-t` docker flag.
- Machinaris - Improved status reporting efficiency and better logging.

## [0.5.4] - 2021-08-31 

- Chia - Update to version 1.2.5.  See their [changelog for details](https://github.com/Chia-Network/chia-blockchain/releases/tag/1.2.5).
- Machinaris - Fix for Chia 1.2.4 SSL issue seen on plotter-only systems.
- Machinaris - Displayname for Workers tabs of Plotting and Farming pages.
- Machinaris - Fix for partials chart on Summary page.
- Machinaris - Fix for plotting log view.

## [0.5.3] - 2021-08-27

- Worker page for each worker shows Warnings for certain configuraton issues.
- Farming page now shows current disk usage for each drive (free and used)
- Plotting page now shows recent disk usage for each drive (free and used)
- Summary page now charts recent blockchain challenges and partial proofs
- Fixes from feedback received by users on the Machinaris Discord.  Thanks all!
- Chia - Update to version 1.2.4. See their [changelog for details](https://github.com/Chia-Network/chia-blockchain/releases/tag/1.2.4).

## [0.5.2] - 2021-08-13

- Machinaris - Docker images now available for [Apple M1](https://github.com/guydavis/machinaris/issues/43) and [Raspberry Pi OS](https://github.com/guydavis/machinaris/issues/155) architectures. 
- Chiadog - Update to new v0.7.0 to [support for parsing partials and solo blocks](https://github.com/martomi/chiadog/pull/268).
- Chia - Update to patch release of 1.2.3.  See their [changelog for details](https://github.com/Chia-Network/chia-blockchain/releases/tag/1.2.3).
- Flax - Update to version 0.1.1.  See their [changelog for details](https://github.com/Flax-Network/flax-blockchain/releases/tag/0.1.1).
- TrueNAS - Support for Machinaris deployment via helm chart. [Issue #78](https://github.com/guydavis/machinaris/issues/78) - Big thanks to @kmoore134 for this!
- Machinaris - Daily Farming Summary now available on Farming page for both Chia and Flax.  Add new plot type column.
- Machinaris - Pools - Show each Pool's status including link to your pool provider.  List pool point events on Summary page.
- Machinaris - Workers - Use hostname for Worker display name, even when using IP addresses behind the scenes. Also show versions. Automated harvester setup. 
- Machinaris - Connections page has link to test your router port forward for farming.
- Machinaris - New [public website](http://www.machinaris.app) with launch Wizard for generating first Docker run/compose of Machinaris.

## [0.5.1] - 2021-07-22

- Wizard on Workers page to create a Docker run/compose based on your settings. [Issue #97](https://github.com/guydavis/machinaris/issues/97)
- Latest Madmax plotter with support for n_buckets3 and n_rmulti2 settings in Plotman.
- Update to patch release of Chia 1.2.2, including a fix for harvester cache updates.  See their [changelog for details](https://github.com/Chia-Network/chia-blockchain/releases/tag/1.2.2).

## [0.5.0] - 2021-07-09

- Support for [official Chia pools](https://github.com/guydavis/machinaris/issues/131). Chia and Madmax plotters can create portable plots.
- Plotting and farming on the [Flax Network](https://github.com/guydavis/machinaris/issues/105). Enabled by default, but can be [disabled](https://github.com/guydavis/machinaris/wiki/Flax#optional-to-disable).


## [0.4.0] - 2021-06-25

- Support for [Madmax plotter](https://github.com/madMAx43v3r/chia-plotter), in addition to official [Chia plotter](https://github.com/Chia-Network/chia-blockchain).
- Manage multiple plotters, harvesters, and farmers across your LAN, all from a [single WebUI on one controller system](https://github.com/guydavis/machinaris/wiki/Workers).


## [0.3.2] - 2021-06-06

- Include the just released Chia 1.1.7. For details, see their [changelog](https://github.com/Chia-Network/chia-blockchain/blob/1.1.7/CHANGELOG.md#117-chia-blockchain-2021-06-05).

## [0.3.1] - 2021-06-04

- After testing showed between 15% to 30% speedup on plotting, adopting [Chiapos multithreaded library](https://github.com/guydavis/machinaris/wiki/Releases#chiapos).
- Thanks to `hereisderek` for a great PR containing better rsync support, SSH key import, and optional auto-plot on container restart.
- Include `paho-mqtt` library to support Chiadog alerts via MQTT by default.

## [0.3.0] - 2021-05-28

- Integrate the excellent Chiadog project for log monitoring and alerting
- Plotman Analyze output to show time spent in each plotting phase
- Log Viewer for Farming, Alerts, and Plotting including logs for running plot jobs
- Rebase off ubuntu:focal, include nice Dockerfile cleanup by sparklyballs 
- When mode=plotter, autoconfigure Plotman with provided farmer_pk and pool_pk
- When mode=harvester, auto import of your farmer's CA certificates

## [0.2.1] - 2021-05-21

- Dark mode CSS patch contributed by Hukuma1.  Looks great! Thanks for the help!
- Patch to latest Chia binaries version at 1.1.6.  Thanks to ChrisM! Nice solution!
- Fix broken 'Add Connection' button on Network | Connections page.

## [0.2] - 2021-05-20

- Improved key handling including generation (if needed) and supporting multiple keys.
- Now supports mounting multiple final plots folders for plotting and/or farming.
- Plotting page now has Plotman Stop action, along with Suspend/Resume/Kill actions for plots.

## [0.1] - 2021-05-15

- Basic integration of official Chia docker (v1.1.5) with Plotman (0.3.1) via a simple WebUI.
- NOTE: Due to versioning in the official docker, you'll see `chia version` report `v1.1.6dev0`
