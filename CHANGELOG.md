# Changelog

All notable changes to this project will be documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.8.5] - 2022-11-?
### Added
 - Wallets page - Claim Rewards button offers portable plot reward recovery after one week has elapsed. (EARLY BETA!)
 - Chart memory usage per container (GiB) as well as total host memory usage (%) for OS and all apps.
 - Enhanced Forktools to optionally decrease a blockchain's full_node process count, which greatly limits memory usage.
 - Improve Plotting page to display configured tmp, dst, and archiving directories before starting to plot. Support `site_path_filter` for archive folders under `site_root`.
  - Bladebit support for new `ramplot` mode (needs 416 GB RAM) 
### Changed
 - Enhance 'NFT Reward Recovery' tool to support v2 databases. 
 - Fixes for invalid Chiadog harvester alerts. 
 - Fixes for bladebit `diskplot` mode (less than 416 GB RAM, needs 400+GB of tmp disk) 
### Updated
 - [Chia](https://github.com/Chia-Network/chia-blockchain/releases/tag/1.6.1) to v1.6.1
 - [Chinilla](https://github.com/Chinilla/chinilla-blockchain/releases/tag/1.3.0 to v1.3.0
 - [Littlelambocoin](https://github.com/BTCgreen-Network/littlelambocoin-blockchain/releases/tag/1.6.1) to v1.6.1
 - [Maize](https://github.com/Maize-Network/maize-blockchain/releases/tag/1.6.0) to v1.6.0
 - [MMX](https://github.com/madMAx43v3r/mmx-node) to `testnet8`.
### Known Issues
 - Incorrect reward recovery calculations for some blockchains.  Please use AllTheBlocks site if this affects you.
 - Chia CLI broke `chia plots check`, affecting new plots on Farming page.  Still investigating...

## [0.8.4] - 2022-09-21
- Scaling-Down: Optional mode where wallets are synced daily, not run 24/7.  Saves ~35% memory so smaller farmers can farm more blockchains concurrently on the same machine. See Wallets page, top-right Settings.
- Scaling-Up: Improved plot tracking efficiency for multi-PB sized farms. Thanks @grobalt!
- Warnings for duplicated, invalid, or key-less plots.  See Farming page.
- Update: [Flax](https://github.com/Flax-Network/flax-blockchain) to v0.1.10, [Cactus](https://github.com/Cactus-Network/cactus-blockchain) to v1.5.2, [Chia](https://github.com/Chia-Network/chia-blockchain/releases/tag/1.6.0) to v1.6.0
- Security: Disable Setup page's mnemonic import field autocomplete from caching value in your local browser. Thanks @Baatezu!
- Fixes: Better handling of farmed block logging for certain blockchains like Apple & BPX, Alerts from Chia 1.5.1 for added coins missing due to blockchain logging changes.  Improved Smartctl response processing.

## [0.8.3] - 2022-08-23
 - Additional blockchain pricing from Vayamos and Posat exchanges on the Blockchains, Wallets, and Summary pages.
 - New blockchains: [Apple](https://github.com/Apple-Network/apple-blockchain), [Chinilla](https://github.com/chinilla/chinilla-blockchain), [Gold](https://github.com/goldcoin-gl/gold-blockchain), [LittleLamboCoin](https://github.com/BTCgreen-Network/littlelambocoin-blockchain), [Mint](https://github.com/MintNetwork/mint-blockchain), [Tad](https://github.com/BTCgreen-Network/tad-blockchain), [Wheat](https://github.com/wheatnetwork/wheat-blockchain)
 - Update: [BPX](https://github.com/bpx-network/bpx-blockchain) to v2.0.0, [BTCGreen](https://github.com/BTCgreen-Network/btcgreen-blockchain) to v1.5.0, [Maize](https://github.com/Maize-Network/maize-blockchain) to v1.5.0, [Petroleum](https://github.com/petroleum-network/petroleum-blockchain) to v1.0.16, [Shibgreen](https://github.com/BTCgreen-Network/shibgreen-blockchain) to v1.5.0
 - Update:  [Chia](https://github.com/Chia-Network/chia-blockchain/releases/tag/1.5.1) - v1.5.1, [Bladebit](https://github.com/Chia-Network/bladebit/tree/2.0.0-beta1) to v2.0.0 (beta-1) with diskplot mode (beta only in `:develop` and `:test` images)
 - Fixes: Avoid timeout/slowness encountered by those with many drives, also many cold wallet transactions

## [0.8.2] - 2022-07-24
 - MMX - Record created blocks from blockchain logs, for display in Machinaris, off index page.
 - Ubuntu - latest blockchains run on Jammy Jellyfish (Python 3.10), outdated blockchains run on Focal Fossa (Python 3.9).
 - Updated: [Cactus](https://github.com/Cactus-Network/cactus-blockchain/releases/tag/1.4.1) to fix SSL certificate expiry, may require entire deletion of `mainnet` directory and full re-sync.  Check [their Discord](https://discord.gg/2Q8RcVacWP) for latest support of this blockchain.
 - [Chia](https://github.com/Chia-Network/chia-blockchain/releases/tag/1.5.0) - v1.5.0, patched into Machinaris v0.8.2 next day.

## [0.8.1] - 2022-07-17
 - Connections - add node peers directly from list offered by AllTheBlocks per blockchain.
 - MMX - Compute "Estimated Time to Win" from plots size, netspace size, and blocks per day.
 - New blockchains: [BPX](https://github.com/bpx-network/bpx-blockchain), [Ecostake](https://github.com/Ecostake-Network/ecostake-blockchain), [Petroleum](https://github.com/Petroleum-Network/petroleum-blockchain), and [Profit](https://github.com/ProfitCrypto/profit-blockchain)
 - Updated: [Cactus](https://github.com/Cactus-Network/cactus-blockchain/releases/tag/1.4.0), [Chiadog](https://github.com/martomi/chiadog/releases/tag/v0.7.2)

## [0.8.0] - 2022-06-30
 - Charting of each blockchain's netspace, farmed coins, and wallet balances over the past month.
 - Tracking farmed blocks sent directly to cold wallet. Set your cold wallet addresses on the Wallets page.
 - Added a read-only transactions viewer for each blockchain's wallet, available from Wallets page.  
 - Alerts: per-notifier [allow setting](https://github.com/guydavis/machinaris/wiki/ChiaDog#ignore-alerts) to allow only selected alerts, based on criteria.
 - [Chia](https://github.com/Chia-Network/chia-blockchain/releases/tag/1.4.0) - v1.4.0, after a month of pre-release testing with Machinaris.
 - [Cactus](https://github.com/Cactus-Network/cactus-blockchain) - v1.3.4, matches Chia 1.3.4, please run: `cactus db upgrade`
 - [Chives](https://github.com/HiveProject2021/chives-blockchain) - v1.3.1, please run: `chives db upgrade`
 - [Cryptodoge](https://github.com/CryptoDoge-Network/cryptodoge) - v1.3.4, matches Chia 1.3.4, please run: `cryptodoge db upgrade`
 - [Flax](https://github.com/Flax-Network/flax-blockchain) - v0.1.9, matches Chia 1.4.0, please run: `flax db upgrade` if you haven't yet
 - [MMX](https://github.com/madMAx43v3r/mmx-node) - updated version for their `testnet6` network.

## [0.7.2] - 2022-05-17
 - Drives monitoring page - allow [overrides of smartctl commands](https://github.com/guydavis/machinaris/wiki/Drives#override-command) for special hardware. Drive failure alerts thru our enhanced Chiadog.
 - Alerts: per-notifier [ignore setting](https://github.com/guydavis/machinaris/wiki/ChiaDog#ignore-alerts) to prevent unwanted alerts, based on criteria.
 - German translations of the Machinaris WebUI by @ApfelBirneKreis.  Big thanks!
 - [Chia](https://github.com/Chia-Network/chia-blockchain/releases/tag/1.3.3) - v1.3.3 release, various minor bug fixes
 - [Chia](https://github.com/Chia-Network/chia-blockchain/releases/tag/1.3.4) - v1.3.4 release, upgrade fullnode before harvesters
 - [Chia](https://github.com/Chia-Network/chia-blockchain/releases/tag/1.3.5) - v1.3.5 release, fixes `chia version` number offset
 - [Staicoin](https://github.com/STATION-I/stai-blockchain) - v1.2 release - careful, bugs reported on their Discord!

## [0.7.1] - 2022-04-02
 - Drive monitoring using Smartctl (WebUI status currently, alerting to come soon)
 - Dutch translations (nl_NL) provided by Bernie Deprez.  Thanks!
 - Updates to various fork blockchains and tools including BTCGreen, Flax, HDDCoin, Madmax, MMX and Shibgreen
 - [Chia](https://github.com/Chia-Network/chia-blockchain/releases/tag/1.3.1) - v1.3.1 release
 - [Chia](https://github.com/Chia-Network/chia-blockchain/releases/tag/1.3.2) - v1.3.2 release

## [0.7.0] - 2022-03-11
 - [Chia](https://chia.net) - [v1.3](https://www.reddit.com/r/chia/comments/t95vuk/13_is_live/), please note reports of issues in this new Chia release...  double-check your Wallet and Pools settings after upgrading!
 - [Internationalization](https://github.com/guydavis/machinaris/wiki/Localization) for locale-specific text, numbers, and currencies.  Huge thanks to @antcasq (pt_PT) and @fabriziocacicia (it_IT) for providing translations!
 - Geolocation of peer connections for each blockchain by their IP address. [Optionally enabled](https://github.com/guydavis/machinaris/wiki/Connections) using a free Maxmind account.
 - [Flax](https://github.com/Flax-Network/flax-blockchain) - updated to v0.1.6, supporting new v2 DB format.
 - [HDDCoin](https://github.com/HDDcoin-Network/hddcoin-blockchain/releases) - update to version 2.0.2
 - [Silicoin](https://github.com/silicoin-network/silicoin-blockchain) - v1.2.2, supported again as per Discord votes.

## [0.6.9] - 2022-02-04
 - [MMX](https://github.com/madMAx43v3r/mmx-node) - support for this new blockchain, which requires its own plot files.
 - [HDDCoin](https://github.com/HDDcoin-Network/hddcoin-blockchain/releases) - update to version 2.0.0
 - Improved summary display for status.  Estimated price in USD provided by alltheblocks.net
 - Various fixes for issues reported in the Discord.  Thanks to all who reported!

## [0.6.8] - 2022-01-04
 - [SHIBGreen](https://github.com/BTCgreen-Network/shibgreen-blockchain) - cross-farming support for this blockchain fork.
 - Support for pooling configuration of forks like Chives.
 - Updated blockchains: Chives, Stor, Stai(coin)
 - Various fixes for issues reported in the Discord.  Thanks all!

## [0.6.7] - 2021-12-03
 - [BTCGreen](https://github.com/BTCgreen-Network/btcgreen-blockchain) - cross-farming support for this blockchain fork.
 - Plotting page - Charts to show plotting speed for recent jobs across all workers on your farm.
 - Option to disable background job to Chia `plots check` and Plotman `analyze`. Set `plots_check_analyze_skip` env var.
 - Fix for Madmax building on certain user's hardware.  Thanks @karaliux for the patch!
 - Fix to ensure Forktool's configs (~/.machinaris*/forktools/ftconfigs/) are persistent across container restarts.
 - Fix to quiet logrotate output from container stdout.  Too verbose.
 - Fix to incorrect commenting out of `pool_contract_address` on plotter systems. Please double-check your Settings | Plotting page!  Check Farming | Plots page for recent 'solo' plots.
 - Fix to Plotting | Workers page for graph showing tmp disk usage during plotting on mode=plotter systems.
 - Fix Farming | Workers page to show Daily Summaries for TrueNAS users with FQDN hostnames in their containers.
 - Fix - Blockchain download for fresh installs, use the new download paths provided by Maize team.

## [0.6.6] - 2021-11-28
 - [Maize](https://github.com/Maize-Network/maize-blockchain) - cross-farming support for this blockchain fork.
 - [Forktools](https://github.com/Qwinn1/forktools) - utilities including a multiproc patch to limit memory usage.
 - Farming - right-side of Plots table offers Chia "plots check", slowly generated on background thread.
 - Bug Fix - hourly log rotation for `farmr`, auto-deletion log if above 20 MB in size.  Sorry all!

## [0.6.5] - 2021-11-19
 - [Cryptodoge](https://github.com/CryptoDoge-Network/cryptodoge) - cross-farming support for this blockchain fork.
 - Docker images now roughly 1/3 the size of previous releases.  Shared base image further decreases download size for forks.
 - API endpoint /metrics/prometheus exposes plotting statistics.  Thanks to @Nold360 for the contribution!
 - Windows deployments now support automatically mounting remote plot shares (such as on a NAS) using CIFS in-container.
 - On Wallets page, display total wallet balance including cold wallet address amounts.

## [0.6.4] - 2021-11-12
 - [Farmr](https://github.com/gilnobrega/farmr) - include `farmr` client for optional monitoring at [farmr.net](https://farmr.net/)
 - [Stor](https://github.com/Stor-Network/stor-blockchain) - cross-farming support for this blockchain fork.
 - [Cactus](https://github.com/Cactus-Network/cactus-blockchain) - cross-farming support for this blockchain fork. 

## [0.6.3] - 2021-11-05
 - [Staicoin](https://github.com/STATION-I/staicoin-blockchain) - cross-farming support for this blockchain fork.
 - Chia - Update to version 1.2.11.  See their [changelog for details](https://github.com/Chia-Network/chia-blockchain/releases/tag/1.2.11).

## [0.6.2] - 2021-10-29
 - [Silicoin](https://github.com/silicoin-network/silicoin-blockchain) - cross-farming support for this blockchain fork.
 - [fd-cli](https://github.com/Flora-Network/flora-dev-cli) - Daily scheduled 7/8 coin win recovery for those farming NFT plots on other blockchains.
 - [Madmax](https://github.com/madMAx43v3r/chia-plotter/commit/8332d625220b9a54c097d85d6eb4c6b0c9464214) - support for plotting k33 and k34 plot sizes.
 - Machinaris - correctly show daily difference tooltips on Summary page statistics for all blockchains

## [0.6.1] - 2021-10-23
 - [Flora](https://github.com/Flora-Network/flora-blockchain) - cross-farming support for this blockchain fork.
 - ChiaDog - improved support for forks, fix coin symbol in certain alerts, Chives decimal placement, etc.
 - Machinaris - correctly report Chives plots from harvesters in the WebUI.  Plots were farmed, but hidden from WebUI before.
 - Machinaris - fix error in Setup - Mnemonic Import wizard.
 - Machinaris - re-enable the Plotman Archving start/stop buttons.

## [0.6.0] - 2021-10-18

 - [NChain](https://gitee.com/ext9/ext9-blockchain) - cross-farming support for this blockchain fork.
 - [HDDCoin](https://github.com/HDDcoin-Network/hddcoin-blockchain) - cross-farming support for this blockchain fork.
 - [Chives](https://github.com/HiveProject2021/chives-blockchain) - support for this blockchain fork.
 - [Flax](https://github.com/Flax-Network/flax-blockchain) - now farmed in a separtate Docker container.
 - [Plotman](https://github.com/ericaltendorf/plotman/pull/937) - enhancement to support plotting for Chives via Madmax.
 - [Chiadog](https://github.com/martomi/chiadog/pull/302) - enhancement to support monitoring of other blockchain forks.

## [0.5.7] - 2021-10-02 
 - Chia - Update to version 1.2.8.  See their [changelog for details](https://github.com/Chia-Network/chia-blockchain/releases/tag/1.2.8).
 - Bladebit - Update to version 1.2.0.  See their [changelog for details](https://github.com/harold-b/bladebit/releases/tag/1.2.0)
 - Chia - Update to version 1.2.9.  See their [changelog for details](https://github.com/Chia-Network/chia-blockchain/releases/tag/1.2.9).

## [0.5.6] - 2021-09-17 

 - Machinaris - On RaspPi, allow configurable status update frequency when running a Machinaris fullnode/controller.
 - Machinaris - Fix for launching harvesters on RaspPi devices, avoids missing bladebit error.
 - Machinaris - "Disconnect Selected" feature now available on Network | Connections page.
 - Machinaris - Improve Summary page to better separate Chia and Flax blockchains.
 - Chia - Update to version 1.2.7.  See their [changelog for details](https://github.com/Chia-Network/chia-blockchain/releases/tag/1.2.7).
 - Flax - Update to version 0.1.2.  See their [changelog for details](https://github.com/Flax-Network/flax-blockchain/releases/tag/0.1.2).
 - Bladebit - Update to version 1.1.1.  See their [changelog for details](https://github.com/harold-b/bladebit/releases/tag/1.1.1)

## [0.5.5] - 2021-09-13 

- Chia - Update to version 1.2.6.  See their [changelog for details](https://github.com/Chia-Network/chia-blockchain/releases/tag/1.2.6).
- Plotman - Update to version 0.5.2 with support for the [Bladebit](https://github.com/harold-b/bladebit) in-memory plotter.
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
- Chia - Update to release of 1.2.3.  See their [changelog for details](https://github.com/Chia-Network/chia-blockchain/releases/tag/1.2.3).
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
- Update to release of Chia 1.2.2, including a fix for harvester cache updates.  See their [changelog for details](https://github.com/Chia-Network/chia-blockchain/releases/tag/1.2.2).

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
