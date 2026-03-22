#!/usr/bin/env python3
"""
Test TOTP generation to verify your secret key works correctly
"""

import json
import pyotp
from datetime import datetime

def test_totp():
    """Test TOTP generation"""
    try:
        # Load config
        with open('config.json', 'r') as f:
            config = json.load(f)

        totp_secret = config.get('totp_secret')
        if not totp_secret or totp_secret == 'your_totp_secret_key_from_authenticator_app':
            print("❌ TOTP secret not configured in config.json")
            return False

        # Generate TOTP
        totp = pyotp.TOTP(totp_secret)
        current_code = totp.now()

        print(f"✅ TOTP generated successfully!")
        print(f"Current TOTP code: {current_code}")
        print(f"Generated at: {datetime.now()}")
        print(f"Valid for approximately 30 seconds")

        # Show next code
        import time
        time.sleep(1)
        next_code = totp.now()
        print(f"Next code check: {next_code}")

        return True

    except FileNotFoundError:
        print("❌ config.json not found. Please create it first.")
        return False
    except Exception as e:
        print(f"❌ Error testing TOTP: {e}")
        return False

if __name__ == "__main__":
    print("Testing TOTP generation...")
    test_totp()
