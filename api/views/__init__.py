from . import actions
from . import analysis
from . import alerts
from . import blockchains
from . import challenges
from . import configs
from . import connections
from . import farms
from . import keys
from . import logs
from . import ping
from . import plots
from . import plottings
from . import wallets
from . import workers


MODULES = (
    actions,
    analysis,
    alerts,
    blockchains,
    challenges,
    configs,
    connections,
    farms,
    keys,
    logs,
    ping,
    plots,
    plottings,
    wallets,
    workers,
)


def register_blueprints(api):
    for module in MODULES:
        api.register_blueprint(module.blp)