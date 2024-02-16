# Changelog

All notable changes to this project will be documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
 - Support for Achi blockchain.  Requires its own plots (like Chives), you'll have to plot separately if interested. Thanks @priyankub
 - Optionally launch Chia Data Layer services (https://docs.chia.net/guides/datalayer-user-guide/) if env var `chia_data=true` is set.
### Changed
 - Harvester mode will now optionally also run chia-exporter for Prometheus results.
### Updated
 - [Chia](https://github.com/Chia-Network/chia-blockchain/releases/tag/2.1.5) to v2.1.5 - misc improvements, see their release notes.
 - [Cactus](https://github.com/Cactus-Network/cactus-blockchain/releases/tag/v2.1.4) to v2.1.4.
 - [Gigahorse](https://github.com/madMAx43v3r/chia-gigahorse/releases/tag/v2.1.4.giga26) to v2.1.4.giga26.

## [2.1.4] - 2024-01-11
### Added
 - Optionally launch `chia-exporter` [metrics endpoint](https://github.com/Chia-Network/chia-exporter) for Prometheus reporting if env var `chia_exporter=true` is set.
 - Support for running Gigahorse containers on arm64 architectures such as Raspberry Pi.
 - Main dashboard page can now be pinned (Pin Icon) to display only a blockchain of interest, rather than rotating through each in turn.
### Changed
 - Optionally launch of Gigahorse recompute server when in harvester mode if env var `gigahorse_recompute_server=true` is set.
 - Fix for Bladebit GPU plotting jobs taking a minute to display on Plotting page on job start.  Should now be seconds only.
### Updated
 - [Chia](https://github.com/Chia-Network/chia-blockchain/releases/tag/2.1.4) to v2.1.4 - misc improvements, see their release notes.
 - [Gigahorse](https://github.com/madMAx43v3r/chia-gigahorse/releases/tag/v2.1.3.giga26) to v2.1.3.giga26.

## [2.1.3] - 2023-12-19
### Updated
 - [Chia](https://github.com/Chia-Network/chia-blockchain/releases/tag/2.1.3) to v2.1.3 - fix for unforunate bug CNI released in 2.1.2

## [2.1.2] - 2023-12-13
### Added 
 - Settings | Plotting | Bladebit now supports "no_direct_io: true" option
 - Settings | Plotting | Bladebit now supports "check_plots: 100" option to check at end of plot creation
 - Settings | Plotting | Bladebit now supports "check_threshold: 0.6" option to delete invalid plots at end of plot creation
### Changed
 - Support for [Gigahorse Recompute Server](https://github.com/guydavis/machinaris/wiki/Gigahorse#recompute-server) (single GPU on fullnode/farmer), shared by multiple Gigahorse harvesters.
### Updated
 - [Chia](https://github.com/Chia-Network/chia-blockchain/releases/tag/2.1.2) to v2.1.2 - misc improvements, see their release notes.
 - [Gigahorse](https://github.com/madMAx43v3r/chia-gigahorse/releases/tag/v2.1.1.giga25) to v2.1.1.giga25 with C20 compression support.
 - [Flask](https://flask.palletsprojects.com/en/3.0.x/changes/#version-3-0-0) to v3.0.0 - serves up the Machinaris WebUI.
### Notes
 - Regression in Chia binaries (since v2.0.0) ignoring the "-y" parameter on plotnft changes, has broken pool join/leave thru WebUI.

## [2.1.0] - 2023-10-06
### Updated
 - [Bladebit](https://github.com/Chia-Network/bladebit/releases/tag/v3.1.0) to v3.1.0 - Supporting hybrid GPU/disk plotting with either 128 GB or 16 GB RAM.
 - [Chia](https://github.com/Chia-Network/chia-blockchain/releases/tag/2.1.0) to v2.1.0 - misc improvements, see their release notes.
### Notes
 - Regression in Chia binaries (since v2.0.0) ignoring the "-y" parameter on plotnft changes, has broken pool join/leave thru WebUI.

## [2.0.0] - 2023-08-24
### Added
 - Request a new plot check, via 'Recheck' button added to Check results dialog on Farming page.  
 - Optionally exclude certain plot directories from replotting check to free disk space. Useful for drives only partially dedicated to holding plots.
### Changed
 - Deprecated stale blockchains, by hiding them from Worker wizards: BPX, N-Chain, Silicoin, Stor
### Updated
 - [Bladebit](https://github.com/Chia-Network/bladebit/releases/tag/v3.0.0) to 3.0.0.
 - [Cactus](https://github.com/Cactus-Network/cactus-blockchain/releases/tag/2.0.0) to v2.0.0
 - [Chia](https://github.com/Chia-Network/chia-blockchain/releases/tag/2.0.0) to v2.0.0.
 - [Gigahorse](https://github.com/madMAx43v3r/chia-gigahorse/releases/tag/v1.8.1.giga14) to v1.8.1.giga14.
 - [HDDCoin](https://github.com/HDDcoin-Network/hddcoin-blockchain/releases/tag/3.0.0) to 3.0.0 based on Chia 1.8.2.
 - [MMX](https://github.com/madMAx43v3r/mmx-node/releases/tag/v0.10.6) to v0.10.6. 
 - [Wheat](https://github.com/wheatnetwork/wheat-blockchain/releases/tag/1.8.2) to v1.8.2.
### Notes
 - Regression in Chia binaries ignoring the "-y" parameter on plotnft changes, has broken pool join/leave thru WebUI.

## [1.8.2] - 2023-06-28
## Updated
 - [Chia](https://github.com/Chia-Network/chia-blockchain/releases/tag/1.8.2) to v1.8.2
### Notes
 - Bladebit still broken on ability to `ramplot` and `diskplot` as they try to match Gigahorse's GPU plotting. Still awaiting a fix...

## [1.8.1] - 2023-05-17
### Changed
 - By default, exclude Gigahorse plots from automated plot check due to poor performance of the 'ProofOfSpace' binary.
 - Fix for plotting manager issues when plotting with multiple tmp drives.
### Updated
 - [Bladebit](https://downloads.chia.net/bladebit/) to 3.0.0-alpha4. [Status](https://github.com/Chia-Network/bladebit/issues)
 - [BPX](https://github.com/bpx-network/bpx-blockchain/releases/tag/2.1.0) to v2.1.0
 - [Cactus](https://github.com/Cactus-Network/cactus-blockchain/releases/tag/1.8.0) to v1.8.0
 - [Chia](https://github.com/Chia-Network/chia-blockchain/releases/tag/1.8.1) to v1.8.1
 - [Flora](https://github.com/ageorge95/flora-blockchain/releases/tag/1.8.0_flora) to v1.8.0, updated by @ageorge95.
 - [Gigahorse](https://github.com/madMAx43v3r/chia-gigahorse/releases/tag/v1.8.0.giga11) to v1.8.0.giga11.
### Notes
 - Bladebit still broken on ability to `ramplot` and `diskplot` as they try to match Gigahorse's GPU plotting. Still awaiting a fix...
 - Support for new blockchains and tools DOES NOT imply my endorsement for them.  *Only run those you are comfortable with.*

## [1.8.0] - 2023-05-04
### Added
 - Concurrent plot transfers to both remote and local archive paths. Previously was one plot transferred at a time.
 - Checking for adequate free space on both tmp and dst paths before starting another plotting job.
 - Replotting selection (Farming page settings) can now target uncompressed plots for deletion.
### Changed
 - Fix for Download button on Settings pages that were providing the wrong config file. Thanks @TuftyBruno.
 - Updated German and Portuguese translations.  Thanks to @slowfinger and @antcasq. All contributions are appreciated.
 - Follow Chia version numbers (like 1.8.0) from now on, as Machinaris is on their release cadence.
### Updated 
 - [Cactus](https://github.com/Cactus-Network/cactus-blockchain/releases/tag/1.7.1) to v1.7.1
 - [Chia](https://github.com/Chia-Network/chia-blockchain/releases/tag/1.8.0) to v1.8.0
 - [Gigahorse](https://github.com/madMAx43v3r/chia-gigahorse/releases/tag/v1.8.0.giga10) to v1.8.0.giga10.
 - [HDDCoin](https://github.com/HDDcoin-Network/hddcoin-blockchain/releases/tag/3.0.0-beta.1) to 3.0.0-beta1 based on Chia 1.7.0.
 - [MMX](https://github.com/madMAx43v3r/mmx-node/releases/tag/v0.10.2) to (v0.10.2) on `testnet10`. 

## [0.8.8] - 2023-03-23
### Added
 - Support for running a blockchain timelord with environment variable `mode` set to `fullnode,timelord`.
 - Optional config setting to restart fork fullnodes if they consume too much memory. Looking at you Flora, HDDCoin, N-Chain, etc...
### Changed
 - On fresh install, optionally download (via libtorrent) a recent [Chia database checkpoint](https://www.chia.net/downloads/).
 - Fixes for Gigahorse GPU plotting including 64 GB RAM mode using the `tmp3` SSD plotting path.
 - Fix for Gigahorse Alerts, please reset [earlier broken settings file](https://github.com/guydavis/machinaris/blob/develop/config/chiadog/gigahorse.sample.yaml).
 - Fix for container stop signal to cleanly shutdown forks too, as was already happening for Chia.
### Updated 
 - [Bladebit](https://downloads.chia.net/bladebit/) to 3.0.0-alpha3. Unstable, see: https://github.com/Chia-Network/bladebit/issues
 - [Chia](https://github.com/Chia-Network/chia-blockchain/releases/tag/1.7.1) to v1.7.1
 - [Gigahorse](https://github.com/madMAx43v3r/chia-gigahorse/releases/tag/v1.6.2.giga7) to v1.6.2.giga7 with OpenCL support for AMD GPUs.
 - [MMX](https://github.com/madMAx43v3r/mmx-node/releases/tag/v0.9.14) to (v0.9.14) on `testnet9`.  Supporting the latest AMD GPU driver.
 - [One](https://github.com/xone-network/one-blockchain/releases/tag/1.7.0) to v1.7.0
### Notes
 - Bladebit has regressed on the ability to `ramplot` and `diskplot` as they try to match Gigahorse's GPU plotting. Still awaiting a fix...
 - Support for new blockchains and tools DOES NOT imply my endorsement for them.  *Only run those you are comfortable with.*

## [0.8.7] - 2023-02-16
### Added
 - Schedule plotting on the "Settings | Plotting" page to take advantage of off-peak electricity, lower your fan noise, avoid backups, etc...
 - [Bladebit](https://github.com/guydavis/machinaris/wiki/Bladebit) - alpha GPU plotting support in main Machinaris image. Set `mode: gpuplot` under `bladebit` on Settings | Plotting page.
 - [Gigahorse](https://github.com/guydavis/machinaris/wiki/Gigahorse) - beta GPU plotting and farming support in new Machinaris-Gigahorse image. Set `mode: gpuplot` under `madmax` on Settings | Plotting page.
 - [Ballcoin](https://github.com/ball-network/ballcoin-blockchain) blockchain at version 1.6.0, another slow Silicoin fork.
 - [Pipscoin](https://github.com/Pipscoin-Network/pipscoin-blockchain) blockchain at version 1.7.0.
### Changed
 - Fix missing Connections listing for Flax and MMX blockchains.  Thanks @ekersey!
 - Fix for Bladebit ramplot relaunching.  Thanks @JoeZotacExperience!
 - Multiple functionality & performance cleanups from excellent code review by @qoole.
 - Display compression level for active plotting jobs on Gigahorse and MMX.
### Updated 
 - [BTCGreen](https://github.com/BTCgreen-Network/btcgreen-blockchain/releases/tag/1.7.0b) to v1.7.0b
 - [Cactus](https://github.com/Cactus-Network/cactus-blockchain/releases/tag/1.6.2) to v1.6.2
 - [Chia](https://github.com/Chia-Network/chia-blockchain/releases/tag/1.7.0) to v1.7.0
 - [Chives](https://github.com/HiveProject2021/chives-blockchain/releases/tag/1.5.4) to v1.5.4, including staking.
 - [SHIBGreen](https://github.com/BTCgreen-Network/shibgreen-blockchain/releases/tag/1.7.0.1) to v1.7.0.1
 - [Staicoin](https://github.com/STATION-I/stai-blockchain/releases/tag/1.3.0) to v1.3.0. Note, they require a fresh `config.yaml`.
### Notes
 - Support for new blockchains and tools DOES NOT imply my endorsement for them.  *Only run those you are comfortable with.*

## [0.8.6] - 2023-01-03
### Added
 - Re-plotting: **Optional** background deletion of a few old plots to free space for new plotting. See Farming page, Settings icon, top-right.
 - Table of recent plot archiving (local and remote) on new "Plotting | Transfers" page, including status and transfer speed.
 - "Settings | Alerts" page: new 'Send Test Alert' button to validate Chiadog configs and receive sample alert to mail/discord/etc.
 - [Coffee](https://github.com/Coffee-Network/coffee-blockchain) blockchain at version 1.0.1, a slow Silicoin fork.
 - [GreenBTC](https://github.com/greenbtc/greenbtc-blockchain) blockchain at version 1.6.3, another slow Silicoin fork.
 - [Moon](https://github.com/MOONCOINTEAM/moon-blockchain) blockchain at version 1.6.0, a recent Chia fork.
 - [One](https://github.com/xone-network/one-blockchain) blockchain at version 1.6.2, a recent Chia fork.
### Changed
 - Fixed broken 'Generate/Import Key' actions for Chia 1.6.1 on Setup page. Thanks @SilverFolfy
 - Missing plots on Farming page when a status.json file was corrupted. Thanks @Yurly
 - Fix for duplicated Chiadog alerts of wallet additions. Thanks @GravitasProblem and @doma2345
 - Improved "Settings | Pools" page with fee amount and `delete_unconfirmed_transactions` action.
### Updated
 - [Bladebit](https://github.com/Chia-Network/bladebit/releases/tag/v2.0.1) to v2.0.1
 - [Chia](https://github.com/Chia-Network/chia-blockchain/releases/tag/1.6.2) to v1.6.2
 - [Chinilla](https://github.com/Chinilla/chinilla-blockchain/releases/tag/1.4.0) to v1.4.0
 - [Chiadog](https://github.com/guydavis/chiadog/releases/tag/v0.7.5) to v0.7.5
 - [Flax](https://github.com/Flax-Network/flax-blockchain/releases/tag/0.1.11) to v0.1.11
 - [MMX](https://github.com/madMAx43v3r/mmx-node/releases/tag/v0.9.3) to (v0.9.3) on `testnet9`.  Supporting the latest AMD GPU driver.
 - [Tad](https://github.com/BTCgreen-Network/tad-blockchain/releases/tag/1.7.0b2) to v1.7.0
### Notes
 - Support for new Chia forks DOES NOT imply my endorsement for them.  Only run those you are comfortable with.
 - Incorrect reward recovery calculations for some blockchains.  Please use AllTheBlocks site if this affects you.

## [0.8.5] - 2022-11-03
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
 - [Bladebit](https://github.com/Chia-Network/bladebit/releases/tag/v2.0.0) to v2.0.0
 - [Chia](https://github.com/Chia-Network/chia-blockchain/releases/tag/1.6.1) to v1.6.1
 - [Chinilla](https://github.com/Chinilla/chinilla-blockchain/releases/tag/1.3.0) to v1.3.0
 - [Littlelambocoin](https://github.com/BTCgreen-Network/littlelambocoin-blockchain/releases/tag/1.6.1) to v1.6.1
 - [Maize](https://github.com/Maize-Network/maize-blockchain/releases/tag/1.6.0) to v1.6.0
 - [MMX](https://github.com/madMAx43v3r/mmx-node) to `testnet8`.
### Known Issues
 - Incorrect reward recovery calculations for some blockchains.  Please use AllTheBlocks site if this affects you.

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
