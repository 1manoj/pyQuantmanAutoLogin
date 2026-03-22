#!/usr/bin/env python3
"""
Simple scheduler to run the auto-login script at specific times
"""

import schedule
import time
import logging
from datetime import datetime
from quantman_auto_login import QuantmanAutoLogin

# Get base directory for absolute paths
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'scheduler.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run_auto_login():
    """Run the auto-login process"""
    try:
        logger.info("Starting scheduled auto-login")

        login_system = QuantmanAutoLogin()
        success = login_system.login(headless=True)

        if success:
            logger.info("Scheduled login completed successfully")
        else:
            logger.error("Scheduled login failed")

    except Exception as e:
        logger.error(f"Error in scheduled login: {e}")

def main():
    """Main scheduler function"""
    print("Quantman Auto-Login Scheduler")
    print("=============================")

    # Schedule login at 9:00 AM on weekdays (market opening time)
    schedule.every().monday.at("09:00").do(run_auto_login)
    schedule.every().tuesday.at("09:00").do(run_auto_login)
    schedule.every().wednesday.at("09:00").do(run_auto_login)
    schedule.every().thursday.at("09:00").do(run_auto_login)
    schedule.every().friday.at("09:00").do(run_auto_login)

    print("Scheduler configured for:")
    print("- Monday to Friday at 9:00 AM")
    print("- Press Ctrl+C to stop")

    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    except KeyboardInterrupt:
        print("\nScheduler stopped by user")
        logger.info("Scheduler stopped by user")

if __name__ == "__main__":
    main()
