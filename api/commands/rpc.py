#
# RPC interactions with Chia and fork blockchains
#

import asyncio
import datetime
import importlib
import os
import traceback
import uuid

from common.config import globals
from api import app
from api import utils

blockchain = globals.enabled_blockchains()[0]

if blockchain == "apple":
    from apple.rpc.full_node_rpc_client import FullNodeRpcClient
    from apple.rpc.farmer_rpc_client import FarmerRpcClient
    from apple.rpc.wallet_rpc_client import WalletRpcClient
    from apple.util.default_root import DEFAULT_ROOT_PATH
    from apple.util.ints import uint16
    from apple.util.config import load_config as load_fork_config
elif blockchain == "bpx":
    from chia.rpc.full_node_rpc_client import FullNodeRpcClient
    from chia.rpc.farmer_rpc_client import FarmerRpcClient
    from chia.rpc.wallet_rpc_client import WalletRpcClient
    from chia.util.default_root import DEFAULT_ROOT_PATH
    from chia.util.ints import uint16
    from chia.util.config import load_config as load_fork_config
elif blockchain == "btcgreen":
    from btcgreen.rpc.full_node_rpc_client import FullNodeRpcClient
    from btcgreen.rpc.farmer_rpc_client import FarmerRpcClient
    from btcgreen.rpc.wallet_rpc_client import WalletRpcClient
    from btcgreen.util.default_root import DEFAULT_ROOT_PATH
    from btcgreen.util.ints import uint16
    from btcgreen.util.config import load_config as load_fork_config
elif blockchain == "cactus":
    from cactus.rpc.full_node_rpc_client import FullNodeRpcClient
    from cactus.rpc.farmer_rpc_client import FarmerRpcClient, PlotPathRequestData
    from cactus.rpc.wallet_rpc_client import WalletRpcClient
    from cactus.util.default_root import DEFAULT_ROOT_PATH
    from cactus.util.ints import uint16
    from cactus.util.config import load_config as load_fork_config
elif blockchain == "chia": 
    from chia.rpc.full_node_rpc_client import FullNodeRpcClient
    from chia.rpc.farmer_rpc_client import FarmerRpcClient, PlotPathRequestData
    from chia.rpc.wallet_rpc_client import WalletRpcClient
    from chia.util.default_root import DEFAULT_ROOT_PATH
    from chia.util.ints import uint16
    from chia.util.config import load_config as load_fork_config
elif blockchain == "chinilla":
    from chinilla.rpc.full_node_rpc_client import FullNodeRpcClient
    from chinilla.rpc.farmer_rpc_client import FarmerRpcClient
    from chinilla.rpc.wallet_rpc_client import WalletRpcClient
    from chinilla.util.default_root import DEFAULT_ROOT_PATH
    from chinilla.util.ints import uint16
    from chinilla.util.config import load_config as load_fork_config
elif blockchain == "chives":
    from chives.rpc.full_node_rpc_client import FullNodeRpcClient
    from chives.rpc.farmer_rpc_client import FarmerRpcClient
    from chives.rpc.wallet_rpc_client import WalletRpcClient
    from chives.util.default_root import DEFAULT_ROOT_PATH
    from chives.util.ints import uint16
    from chives.util.config import load_config as load_fork_config
elif blockchain == "cryptodoge":
    from cryptodoge.rpc.full_node_rpc_client import FullNodeRpcClient
    from cryptodoge.rpc.farmer_rpc_client import FarmerRpcClient
    from cryptodoge.rpc.wallet_rpc_client import WalletRpcClient
    from cryptodoge.util.default_root import DEFAULT_ROOT_PATH
    from cryptodoge.util.ints import uint16
    from cryptodoge.util.config import load_config as load_fork_config
elif blockchain == "ecostake":
    from ecostake.rpc.full_node_rpc_client import FullNodeRpcClient
    from ecostake.rpc.farmer_rpc_client import FarmerRpcClient
    from ecostake.rpc.wallet_rpc_client import WalletRpcClient
    from ecostake.util.default_root import DEFAULT_ROOT_PATH
    from ecostake.util.ints import uint16
    from ecostake.util.config import load_config as load_fork_config
