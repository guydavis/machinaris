# Changelog

All notable changes to this project will be documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
