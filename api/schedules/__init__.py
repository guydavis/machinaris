import time
import atexit

from apscheduler.schedulers.background import BackgroundScheduler

from api import app
from api.schedules import status_worker, status_farm
from api.schedules import stats_disk, stats_farm

scheduler = BackgroundScheduler()

# Statistics gathering locally
#scheduler.add_job(func=stats_farm.collect, trigger='cron', minute=0)  # Hourly
#scheduler.add_job(func=stats_disk.collect, trigger='cron', minute="*/5") # Every 5 minutes

# Testing only
#scheduler.add_job(func=stats_farm.collect, trigger='interval', seconds=20) # Test immediately
#scheduler.add_job(func=stats_disk.collect, trigger='interval', seconds=20) # Test immediately
#scheduler.add_job(func=status_farm.update, trigger='interval', seconds=20) # Test immediately

# Status gathering - reported via API
scheduler.add_job(func=status_worker.update, trigger='interval', seconds=20) # Test immediately
scheduler.add_job(func=status_farm.update, trigger='interval', seconds=20) # Test immediately

scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())