elif blockchain == "flax":
    from flax.rpc.full_node_rpc_client import FullNodeRpcClient
    from flax.rpc.farmer_rpc_client import FarmerRpcClient, PlotPathRequestData
    from flax.rpc.wallet_rpc_client import WalletRpcClient
    from flax.util.default_root import DEFAULT_ROOT_PATH
    from flax.util.ints import uint16
    from flax.util.config import load_config as load_fork_config
elif blockchain == "flora":
    from chia.rpc.full_node_rpc_client import FullNodeRpcClient
    from chia.rpc.farmer_rpc_client import FarmerRpcClient
    from chia.rpc.wallet_rpc_client import WalletRpcClient
    from chia.util.default_root import DEFAULT_ROOT_PATH
    from chia.util.ints import uint16
    from chia.util.config import load_config as load_fork_config
elif blockchain == "gold":
    from chia.rpc.full_node_rpc_client import FullNodeRpcClient
    from chia.rpc.farmer_rpc_client import FarmerRpcClient
    from chia.rpc.wallet_rpc_client import WalletRpcClient
    from chia.util.default_root import DEFAULT_ROOT_PATH
    from chia.util.ints import uint16
    from chia.util.config import load_config as load_fork_config
elif blockchain == "hddcoin":
    from hddcoin.rpc.full_node_rpc_client import FullNodeRpcClient
    from hddcoin.rpc.farmer_rpc_client import FarmerRpcClient
    from hddcoin.rpc.wallet_rpc_client import WalletRpcClient
    from hddcoin.util.default_root import DEFAULT_ROOT_PATH
    from hddcoin.util.ints import uint16
    from hddcoin.util.config import load_config as load_fork_config
elif blockchain == "littlelambocoin":
    from littlelambocoin.rpc.full_node_rpc_client import FullNodeRpcClient
    from littlelambocoin.rpc.farmer_rpc_client import FarmerRpcClient
    from littlelambocoin.rpc.wallet_rpc_client import WalletRpcClient
    from littlelambocoin.util.default_root import DEFAULT_ROOT_PATH
    from littlelambocoin.util.ints import uint16
    from littlelambocoin.util.config import load_config as load_fork_config
elif blockchain == "maize":
    from maize.rpc.full_node_rpc_client import FullNodeRpcClient
    from maize.rpc.farmer_rpc_client import FarmerRpcClient
    from maize.rpc.wallet_rpc_client import WalletRpcClient
    from maize.util.default_root import DEFAULT_ROOT_PATH
    from maize.util.ints import uint16
    from maize.util.config import load_config as load_fork_config
elif blockchain == "mint":
    from mint.rpc.full_node_rpc_client import FullNodeRpcClient
    from mint.rpc.farmer_rpc_client import FarmerRpcClient
    from mint.rpc.wallet_rpc_client import WalletRpcClient
    from mint.util.default_root import DEFAULT_ROOT_PATH
    from mint.util.ints import uint16
    from mint.util.config import load_config as load_fork_config
elif blockchain == "mmx":
    pass
elif blockchain == "nchain": 
    from chia.rpc.full_node_rpc_client import FullNodeRpcClient
    from chia.rpc.farmer_rpc_client import FarmerRpcClient
    from chia.rpc.wallet_rpc_client import WalletRpcClient
    from chia.util.default_root import DEFAULT_ROOT_PATH
    from chia.util.ints import uint16
    from chia.util.config import load_config as load_fork_config
elif blockchain == "petroleum":
    from chia.rpc.full_node_rpc_client import FullNodeRpcClient
    from chia.rpc.farmer_rpc_client import FarmerRpcClient
    from chia.rpc.wallet_rpc_client import WalletRpcClient
    from chia.util.default_root import DEFAULT_ROOT_PATH
    from chia.util.ints import uint16
    from chia.util.config import load_config as load_fork_config
elif blockchain == "profit":
    from profit.rpc.full_node_rpc_client import FullNodeRpcClient
    from profit.rpc.farmer_rpc_client import FarmerRpcClient
    from profit.rpc.wallet_rpc_client import WalletRpcClient
    from profit.util.default_root import DEFAULT_ROOT_PATH
    from profit.util.ints import uint16
    from profit.util.config import load_config as load_fork_config
