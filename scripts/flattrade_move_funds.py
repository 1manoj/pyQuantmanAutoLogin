
# quantman_auto_login.py
# Automated login script for quantman.in with flattrade broker
# Includes TOTP generation and WhatsApp/SMS notifications

import json
import logging
import os
import base64
import requests
import time
import traceback
from datetime import datetime
from typing import Dict, Optional

# Third-party imports
import pyotp
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
import pytz  # pip install pytz

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('quantman_login.log', encoding='utf-8', mode='a'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

ist = pytz.timezone('Asia/Kolkata')

current_date_ist = datetime.now(ist).strftime("%d-%m-%Y")
logins_dir = "logins"
ft_username = None
login_file_name = None


class FlatTradeMoveFunds:
    """
    Automated login class for quantman.in with flattrade broker integration
    """

    def __init__(self, config_file: str = "config.json"):
        """
        Initialize the auto-login system

        Args:
            config_file: Path to configuration file
        """
        self.config = self.load_config(config_file)
        self.driver = None
        self.wait = None
        self.totp_secret = self.config.get('totp_secret')
        self.GITHUB_OWNER = self.config.get('GITHUB_OWNER')
        self.GITHUB_REPO = self.config.get('GITHUB_REPO')
        self.GITHUB_TOKEN = self.config.get('GITHUB_TOKEN')
        # Load retry settings from config, with sane defaults
        self.retry_config = self.config.get('retry_settings', {'attempts': 1, 'delay_seconds': 5})

        # Twilio configuration for WhatsApp/SMS
        self.twilio_client = Client(
            os.getenv('TWILIO_ACCOUNT_SID'),
            os.getenv('TWILIO_AUTH_TOKEN')
        ) if os.getenv('TWILIO_ACCOUNT_SID') else None

    def load_config(self, config_file: str) -> Dict:
        """
        Load configuration from JSON file

        Args:
            config_file: Path to configuration file

        Returns:
            Configuration dictionary
        """
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)

            # Validate required fields
            required_fields = ['username', 'password', 'pin', 'totp_secret', 'GITHUB_OWNER', 'GITHUB_REPO', 'GITHUB_TOKEN']
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Missing required field: {field}")

            logger.info("Configuration loaded successfully")
            return config

        except FileNotFoundError:
            logger.error(f"Configuration file {config_file} not found")
            raise
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in configuration file {config_file}")
            raise

    def setup_driver(self, headless: bool = False):
        """
        Setup Chrome WebDriver with options

        Args:
            headless: Run browser in headless mode
        """
        try:
            chrome_options = Options()
            if headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')

            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.maximize_window()
            self.wait = WebDriverWait(self.driver, 10)

            logger.info("WebDriver setup completed")

        except Exception as e:
            logger.error(f"Error setting up WebDriver: {str(e)}\n{traceback.format_exc()}")
            raise

    def generate_totp(self) -> str:
        """
        Generate TOTP code using the secret key

        Returns:
            6-digit TOTP code
        """
        try:
            if not self.totp_secret:
                raise ValueError("TOTP secret not configured")

            totp = pyotp.TOTP(self.totp_secret)
            code = totp.now()

            logger.info("TOTP generated successfully")
            return code

        except Exception as e:
            logger.error(f"Error generating TOTP: {str(e)}\n{traceback.format_exc()}")
            raise

    def open_flattrade(self):
        try:
            self.driver.get("https://web.flattrade.in/#/")
            logger.info("Opened web.flattrade.in")

            # Wait for page to load
            self.wait.until(EC.visibility_of_element_located((By.TAG_NAME, "body")))

        except TimeoutException:
            logger.error("Timeout waiting for web.flattrade.in to load")
            raise

    def handle_flattrade_auth_window(self) -> bool:
        try:
            # Find the host element in the main DOM (the outer element containing shadow DOM)
            host_element = self.driver.find_element(By.TAG_NAME, "flt-glass-pane")

            # Access the shadow root using Selenium 4
            shadow_root = host_element.shadow_root

            # Now find elements inside the shadow DOM
            element_inside_shadow = shadow_root.find_element(By.CSS_SELECTOR, "input")


            shadow_root = self.driver.execute_script('return arguments[0].shadowRoot', host_element)
            # Double-check element IDs in the new window
            username_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input")))
            username_input.clear()
            username_input.send_keys(self.config['username'])

            password_field = self.driver.find_element(By.XPATH, "//input[@type='password']")
            password_field.clear()
            password_field.send_keys(self.config['password'])

            # Generate TOTP
            totp_code = self.generate_totp()

            # Fill TOTP field
            totp_field = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='OTP/TOTP']"))
            )
            totp_field.clear()
            totp_field.send_keys(totp_code)
            logger.info("Flattrade auth fields filled successfully")

            # login_btn = self.wait.until(
            #     EC.visibility_of_element_located((By.ID, "sbmt"))
            # )
            login_btn = self.driver.find_element(By.XPATH, "//button[contains(text(),'Log In') or contains(text(),'Login')]")
            time.sleep(1)
            login_btn.click()

            # Wait for a success indicator or close the auth window manually
            time.sleep(3)  # Give time for login to process

            # Wait for dashboard/home to load (use a unique selector for success!)
            self.wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(text(),'Dashboard') or contains(text(),'Welcome')]")))
            logger.info("✅ Login succeeded!")
            return True

        except Exception as e:
            logger.error(f"Error login Flattrade: {str(e)}\n{traceback.format_exc()}")
            raise

    def cleanup(self):
        """
            Clean up resources
        """
        try:
            if self.driver:
                self.driver.quit()
                logger.info("WebDriver closed")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}\n{traceback.format_exc()}")
        finally:
            # Ensure the driver is cleared to prevent reuse.
            self.driver = None
            self.wait = None

    def login_with_retries(self, headless: bool = False) -> bool:
        """
        Orchestrates the login process, retrying on failure according to the configuration.
        This is the main public method to trigger the login.

        Returns:
            True if login was successful within the allowed attempts, False otherwise.
        """
        attempts = self.retry_config.get('attempts', 3)
        delay = self.retry_config.get('delay_seconds', 30)
        last_exception = None

        for attempt in range(1, attempts + 1):
            try:
                # if attempt == 1:
                #     raise ValueError("Dummy Exception")
                logger.info(f"--- Starting login attempt {attempt} of {attempts} ---")
                self.setup_driver(headless)  # Setup a fresh driver for each attempt
                if self.login_flattrade_and_move_funds(headless=headless):
                    logger.info("✅ Login process completed successfully!")

                    current_time_ist = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")
                    # Create a directory for login files if it doesn't exist

                    # Write login success status to a file
                    logger.info(f"Writing login status to {login_file_name}")
                    file_content = f"Login successful - {ft_username} - Broker: {self.config['broker']} - IST Time: {current_time_ist}"
                    if self.create_github_login_file(login_file_name,file_content):
                        logger.info(f"Login file created successfully: {login_file_name}")
                        return True
                    else:
                        logger.error(f"Failed to create login file: {login_file_name}")
                        last_exception = Exception("Failed to create login file after successful login.")
                        self.notify_status(success=False, error_message=str(last_exception))
                        return False
                else:
                    # This case handles when check_login_status returns False without an exception
                    logger.warning(f"Attempt {attempt} failed verification. Retrying if possible...")
                    last_exception = Exception("Login verification failed after all steps.")

            except Exception as e:
                logger.error(f"Attempt {attempt} failed with an exception: {e}", exc_info=True)
                last_exception = e
            finally:
                # Clean up the driver after each attempt to ensure a clean slate for the next one
                self.cleanup()

            if attempt < attempts:
                logger.info(f"Waiting for {delay} seconds before next attempt...")
                time.sleep(delay)

        # If all attempts fail
        logger.error("❌ All login attempts have failed.")
        error_message = f"{type(last_exception).__name__}: {str(last_exception)}" if last_exception else "Unknown error after all retries."
        self.notify_status(success=False, error_message=error_message)
        return False

    def login_flattrade_and_move_funds(self, headless: bool = False) -> bool:
        """
        Main login function
        Args: headless: Run browser in headless mode
        Returns: True if login successful, False otherwise
        """
        try:
            logger.info("Starting FlatTrade auto-login process")

            # Setup WebDriver
            # self.setup_driver(headless)

            # Open quantman.in
            self.open_flattrade()

            # Handle Flattrade authentication window
            success = self.handle_flattrade_auth_window()

            # Send notifications
            if success:
                logger.info("Login process completed successfully")
            else:
                logger.error("Login process failed")

            return success

        except Exception as e:
            error_msg = f"Login process error: {str(e)}"
            logger.error(error_msg)
            return False

    def is_exists_github_login_file(self, filename, branch="master") -> bool:
        logger.info(f"Ensuring GitHub login file (EXISTS): {filename}")

        owner = self.GITHUB_OWNER
        repo = self.GITHUB_REPO
        path = f"logins/{filename}"
        token = self.GITHUB_TOKEN
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"
        }

        # Check if file exists
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            logger.info(f"File-{filename}, already exists on GitHub.")
            return True
        elif resp.status_code == 404:
            logger.info(f"File-{filename}, does NOT exists on GitHub.")
            return False
        else:
            logger.error(f"Error checking file: {resp.text}")
            return False

    def create_github_login_file(self, filename, file_content="Login successful!", branch="master") -> bool:
        owner = self.GITHUB_OWNER
        repo = self.GITHUB_REPO
        path = f"logins/{filename}"
        token = self.GITHUB_TOKEN
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"
        }

        # Create the file
        create_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        data = {
            "message": f"Create login file {filename}",
            "content": base64.b64encode(file_content.encode()).decode(),
            "branch": branch
        }
        create_resp = requests.put(create_url, headers=headers, json=data)
        if create_resp.status_code in [201, 200]:
            logger.info(f"File-{filename}, created successfully on GitHub.")
            return True
        else:
            logger.error(f"Failed to create file-{filename}: {create_resp.text}")
            return False

def main():
    """
    Main function to run the auto-login process
    """
    try:
        # Initialize auto-login system
        login_system = FlatTradeMoveFunds()

        global ft_username; ft_username = login_system.config.get('username')
        # Construct the full path for the login file
        #global login_file_name; login_file_name = os.path.join(logins_dir, f"{current_date_ist}_{ft_username}_quantman.txt")
        global login_file_name; login_file_name = f"{current_date_ist}_{ft_username}_quantman.txt"

        # Perform login
        success = login_system.login_with_retries(headless=login_system.config.get("browser_settings", {}).get("headless", False))  # Set to False for visible browser

        if success:
            print("Login successful! Check notifications for details.")
        else:
            print("Login failed! Check logs and notifications for details.")

    except Exception as e:
        logger.error(f"Fatal error in main: {str(e)}\n{traceback.format_exc()}")
        print(f"Fatal error: {str(e)}\n{traceback.format_exc()}")


if __name__ == "__main__":
    main()
