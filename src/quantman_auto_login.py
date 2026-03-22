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
from selenium.webdriver.common.keys import Keys
from twilio.rest import Client
from twilio.base.exceptions import TwilioException
import pytz  # pip install pytz

# Load environment variables
load_dotenv()

# Get base directory for absolute paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

from logging.handlers import RotatingFileHandler

# Configure logging masking
class SecretFilter(logging.Filter):
    def __init__(self, secrets=None):
        super().__init__()
        self.secrets = secrets or []

    def filter(self, record):
        if not self.secrets:
            return True
        msg = str(record.msg)
        for secret in self.secrets:
            if secret and str(secret).strip():
                msg = msg.replace(str(secret), "[MASKED]")
        record.msg = msg
        return True

# Silence verbose third-party loggers
logging.getLogger('selenium').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('twilio').setLevel(logging.WARNING)

# Configure rotating logging (5MB per file, max 5 files)
log_file_path = os.path.join(LOG_DIR, 'quantman_login.log')
file_handler = RotatingFileHandler(
    log_file_path, 
    maxBytes=5 * 1024 * 1024, # 5 megabytes
    backupCount=5,
    encoding='utf-8', 
    mode='a'
)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        file_handler,
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
secret_filter = SecretFilter()
logger.addFilter(secret_filter)

ist = pytz.timezone('Asia/Kolkata')

current_date_ist = datetime.now(ist).strftime("%d-%m-%Y")
logins_dir = "logins"
ft_username = None
login_file_name = None