elif blockchain == "shibgreen":
    from shibgreen.rpc.full_node_rpc_client import FullNodeRpcClient
    from shibgreen.rpc.farmer_rpc_client import FarmerRpcClient
    from shibgreen.rpc.wallet_rpc_client import WalletRpcClient
    from shibgreen.util.default_root import DEFAULT_ROOT_PATH
    from shibgreen.util.ints import uint16
    from shibgreen.util.config import load_config as load_fork_config
elif blockchain == "silicoin":
    from chia.rpc.full_node_rpc_client import FullNodeRpcClient
    from chia.rpc.farmer_rpc_client import FarmerRpcClient
    from chia.rpc.wallet_rpc_client import WalletRpcClient
    from chia.util.default_root import DEFAULT_ROOT_PATH
    from chia.util.ints import uint16
    from chia.util.config import load_config as load_fork_config
elif blockchain == "staicoin":
    from stai.rpc.full_node_rpc_client import FullNodeRpcClient
    from stai.rpc.farmer_rpc_client import FarmerRpcClient
    from stai.rpc.wallet_rpc_client import WalletRpcClient
    from stai.util.default_root import DEFAULT_ROOT_PATH
    from stai.util.ints import uint16
    from stai.util.config import load_config as load_fork_config
elif blockchain == "stor":
    from stor.rpc.full_node_rpc_client import FullNodeRpcClient
    from stor.rpc.farmer_rpc_client import FarmerRpcClient
    from stor.rpc.wallet_rpc_client import WalletRpcClient
    from stor.util.default_root import DEFAULT_ROOT_PATH
    from stor.util.ints import uint16
    from stor.util.config import load_config as load_fork_config
elif blockchain == "tad":
    from tad.rpc.full_node_rpc_client import FullNodeRpcClient
    from tad.rpc.farmer_rpc_client import FarmerRpcClient
    from tad.rpc.wallet_rpc_client import WalletRpcClient
    from tad.util.default_root import DEFAULT_ROOT_PATH
    from tad.util.ints import uint16
    from tad.util.config import load_config as load_fork_config
elif blockchain == "wheat":
    from wheat.rpc.full_node_rpc_client import FullNodeRpcClient
    from wheat.rpc.farmer_rpc_client import FarmerRpcClient
    from wheat.rpc.wallet_rpc_client import WalletRpcClient
    from wheat.util.default_root import DEFAULT_ROOT_PATH
    from wheat.util.ints import uint16
    from wheat.util.config import load_config as load_fork_config
else:
    app.logger.info("No RPC modules found on pythonpath for blockchain: {0}".format(os.environ['blockchains']))

