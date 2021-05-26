import time
import atexit

from apscheduler.schedulers.background import BackgroundScheduler

from app import app
from app.schedules import farm_stats

scheduler = BackgroundScheduler()
scheduler.add_job(func=farm_stats.collect, trigger='cron', minute=0)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())
