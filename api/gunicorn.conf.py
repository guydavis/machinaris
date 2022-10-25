# Initialize the scheduler only once, not in each worker
from api.schedules import periodically_sync_wallet


def on_starting(server):
    import atexit
    import os
    import time

    from datetime import datetime, timedelta
    from apscheduler.schedulers.background import BackgroundScheduler

    from api import app, utils
    from api.schedules import status_worker, status_farm, status_plotting, \
        status_plots, status_challenges, status_wallets, status_blockchains, \
        status_connections, status_keys, status_alerts, status_controller, \
        status_plotnfts, status_pools, status_partials, status_drives, \
        stats_blocks, stats_balances, stats_disk, stats_farm, nft_recover, plots_check, \
        log_rotate, restart_stuck_farmer, geolocate_peers, \
        stats_effort, status_warnings
    from common.config import globals
    from common.models import pools, plottings

    from api.commands import websvcs

    scheduler = BackgroundScheduler()

    schedule_every_x_minutes = "?"
    try:
        schedule_every_x_minutes = app.config['STATUS_EVERY_X_MINUTES']
        JOB_FREQUENCY = 60 * int(schedule_every_x_minutes)
        JOB_JITTER = JOB_FREQUENCY / 2
    except:
        app.logger.info("Failed to configure job schedule frequency in minutes as setting was: '{0}'".format(schedule_every_x_minutes))
        JOB_FREQUENCY = 60 # once a minute
        JOB_JITTER = 30 # 30 seconds
    app.logger.info("Scheduler frequency will be once every {0} seconds.".format(JOB_FREQUENCY))

    # Every single container should report as a worker
    scheduler.add_job(func=status_worker.update, name="status_workers", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER) 

    # Collect disk stats from all modes where blockchain is chia, avoiding duplicate disks from multiple forks on same host
    if 'chia' in globals.enabled_blockchains():
        scheduler.add_job(func=stats_disk.collect, name="stats_disk", trigger='cron', minute="*/10") # Every 10 minutes
        scheduler.add_job(func=status_drives.update, name="status_drives", trigger='cron', minute="*/15") # Every 15 minutes
        
    # MMX needs to report plots from harvesters directly as they are not listed via the fullnode like Chia does
    if not utils.is_fullnode() and globals.harvesting_enabled() and 'mmx' in globals.enabled_blockchains():
        scheduler.add_job(func=status_plots.update, name="status_plots", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER) 
    
    # Status for both farmers and harvesters (includes fullnodes)
    if globals.farming_enabled() or globals.harvesting_enabled():
        scheduler.add_job(func=status_challenges.update, name="status_challenges", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER)
        scheduler.add_job(func=status_alerts.update, name="status_alerts", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER) 
        scheduler.add_job(func=log_rotate.execute, name="log_rotate", trigger='cron', minute=0)  # Hourly
    
    if globals.farming_enabled() and 'chia' in globals.enabled_blockchains():  # For now, only Chia fullnodes
        scheduler.add_job(func=status_warnings.collect, name="status_warnings", trigger='cron', minute="*/20") # Every 20 minutes

    # Status for plotters
    if globals.plotting_enabled():
        scheduler.add_job(func=status_plotting.update, name="plottings", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER)
          
    # Status for fullnodes, all different forks
    if utils.is_fullnode():
        scheduler.add_job(func=stats_farm.collect, name="stats_farm", trigger='cron', minute=0)  # Hourly
        scheduler.add_job(func=stats_effort.collect, name="stats_effort", trigger='cron', minute=0)  # Hourly
        scheduler.add_job(func=status_wallets.update, name="status_wallets", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER) 
        scheduler.add_job(func=status_blockchains.update, name="status_blockchains", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER) 
        scheduler.add_job(func=status_connections.update, name="status_connections", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER) 
        scheduler.add_job(func=status_keys.update, name="status_keys", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER)
        scheduler.add_job(func=status_farm.update, name="status_farm", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER) 
        scheduler.add_job(func=stats_blocks.collect, name="status_blocks", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER)
        scheduler.add_job(func=restart_stuck_farmer.execute, name="status_blockchain_sync", trigger='interval', minutes=5, jitter=0) 
        scheduler.add_job(func=periodically_sync_wallet.execute, name="status_wallet_sync", trigger='interval', minutes=15, jitter=0) 
        scheduler.add_job(func=nft_recover.execute, name="status_nft_recover", trigger='interval', hours=1) # Once an hour
        if globals.enabled_blockchains()[0] in plottings.PLOTTABLE_BLOCKCHAINS: # Only get plot listing from these three blockchains
            scheduler.add_job(func=status_plots.update, name="status_plots", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER)
        if globals.enabled_blockchains()[0] in pools.POOLABLE_BLOCKCHAINS: # Only get pool submissions from poolable blockchains
            scheduler.add_job(func=status_pools.update, name="status_pools", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER)
            scheduler.add_job(func=status_partials.update, name="status_partials", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER)
            scheduler.add_job(func=status_plotnfts.update, name="status_plotnfts", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER) 
        
    # Status for single Machinaris controller only, should be blockchain=chia
    if utils.is_controller():
        scheduler.add_job(func=plots_check.execute, name="plot_checks", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER, 
            start_date=(datetime.now() + timedelta(minutes = 30))) # Delay first plots check until well after launch
        scheduler.add_job(func=status_controller.update, name="status_controller", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER) 
        scheduler.add_job(func=websvcs.get_prices, name="status_exchange_prices", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER) 
        scheduler.add_job(func=websvcs.get_chain_statuses, name="status_blockchain_networks", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER) 
        scheduler.add_job(func=geolocate_peers.execute, name="stats_geolocate_peers", trigger='interval', seconds=JOB_FREQUENCY, jitter=JOB_JITTER) 
        scheduler.add_job(func=stats_balances.collect, name="stats_balances", trigger='cron', minute=0)  # Hourly
        
    # Testing only
    #scheduler.add_job(func=status_plotnfts.update, name="status_plotnfts", trigger='interval', seconds=10) # Test immediately
    #scheduler.add_job(func=stats_effort.collect, name="stats_effort", trigger='interval', seconds=10) # Test immediately
    #scheduler.add_job(func=stats_balances.collect, name="stats_balances", trigger='interval', seconds=10) # Test immediately
    #scheduler.add_job(func=websvcs.get_chain_statuses, name="get_chain_statuses", trigger='interval', seconds=10) # Test immediately
    #scheduler.add_job(func=status_farm.update, name="farms", trigger='interval', seconds=10) # Test immediately
    #scheduler.add_job(func=status_alerts.update, name="alerts", trigger='interval', seconds=10) # Test immediately
    #scheduler.add_job(func=periodically_sync_wallet.execute, name="periodically_sync_wallet", trigger='interval', seconds=60) # Test immediately
    #scheduler.add_job(func=status_warnings.collect, name="status_warnings", trigger='interval', seconds=60) # Test immediately
    #scheduler.add_job(func=nft_recover.execute, name="status_nft_recover", trigger='interval', seconds=60)

    app.logger.debug("Starting background scheduler...")
    scheduler.start()

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
