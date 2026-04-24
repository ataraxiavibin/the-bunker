# scheduler.py
#
# was darf hier sein?
#
# i mean, the scheduler is the bunker.py. When the service does run, the bunker must be online and running.

import schedule
import time
import subprocess
from loguru import logger

logger.add("./logs/scheduler.log", rotation="10 MB", retention="30 days", level="INFO")

def check_berserk():
    try:
        subprocess.run(["python", "-m", "services.berserk_checker.checker"], timeout=60)
    except subprocess.TimeoutExpired:
        logger.error("berserk_checker timed out!")


schedule.every(1).days.do(check_berserk)

while True:
    schedule.run_pending()
    time.sleep(1)
