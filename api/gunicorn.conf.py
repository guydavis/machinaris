# Initialize the scheduler only once, not in each worker
def on_starting(server):
    import atexit
    import os
    import time

    from apscheduler.schedulers.background import BackgroundScheduler

    from api import app
    from api.schedules import status_worker, status_farm, status_plotting, \
        status_plots, status_challenges, status_wallets, status_blockchains, \
        status_connections, status_keys, status_alerts, status_controller
    from api.schedules import stats_disk, stats_farm

    scheduler = BackgroundScheduler()

    # Statistics gathering locally
    scheduler.add_job(func=stats_farm.collect, trigger='cron', minute=0)  # Hourly
    scheduler.add_job(func=stats_disk.collect, trigger='cron', minute="*/5") # Every 5 minutes

    # Testing only
    #scheduler.add_job(func=stats_farm.collect, trigger='interval', seconds=10) # Test immediately
    #scheduler.add_job(func=stats_disk.collect, trigger='interval', seconds=10) # Test immediately

    # Status gathering - reported via API
    scheduler.add_job(func=status_challenges.update, trigger='interval', seconds=5)
    scheduler.add_job(func=status_worker.update, trigger='interval', seconds=60, jitter=30) 
    scheduler.add_job(func=status_controller.update, trigger='interval', seconds=60, jitter=30) 
    scheduler.add_job(func=status_farm.update, trigger='interval', seconds=60, jitter=30) 
    scheduler.add_job(func=status_plotting.update, trigger='interval', seconds=60, jitter=30) 
    scheduler.add_job(func=status_plots.update, trigger='interval', seconds=60, jitter=30)  
    scheduler.add_job(func=status_wallets.update, trigger='interval', seconds=60, jitter=30) 
    scheduler.add_job(func=status_blockchains.update, trigger='interval', seconds=60, jitter=30) 
    scheduler.add_job(func=status_connections.update, trigger='interval', seconds=60, jitter=30) 
    scheduler.add_job(func=status_keys.update, trigger='interval', seconds=60, jitter=30) 
    scheduler.add_job(func=status_alerts.update, trigger='interval', seconds=60, jitter=30) 
    app.logger.debug("Starting background scheduler...")
    scheduler.start()

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
