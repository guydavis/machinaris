from . import actions
from . import analysis
from . import alerts
from . import blockchains
from . import certificates
from . import challenges
from . import configs
from . import connections
from . import farms
from . import keys
from . import logs
from . import partials
from . import ping
from . import plotnfts
from . import plots
from . import plottings
from . import pools
from . import wallets
from . import workers

from .stats import plottingdiskused,plottingdiskfree,plotsdiskused,plotsdiskfree

MODULES = (
    actions,
    analysis,
    alerts,
    blockchains,
    challenges,
    certificates,
    configs,
    connections,
    farms,
    keys,
    logs,
    partials,
    ping,
    plotnfts,
    plots,
    plottings,
    pools,
    wallets,
    workers,

    plottingdiskused,
    plottingdiskfree,
    plotsdiskused,
    plotsdiskfree
)


def register_blueprints(api):
    for module in MODULES:
        api.register_blueprint(module.blp)