class QuantmanAutoLogin:
    """
    Automated login class for quantman.in with flattrade broker integration
    """

    def __init__(self, config_file: str = None):
        """
        Initialize the auto-login system

        Args:
            config_file: Path to configuration file (defaults to config/config.json)
        """
        if config_file is None:
            config_file = os.path.join(BASE_DIR, "config", "config.json")
        self.config = self.load_config(config_file)
        
        # Populate secrets for masking in logs
        secret_filter.secrets.extend([
            self.config.get('password'),
            self.config.get('pin'),
            self.config.get('totp_secret'),
            self.config.get('GITHUB_TOKEN'),
            os.getenv('TWILIO_ACCOUNT_SID'),
            os.getenv('TWILIO_AUTH_TOKEN'),
            os.getenv('FLATTRADE_API_KEY'),
            os.getenv('FLATTRADE_API_SECRET')
        ])
        
        self.driver = None
        self.wait = None
        self.totp_secret = self.config.get('totp_secret')
        self.GITHUB_OWNER = self.config.get('GITHUB_OWNER')
        self.GITHUB_REPO = self.config.get('GITHUB_REPO')
        self.GITHUB_TOKEN = self.config.get('GITHUB_TOKEN')
        # Load retry settings from config, with sane defaults
        self.retry_config = self.config.get('retry_settings', {'attempts': 1, 'delay_seconds': 5})
        self.buffer_small_delay_seconds = self.config.get('buffer_small_delay_seconds', 3)
        self.buffer_medium_delay_seconds = self.config.get('buffer_medium_delay_seconds', 6)

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
            chrome_options.add_argument('--disable-popup-blocking')
            chrome_options.add_argument('--disable-notifications')
            # Critical for some cross-origin popups
            chrome_options.add_argument('--disable-features=IsolateOrigins,site-per-process')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.maximize_window()
            self.wait = WebDriverWait(self.driver, 20)  # Increased timeout for robustness

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

    def close_popups(self):
        """
        Detect and close common modal popups (ads, promos)
        """
        try:
            # CSS selectors
            css_selectors = [
                "button.modal-close",
                "div.modal-close-btn",
                "i.close-icon",
                ".modal-header .close"
            ]
            
            # XPath selectors for text-based matching
            xpath_selectors = [
                "//button[contains(text(), 'Close')]",
                "//span[contains(text(), 'Close')]"
            ]
            
            for selector in css_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed():
                        logger.info(f"Closing popup with CSS selector: {selector}")
                        element.click()
                        time.sleep(1)
            
            for selector in xpath_selectors:
                elements = self.driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed():
                        logger.info(f"Closing popup with XPath selector: {selector}")
                        element.click()
                        time.sleep(1)
        except Exception as e:
            logger.warning(f"Error while trying to close popups: {e}")

    def open_quantman(self):
        """
        Open quantman.in website
        """
        try:
            self.driver.get("https://quantman.in")
            logger.info("Opened quantman.in")

            # Wait for page to load
            self.wait.until(EC.visibility_of_element_located((By.TAG_NAME, "body")))
            
            # Close any initial popups
            self.close_popups()

        except TimeoutException:
            logger.error("Timeout waiting for quantman.in to load")
            raise

    def select_flattrade_broker(self):
        """
        Select Flattrade broker from the list
        """
        try:
            # Step 1: Find and click the 'Login With Broker' button directly
            logger.info("Looking for 'Login With Broker' button on landing page")
            
            # Robust landing page selectors found via browser inspection
            landing_page_selectors = [
                (By.CSS_SELECTOR, "button.login-btn"),
                (By.CSS_SELECTOR, "button.free-trial-button"),
                (By.XPATH, "//button[contains(normalize-space(.), 'Login')]"),
                (By.XPATH, "//div[contains(normalize-space(.), 'Login With Broker')]"),
                (By.XPATH, "//button[contains(@class, 'change-broker-btn')]")
            ]
            
            login_btn = None
            # Retry for up to 15 seconds to give the landing page extra time to render
            for retry in range(3):
                for by, val in landing_page_selectors:
                    try:
                        # Use a short timeout for each individual check
                        temp_wait = WebDriverWait(self.driver, 5)
                        login_btn = temp_wait.until(EC.element_to_be_clickable((by, val)))
                        if login_btn:
                            logger.info(f"Entry point found using {by}: {val} (Attempt {retry+1})")
                            break
                    except:
                        continue
                if login_btn:
                    break
                logger.info(f"Entry point not found, retrying in 5 seconds... (Attempt {retry+1}/3)")
                time.sleep(5)
                
            if not login_btn:
                # Final Debugging: Capture a screenshot to see what's actually on the screen
                fail_screen = os.path.join(LOG_DIR, 'failed_login_discovery.png')
                self.driver.save_screenshot(fail_screen)
                logger.error(f"Failed to find any login entry points. Screenshot saved to {fail_screen}")
                # Direct navigation attempt
                logger.info("Trying direct navigation to help trigger the modal...")
                self.driver.execute_script("window.scrollTo(0, 500);")
                time.sleep(1)
                raise Exception("Unable to locate any login entry point on the landing page.")

            self.driver.execute_script("arguments[0].click();", login_btn)
            logger.info("Clicked initial Login button successfully")
            
            # Wait for the search modal to appear after clicking
            search_input = self.wait.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Search'], input[placeholder*='broker']"))
            )

            # Step 2: Feed "flattrade" into the search box
            search_input.clear()
            search_input.send_keys("flattrade")
            time.sleep(self.buffer_small_delay_seconds)

            # Step 3: Select the "Flattrade" option
            # Look for elements containing 'Flattrade' text
            flattrade_option = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'card-actions__label') and contains(text(), 'Flattrade')] | //span[contains(text(), 'Flattrade')] | //div[contains(text(), 'Flattrade')]"))
            )
            flattrade_option.click()
            time.sleep(self.buffer_small_delay_seconds)

            logger.info("Selected Flattrade broker successfully")
        except Exception as e:
            logger.error(f"Error selecting Flattrade broker: {e}")
            raise

    def fill_initial_login_details(self):
        """
        Fill in the login credentials on Quantman
        """
        try:
            # Wait for the Flattrade User Id input
            user_id_field = self.wait.until(
                EC.visibility_of_element_located((By.ID, "flattrade-client-id"))
            )
            user_id_field.clear()
            user_id_field.send_keys(self.config['username'])

            # Optional: Reveal and fill API details only if available in environment
            api_key = os.getenv('FLATTRADE_API_KEY')
            api_secret = os.getenv('FLATTRADE_API_SECRET')
            
            if api_key and api_secret:
                try:
                    logger.info("Filling API details from environment...")
                    change_api_link = self.driver.find_element(By.XPATH, "//span[contains(text(), 'Change API details?')]")
                    change_api_link.click()
                    time.sleep(1)
                    
                    api_key_field = self.wait.until(EC.visibility_of_element_located((By.ID, "flattrade-api-key")))
                    api_key_field.clear()
                    api_key_field.send_keys(api_key)

                    api_secret_field = self.wait.until(EC.visibility_of_element_located((By.ID, "flattrade-secret-key")))
                    api_secret_field.clear()
                    api_secret_field.send_keys(api_secret)
                    logger.info("Initial API details filled")
                except Exception as e:
                    logger.warning(f"Could not fill API details (might be already set): {e}")

            # Click login button in the modal
            login_btn = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'main-button') and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'login')] | //form//button[@type='submit']"))
            )
            # Use JS click if normal click fails
            try:
                login_btn.click()
            except:
                self.driver.execute_script("arguments[0].click();", login_btn)
            
            logger.info("Clicked initial Login button")
            time.sleep(self.buffer_small_delay_seconds)

        except TimeoutException as te:
            logger.error(f"Initial Login | Timeout: {te}")
            raise
        except Exception as e:
            logger.error(f"Initial Login | Error: {e}")
            raise

    def handle_flattrade_auth_window(self):
        """
        Handle the secondary authentication window on auth.flattrade.in
        """
        try:
            # Small delay to let browser stabilize after click
            time.sleep(3)
            main_window = self.driver.current_window_handle
            
            # Diagnostic: check window count before waiting
            initial_count = 1  # We know it starts with just the main window
            logger.info(f"Initial window handles count: {initial_count}")
            
            # Polling instead of a single wait to prevent potential hung calls
            logger.info("Polling for Flattrade auth window to appear...")
            found = False
            for i in range(12): # 12 attempts * 5 seconds = 60 seconds
                try:
                    current_handles = self.driver.window_handles
                    logger.info(f"Poll {i+1}: Current handle count = {len(current_handles)}")
                    if len(current_handles) > initial_count:
                        found = True
                        break
                except Exception as e:
                    logger.warning(f"Error checking window handles: {e}")
                
                # If still at 1 window after 15s, try one more click
                if i == 3 and len(self.driver.window_handles) == initial_count:
                    logger.info("Attempting secondary click on Login button (JS)...")
                    try:
                        login_btn = self.driver.find_element(By.XPATH, "//div[contains(text(), 'Login')] | //button[contains(text(), 'Login')] | //div[contains(@class, 'main-button')]")
                        self.driver.execute_script("arguments[0].click();", login_btn)
                    except:
                        pass
                
                time.sleep(5)
            
            if not found:
                logger.warning("No new window appeared after 60s of polling.")
            
            # Find the correct window by URL
            auth_window = None
            logger.info("Iterating handles to find auth window...")
            for handle in self.driver.window_handles:
                try:
                    if handle == main_window:
                        continue
                        
                    self.driver.switch_to.window(handle)
                    # Wait for redirect to flattrade (up to 10s)
                    logger.info(f"Checking window {handle}. Waiting for redirect to auth.flattrade.in...")
                    start_wait = time.time()
                    while time.time() - start_wait < 10:
                        current_url = self.driver.current_url
                        if "auth.flattrade.in" in current_url:
                            auth_window = handle
                            logger.info(f"✅ CONFIRMED: Found Flattrade auth window: {current_url}")
                            break
                        time.sleep(2)
                    
                    if auth_window:
                        break
                except Exception as e:
                    logger.warning(f"Error checking handle {handle}: {e}")
                    continue
            
            if not auth_window:
                # Fallback: check all windows again or pick last
                handles = self.driver.window_handles
                if len(handles) > 1:
                    auth_window = handles[-1]
                    self.driver.switch_to.window(auth_window)
                    logger.warning(f"Using fallback window: {self.driver.current_url}")
                else:
                    raise TimeoutException("Could not find any secondary window for authentication.")

            time.sleep(self.buffer_medium_delay_seconds)

            # Wait for user field and fill credentials
            try:
                user_field = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[placeholder*='User ID']")))
            except TimeoutException:
                logger.error("Timeout finding userName. Dumping DOM to flattrade_auth_dom.html...")
                with open("flattrade_auth_dom.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                raise
            user_field.clear()
            user_field.send_keys(self.config['username'])

            password_field = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[placeholder*='Password']")))
            password_field.clear()
            password_field.send_keys(self.config['password'])

            # Generate and fill TOTP
            totp_code = self.generate_totp()
            totp_field = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[placeholder*='OTP']")))
            totp_field.clear()
            totp_field.send_keys(totp_code)
            
            logger.info("Flattrade auth fields filled successfully")

            # Click Log In button
            try:
                # Use a broader set of robust selectors
                selectors = [
                    (By.CSS_SELECTOR, "button.shine-button"),
                    (By.XPATH, "//button[.//span[contains(text(), 'Log In')]] | //button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'login')]")
                ]
                
                submit_btn = None
                for by, val in selectors:
                    try:
                        submit_btn = self.wait.until(EC.presence_of_element_located((by, val)))
                        if submit_btn:
                            logger.info(f"Found login button with {by}: {val}")
                            break
                    except TimeoutException:
                        continue
                
                if not submit_btn:
                    raise TimeoutException("Could not find Log In button with any selector")
                
                # Try normal click, then JS click as fallback
                try:
                    submit_btn.click()
                    logger.info("Clicked Flattrade Log In button")
                except:
                    self.driver.execute_script("arguments[0].click();", submit_btn)
                    logger.info("Clicked Flattrade Log In button via JS")
            except Exception as e:
                logger.error(f"Error clicking Log In button: {e}")
                raise

            # Wait for the auth window to close itself (Success indicator)
            logger.info("Waiting for authentication window to close (indicates success)...")
            start_wait = time.time()
            auth_closed = False
            while time.time() - start_wait < 15:
                if len(self.driver.window_handles) < 2:
                    auth_closed = True
                    break
                time.sleep(1)
            
            if not auth_closed:
                logger.warning("Auth window still open after 15s. Taking screenshot and attempting to switch back to main window.")
                try:
                    self.driver.save_screenshot("flattrade_auth_error_state.png")
                    logger.info("Saved flattrade_auth_error_state.png")
                except Exception as ss_e:
                    logger.error(f"Failed to take screenshot: {ss_e}")

                if len(self.driver.window_handles) > 0:
                    self.driver.switch_to.window(self.driver.window_handles[0])
            else:
                logger.info("Authentication window closed successfully")
            
            self.driver.switch_to.window(main_window)
            logger.info("Flattrade auth stage completed")
        except Exception as e:
            logger.error(f"Error handling Flattrade auth window: {str(e)}\n{traceback.format_exc()}")
            raise

    def check_login_status(self) -> bool:
        """
        Verify if login was successful by checking the Quantman dashboard.
        """
        try:
            logger.info("Verifying login status on Quantman dashboard...")
            
            # Use a fresh, longer wait for the dashboard
            dashboard_wait = WebDriverWait(self.driver, 60)
            
            for attempt in range(2):
                try:
                    # Look for cards or dashboard elements
                    cards = dashboard_wait.until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.card.info"))
                    )
                    
                    for card in cards:
                        card_text = card.text
                        if "Broker Integration" in card_text:
                            logger.info(f"Retrieved Broker Integration card text: {card_text!r}")
                            if "Yes" in card_text and "Automatic" in card_text:
                                logger.info("Login successful - found 'Yes' and 'Automatic' in Broker Integration card")
                                return True
                            else:
                                logger.warning(f"Broker Integration found but status is not 'Yes Automatic': {card_text!r}")
                    
                    # If we finished the loop and didn't return True, try refresh if it's the first attempt
                    if attempt == 0:
                        logger.info("Dashboard card not found or status incorrect, refreshing page...")
                        self.driver.refresh()
                        time.sleep(5)
                except TimeoutException:
                    if attempt == 0:
                        logger.info("Dashboard cards not found, refreshing page once...")
                        self.driver.refresh()
                        time.sleep(5)
                    else:
                        logger.error("Timeout waiting for broker integration cards after refresh")
            
            return False
        except Exception as e:
            logger.error(f"Error checking login status: {str(e)}\n{traceback.format_exc()}")
            return False

    def send_whatsapp_notification(self, message: str):
        """
        Send WhatsApp notification using Twilio

        Args:
            message: Message to send
        """
        try:
            if not self.twilio_client:
                logger.warning("Twilio client not configured")
                return

            phone_number = os.getenv('NOTIFICATION_PHONE_NUMBER')
            if not phone_number:
                logger.warning("Notification phone number not configured")
                return

            message_obj = self.twilio_client.messages.create(
                body=message,
                from_=f"whatsapp:{os.getenv('TWILIO_WHATSAPP_NUMBER')}",
                to=f"whatsapp:{phone_number}"
            )

            logger.info(f"WhatsApp notification sent: {message_obj.sid}")

        except TwilioException as e:
            logger.error(f"Error sending WhatsApp notification: {str(e)}\n{traceback.format_exc()}")
        except Exception as e:
            logger.error(f"Unexpected error sending WhatsApp notification: {str(e)}\n{traceback.format_exc()}")

    def send_sms_notification(self, message: str):
        """
        Send SMS notification using Twilio

        Args:
            message: Message to send
        """
        try:
            if not self.twilio_client:
                logger.warning("Twilio client not configured")
                return

            phone_number = os.getenv('NOTIFICATION_PHONE_NUMBER')
            if not phone_number:
                logger.warning("Notification phone number not configured")
                return

            message_obj = self.twilio_client.messages.create(
                body=message,
                from_=os.getenv('TWILIO_PHONE_NUMBER'),
                to=phone_number
            )

            logger.info(f"SMS notification sent: {message_obj.sid}")

        except TwilioException as e:
            logger.error(f"Error sending SMS notification: {str(e)}\n{traceback.format_exc()}")
        except Exception as e:
            logger.error(f"Unexpected error sending SMS notification: {str(e)}\n{traceback.format_exc()}")

    def notify_status(self, success: bool, error_message: str = None):
        """
        Send notifications about login status
        Args:
            success: Whether login was successful
            error_message: Error message if login failed
        """
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_time_ist = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")

        if success:
            message = f"✅ Quantman Login Successful\nIST Time: {current_time_ist}\nTime: {current_time}\nBroker: Flattrade\nStatus: Logged in successfully"
        else:
            message = f"❌ Quantman Login Failed\nIST Time: {current_time_ist}\nTime: {current_time}\nBroker: Flattrade\nError: {error_message or 'Unknown error'}"

        logger.info(f"Sending notification: {message}")

        if self.config.get("notification_settings", {}).get("whatsapp_enabled", False):
            logger.info(f"trying to send WhatsApp notification...")
            self.send_whatsapp_notification(message)
            logger.info(f"WhatsApp notification sent: {message}")
        else:
            logger.info("WhatsApp notifications are disabled in configuration.")

        if self.config.get("notification_settings", {}).get("sms_enabled", False):
            logger.info(f"trying to send SMS notification...")
            self.send_sms_notification(message)
            logger.info(f"SMS notification sent: {message}")
        else:
            logger.info("SMS notifications are disabled in configuration.")

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
        """
        ft_username = self.config['username']
        login_file_name = f"{current_date_ist}_{ft_username}_quantman.txt"
        
        attempts = self.retry_config.get('attempts', 3)
        delay = self.retry_config.get('delay_seconds', 30)
        last_exception = None

        # Check if a successful login file for today already exists
        if self.is_exists_github_login_file(login_file_name):
            logger.info(f"Login file for today ({current_date_ist}) and user {ft_username} already exists. Assuming already logged in.")
            self.notify_status(success=True, error_message="Already logged in based on existing file.")
            return True


        for attempt in range(1, attempts + 1):
            try:
                # if attempt == 1:
                #     raise ValueError("Dummy Exception")
                logger.info(f"--- Starting login attempt {attempt} of {attempts} ---")
                self.setup_driver(headless)  # Setup a fresh driver for each attempt
                if self.login(headless=headless):
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

    def login(self, headless: bool = False) -> bool:
        """
        Main login function
        Args: headless: Run browser in headless mode
        Returns: True if login successful, False otherwise
        """
        try:
            logger.info("Starting Quantman auto-login process")

            # Setup WebDriver
            # self.setup_driver(headless)

            # Open quantman.in
            self.open_quantman()

            # Select Flattrade broker
            self.select_flattrade_broker()

            # Fill initial login details
            self.fill_initial_login_details()

            # Handle Flattrade authentication window
            self.handle_flattrade_auth_window()

            # Check login status
            success = self.check_login_status()

            # Send notifications
            if success:
                self.notify_status(True)
                logger.info("Login process completed successfully")
            else:
                self.notify_status(False, "Login verification failed")
                logger.error("Login process failed")

            return success

        except Exception as e:
            error_msg = f"Login process error: {str(e)}"
            logger.error(error_msg)
            self.notify_status(False, str(e))
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
        login_system = QuantmanAutoLogin()

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
