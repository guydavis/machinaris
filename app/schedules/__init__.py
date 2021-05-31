import time
import atexit

from apscheduler.schedulers.background import BackgroundScheduler

from app import app
from app.schedules import farm_stats, disk_stats

scheduler = BackgroundScheduler()
scheduler.add_job(func=farm_stats.collect, trigger='cron', minute=0)  # Hourly
scheduler.add_job(func=disk_stats.collect, trigger='cron', minute="*/5") # Every 5 minutes

# Testing only
#scheduler.add_job(func=farm_stats.collect, trigger='interval', seconds=20) # Test immediately
#scheduler.add_job(func=disk_stats.collect, trigger='interval', seconds=20) # Test immediately

scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())
