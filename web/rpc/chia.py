#
# RPC interactions with Chia on controller via WebUI
#

import asyncio
import datetime
import importlib

if importlib.util.find_spec("chia"): # Also Chives
    from chia.rpc.full_node_rpc_client import FullNodeRpcClient
    from chia.rpc.farmer_rpc_client import FarmerRpcClient
    from chia.util.default_root import DEFAULT_ROOT_PATH
    from chia.util.ints import uint16
    from chia.util.config import load_config as load_fork_config
elif importlib.util.find_spec("chives"):
    from chives.rpc.full_node_rpc_client import FullNodeRpcClient
    from chives.rpc.farmer_rpc_client import FarmerRpcClient
    from chives.util.default_root import DEFAULT_ROOT_PATH
    from chives.util.ints import uint16
    from chives.util.config import load_config as load_fork_config
elif importlib.util.find_spec("flax"):
    from flax.rpc.full_node_rpc_client import FullNodeRpcClient
    from flax.rpc.farmer_rpc_client import FarmerRpcClient
    from flax.util.default_root import DEFAULT_ROOT_PATH
    from flax.util.ints import uint16
    from flax.util.config import load_config as load_fork_config
elif importlib.util.find_spec("flora"):
    from flora.rpc.full_node_rpc_client import FullNodeRpcClient
    from flora.rpc.farmer_rpc_client import FarmerRpcClient
    from flora.util.default_root import DEFAULT_ROOT_PATH
    from flora.util.ints import uint16
    from flora.util.config import load_config as load_fork_config
elif importlib.util.find_spec("hddcoin"):
    from hddcoin.rpc.full_node_rpc_client import FullNodeRpcClient
    from hddcoin.rpc.farmer_rpc_client import FarmerRpcClient
    from hddcoin.util.default_root import DEFAULT_ROOT_PATH
    from hddcoin.util.ints import uint16
    from hddcoin.util.config import load_config as load_fork_config

else:
    raise Exception("RPC modules found on pythonpath!")

from web import app

async def load_plots_per_harvester():
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
            host = harvester["connection"]["host"]
            plots = harvester["plots"]
            harvester_plots = []
            for plot in plots:
                harvester_plots.append({
                    "type": "solo" if (plot["pool_contract_puzzle_hash"] is None) else "portable",
                    "plot_id": plot['plot_id'],
                    "file_size": plot['file_size'], # bytes
                    "filename": plot['filename'], # full path and name
                    "plot_public_key": plot['plot_public_key'],
                    "pool_contract_puzzle_hash": plot['pool_contract_puzzle_hash'],
                    "pool_public_key": plot['pool_public_key'],
                })
            harvesters[host] = harvester_plots
    except Exception as ex:
        app.logger.info("Error getting plots via RPC: {0}".format(str(ex)))
    return harvesters