class RPC:
    def __init__(self):
        # Workaround, see: https://stackoverflow.com/a/46750562/3072265
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Used to load all plots on all harvesters
    def get_all_plots_test_harness(self):
        testing_plots = []
        for i in range(240): # 240 x 500 is 120000 plots
            for plot in asyncio.run(self._load_all_plots())[:500]:
                #old_plot_name = plot['filename']
                plot['plot_id'] = str(uuid.uuid4())[:16] # Generate a unique plot
                idx = plot['filename'].rindex('-')
                plot['filename'] = plot['filename'][:idx+1] + plot['plot_id'] + plot['filename'][idx+17:]
                #app.logger.info("{0} -> {1}".format(old_plot_name, plot['filename']))
                testing_plots.append(plot)
        return testing_plots

    # Used to load all plots on all harvesters
    def get_all_plots(self):
        plots_via_rpc = asyncio.run(self._load_all_plots())
        return plots_via_rpc

    # Get all wallet info
    def get_wallets(self):
        if not globals.wallet_running():
            return []
        wallets = asyncio.run(self._load_wallets())
        return wallets

    # Get transactions for a particular wallet
    def get_transactions(self, wallet_id, reverse=False):
        if not globals.wallet_running():
            return []
        if globals.legacy_blockchain(globals.enabled_blockchains()[0]):
            transactions = asyncio.run(self._load_transactions_legacy_blockchains(wallet_id, reverse))
        else:
            transactions = asyncio.run(self._load_transactions(wallet_id, reverse))
        return transactions

    # Get invalid plots on each harvester
    def get_harvester_warnings(self):
        invalid_plots = asyncio.run(self._load_harvester_warnings())
        return invalid_plots

    # Get status of all pools (aka plotnfts)
    def get_pool_states(self, blockchain):
        pool_states = asyncio.run(self._get_pool_states(blockchain))
        return pool_states

    # Used on Pools page to display each pool's state
    async def _get_pool_states(self, blockchain):
        pools = []
        try:
            config = load_fork_config(DEFAULT_ROOT_PATH, 'config.yaml')
            farmer_rpc_port = config["farmer"]["rpc_port"]
            farmer = await FarmerRpcClient.create(
                'localhost', uint16(farmer_rpc_port), DEFAULT_ROOT_PATH, config
            )
            result = await farmer.get_pool_state()
            farmer.close()
            await farmer.await_closed()
            if 'pool_state' in result:
                for pool in result["pool_state"]:
                    pools.append(pool)
        except Exception as ex:
            app.logger.info("Error getting {0} blockchain pool states: {1}".format(blockchain, str(ex)))
        return pools

    # Load all plots from all harvesters
    async def _load_all_plots(self):
        all_plots = []
        try:
            config = load_fork_config(DEFAULT_ROOT_PATH, 'config.yaml')
            farmer_rpc_port = config["farmer"]["rpc_port"]
            farmer = await FarmerRpcClient.create(
                'localhost', uint16(farmer_rpc_port), DEFAULT_ROOT_PATH, config
            )
            result = await farmer.get_harvesters()
            farmer.close()
            await farmer.await_closed()
            for harvester in result["harvesters"]:
                # app.logger.info(harvester.keys()) Returns: ['connection', 'failed_to_open_filenames', 'no_key_filenames', 'plots']
                # app.logger.info(harvester['connection']) Returns: {'host': '192.168.1.100', 'node_id': '602eb9...90378', 'port': 62599}
                host = utils.convert_chia_ip_address(harvester["connection"]["host"])
                plots = harvester["plots"]
                #app.logger.info("Listing plots found {0} plots on {1}.".format(len(plots), host))
                for plot in plots:
                    all_plots.append({
                        "hostname": host,
                        "type": "solo" if (plot["pool_contract_puzzle_hash"] is None) else "portable",
                        "plot_id": plot['plot_id'],
                        "file_size": plot['file_size'], # bytes
                        "filename": plot['filename'], # full path and name
                        "plot_public_key": plot['plot_public_key'],
                        "pool_contract_puzzle_hash": plot['pool_contract_puzzle_hash'],
                        "pool_public_key": plot['pool_public_key'],
                    })
        except Exception as ex:
            app.logger.info("Error getting plots via RPC: {0}".format(str(ex)))
        return all_plots

    # Load all the wallet info
    async def _load_wallets(self):
        wallets = []
        try:
            config = load_fork_config(DEFAULT_ROOT_PATH, 'config.yaml')
            wallet_rpc_port = config["wallet"]["rpc_port"]
            wallet = await WalletRpcClient.create(
                'localhost', uint16(wallet_rpc_port), DEFAULT_ROOT_PATH, config
            )
            result = await wallet.get_wallets()
            wallet.close()
            await wallet.await_closed()
            wallets.extend(result)
        except Exception as ex:
            app.logger.info("Error getting plots via RPC: {0}".format(str(ex)))
        return wallets

    # Load all transactions for a wallet id number
    async def _load_transactions_legacy_blockchains(self, wallet_id, reverse):
        transactions = []
        config = load_fork_config(DEFAULT_ROOT_PATH, 'config.yaml')
        wallet_rpc_port = config["wallet"]["rpc_port"]
        try:
            # Now load the transactions
            wallet = await WalletRpcClient.create(
                'localhost', uint16(wallet_rpc_port), DEFAULT_ROOT_PATH, config
            )
            result = await wallet.get_transactions(wallet_id)  
            if reverse: # Old blockchains can't take reverse param
                result.reverse()
            wallet.close()
            await wallet.await_closed()
            transactions.extend(result)
        except Exception as ex:
            app.logger.info("Error getting transactions via RPC: {0}".format(str(ex)))
        return transactions

    # Load all transactions for a wallet id number, get total count first
    async def _load_transactions(self, wallet_id, reverse):
        transactions = []
        try:
            config = load_fork_config(DEFAULT_ROOT_PATH, 'config.yaml')
            wallet_rpc_port = config["wallet"]["rpc_port"]
            # First load the total count, but this method only works on newish blockchains
            wallet = await WalletRpcClient.create(
                'localhost', uint16(wallet_rpc_port), DEFAULT_ROOT_PATH, config
            )
            count = await wallet.get_transaction_count(wallet_id)
            wallet.close()
            await wallet.await_closed()
            # Now load the transactions
            wallet = await WalletRpcClient.create(
                'localhost', uint16(wallet_rpc_port), DEFAULT_ROOT_PATH, config
            )
            result = await wallet.get_transactions(wallet_id, 0, count, reverse=reverse)
            wallet.close()
            await wallet.await_closed()
            transactions.extend(result)
        except Exception as ex:
            app.logger.info("Error getting transactions via RPC: {0}".format(str(ex)))
        return transactions

    # Get warnings about problem plots, only first 100 warnings each to avoid overwhelming the user
    async def _load_harvester_warnings(self):
        harvesters = {}
        try:
            config = load_fork_config(DEFAULT_ROOT_PATH, 'config.yaml')
            farmer_rpc_port = config["farmer"]["rpc_port"]
            farmer = await FarmerRpcClient.create(
                'localhost', uint16(farmer_rpc_port), DEFAULT_ROOT_PATH, config
            )
            result = await farmer.get_harvesters()
            farmer.close()
            await farmer.await_closed()

            for harvester in result["harvesters"]:
                
                # app.logger.info(harvester.keys()) Returns: ['connection', 'failed_to_open_filenames', 'no_key_filenames', 'plots']
                # app.logger.info(harvester['connection']) Returns: {'host': '192.168.1.100', 'node_id': '602eb9...90378', 'port': 62599}
                host = utils.convert_chia_ip_address(harvester["connection"]["host"])
                node_id = harvester["connection"]["node_id"] # TODO Track link between worker and node_id?
                #app.logger.info(node_id)

                # Plots Invalid
                farmer = await FarmerRpcClient.create(
                    'localhost', uint16(farmer_rpc_port), DEFAULT_ROOT_PATH, config
                )

                invalid_plots = []
                results = await farmer.get_harvester_plots_invalid(PlotPathRequestData(bytes.fromhex(node_id[2:]), 0, 1000))
                invalid_plots.extend(results['plots'][:100])
                farmer.close()
                await farmer.await_closed()

                # Plots Missing Keys
                farmer = await FarmerRpcClient.create(
                    'localhost', uint16(farmer_rpc_port), DEFAULT_ROOT_PATH, config
                )
                missing_keys = []
                results = await farmer.get_harvester_plots_keys_missing(PlotPathRequestData(bytes.fromhex(node_id[2:]), 0, 1000))
                missing_keys.extend(results['plots'][:100])
                farmer.close()
                await farmer.await_closed()

                # Plots Duplicated, only on a single worker, not across entire farm
                farmer = await FarmerRpcClient.create(
                    'localhost', uint16(farmer_rpc_port), DEFAULT_ROOT_PATH, config
                )
                duplicate_plots = []
                results = await farmer.get_harvester_plots_duplicates(PlotPathRequestData(bytes.fromhex(node_id[2:]), 0, 1000))
                duplicate_plots.extend(results['plots'][:100])
                farmer.close()
                await farmer.await_closed()

                harvesters[host] = \
                    {
                        'node': node_id, 
                        'invalid_plots': invalid_plots, 
                        'missing_keys': missing_keys, 
                        'duplicate_plots': duplicate_plots
                    }
        except Exception as ex:
            app.logger.info("Error getting harvester warnings: {0}".format(str(ex)))
            traceback.print_exc()
        return harvesters
