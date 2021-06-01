from . import alerts
from . import farms
from . import plots
from . import plottings
from . import workers


MODULES = (
    alerts,
    farms,
    plots,
    plottings,
    workers,
)


def register_blueprints(api):
    for module in MODULES:
        api.register_blueprint(module.blp)