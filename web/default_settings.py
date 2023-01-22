import os

class DefaultConfig:
    API_TITLE = "Machinaris WEB"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:////root/.chia/machinaris/dbs/default.db'
    SQLALCHEMY_BINDS = {
        'alerts':           'sqlite:////root/.chia/machinaris/dbs/alerts.db',
        'blockchains':      'sqlite:////root/.chia/machinaris/dbs/blockchains.db',
        'challenges':       'sqlite:////root/.chia/machinaris/dbs/challenges.db',
        'connections':      'sqlite:////root/.chia/machinaris/dbs/connections.db',
        'drives':           'sqlite:////root/.chia/machinaris/dbs/drives.db',
        'farms':            'sqlite:////root/.chia/machinaris/dbs/farms.db',
        'keys':             'sqlite:////root/.chia/machinaris/dbs/keys.db',
        'partials':         'sqlite:////root/.chia/machinaris/dbs/partials.db',
        'plotnfts':         'sqlite:////root/.chia/machinaris/dbs/plotnfts.db',
        'plottings':        'sqlite:////root/.chia/machinaris/dbs/plottings.db',
        'plots':            'sqlite:////root/.chia/machinaris/dbs/plots.db',
        'pools':            'sqlite:////root/.chia/machinaris/dbs/pools.db',
        'transfers':        'sqlite:////root/.chia/machinaris/dbs/transfers.db',
        'wallets':          'sqlite:////root/.chia/machinaris/dbs/wallets.db',
        'warnings':         'sqlite:////root/.chia/machinaris/dbs/warnings.db',
        'workers':          'sqlite:////root/.chia/machinaris/dbs/workers.db',

        'stat_plot_count':          'sqlite:////root/.chia/machinaris/dbs/stat_plot_count.db',
        'stat_plots_size':          'sqlite:////root/.chia/machinaris/dbs/stat_plots_size.db',
        'stat_total_coins':         'sqlite:////root/.chia/machinaris/dbs/stat_total_coins.db',
        'stat_netspace_size':       'sqlite:////root/.chia/machinaris/dbs/stat_netspace_size.db',
        'stat_time_to_win':         'sqlite:////root/.chia/machinaris/dbs/stat_time_to_win.db',
        'stat_effort':              'sqlite:////root/.chia/machinaris/dbs/stat_effort.db',
        'stat_plots_total_used':    'sqlite:////root/.chia/machinaris/dbs/stat_plots_total_used.db',
        'stat_plots_disk_used':     'sqlite:////root/.chia/machinaris/dbs/stat_plots_disk_used.db',
        'stat_plots_disk_free':     'sqlite:////root/.chia/machinaris/dbs/stat_plots_disk_free.db',
        'stat_plotting_total_used': 'sqlite:////root/.chia/machinaris/dbs/stat_plotting_total_used.db',
        'stat_plotting_disk_used':  'sqlite:////root/.chia/machinaris/dbs/stat_plotting_disk_used.db',
        'stat_plotting_disk_free':  'sqlite:////root/.chia/machinaris/dbs/stat_plotting_disk_free.db',
        'stat_farmed_blocks':       'sqlite:////root/.chia/machinaris/dbs/stat_farmed_blocks.db',
        'stat_wallet_balances':     'sqlite:////root/.chia/machinaris/dbs/stat_wallet_balances.db',
        'stat_total_balance':       'sqlite:////root/.chia/machinaris/dbs/stat_total_balance.db',
        'stat_container_mem_gib':   'sqlite:////root/.chia/machinaris/dbs/stat_container_mem_gib.db',
        'stat_host_mem_pct':        'sqlite:////root/.chia/machinaris/dbs/stat_host_mem_pct.db',
    }
    SQLALCHEMY_ECHO = True if 'FLASK_DEBUG' in os.environ and os.environ['FLASK_DEBUG'] == "development" else False
    CONTROLLER_SCHEME = 'http'
    CONTROLLER_HOST = os.environ['controller_host'] if 'controller_host' in os.environ else 'localhost'
    CONTROLLER_PORT = os.environ['controller_api_port'] if 'controller_api_port' in os.environ else '8926'

    MAX_CHART_CHALLENGES_MINS = 15

    # Note, babel looks in /machinaris/web/translations with this path.
    BABEL_TRANSLATION_DIRECTORIES = "translations"
    LANGUAGES = ['en', 'de_DE', 'fr_FR', 'it_IT', 'nl_NL', 'pt_PT', 'zh']

    # Enable client-side caching of static files; Thanks @qoole!
    SEND_FILE_MAX_AGE_DEFAULT = 86400
