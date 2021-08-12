#
# RPC interactions with Chia
#

from chia.rpc.full_node_rpc_client import FullNodeRpcClient
from chia.rpc.farmer_rpc_client import FarmerRpcClient
from chia.util.default_root import DEFAULT_ROOT_PATH
from chia.util.ints import uint16
from chia.util.config import load_config as load_chia_config

from api import app

# Unused as I am getting signage points from debug.log as this API returns no dates
async def get_signage_points(blockchain):
    config = load_chia_config(DEFAULT_ROOT_PATH, 'config.yaml')
    farmer_rpc_port = config["farmer"]["rpc_port"]
    farmer = await FarmerRpcClient.create(
        'localhost', uint16(farmer_rpc_port), DEFAULT_ROOT_PATH, config
    )
    points = await farmer.get_signage_points()
    farmer.close()
    await farmer.await_closed()
    config = load_chia_config(DEFAULT_ROOT_PATH, 'config.yaml')
    full_node_rpc_port = config["full_node"]["rpc_port"]
    fullnode = await FullNodeRpcClient.create(
        'localhost', uint16(full_node_rpc_port), DEFAULT_ROOT_PATH, config
    )
    for point in points:
        sp = point['signage_point']
        signage_point = await fullnode.get_recent_signage_point_or_eos(
            sp_hash=sp['challenge_chain_sp'],
            challenge_hash=sp['challenge_hash'])
        app.logger.info(signage_point)
    fullnode.close()
    await fullnode.await_closed()
    return points

# Used on Pools page to display each pool's state
async def get_pool_state(blockchain):
    pools = []
    try:
        config = load_chia_config(DEFAULT_ROOT_PATH, 'config.yaml')
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

# Used to load plot type (solo or portable) via RPC
async def get_all_plots():
    all_plots = []
    try:
        config = load_chia_config(DEFAULT_ROOT_PATH, 'config.yaml')
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
