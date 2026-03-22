#!/usr/bin/env python3
"""
Configuration validator to check if all settings are properly configured
"""

import json
import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(BASE_DIR, 'config', 'config.json')
ENV_PATH = os.path.join(BASE_DIR, '.env')

def validate_config():
    """Validate config.json file"""
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)

        required_fields = ['username', 'password', 'pin', 'totp_secret']
        missing_fields = []
        placeholder_fields = []

        for field in required_fields:
            if field not in config:
                missing_fields.append(field)
            elif str(config[field]).startswith('your_'):
                placeholder_fields.append(field)

        if missing_fields:
            print(f"❌ Missing required fields in config.json: {missing_fields}")
            return False

        if placeholder_fields:
            print(f"⚠️  Placeholder values found in config.json: {placeholder_fields}")
            print("   Please update these with actual values")
            return False

        print("✅ config.json validation passed")
        return True

    except FileNotFoundError:
        print("❌ config.json not found")
        return False
    except json.JSONDecodeError:
        print("❌ Invalid JSON format in config.json")
        return False

def validate_env():
    """Validate .env file"""
    try:
        load_dotenv(ENV_PATH)

        required_vars = [
            'TWILIO_ACCOUNT_SID',
            'TWILIO_AUTH_TOKEN',
            'TWILIO_PHONE_NUMBER',
            'NOTIFICATION_PHONE_NUMBER'
        ]

        missing_vars = []
        placeholder_vars = []

        for var in required_vars:
            value = os.getenv(var)
            if not value:
                missing_vars.append(var)
            elif value.startswith('your_'):
                placeholder_vars.append(var)

        if missing_vars:
            print(f"❌ Missing environment variables: {missing_vars}")
            return False

        if placeholder_vars:
            print(f"⚠️  Placeholder values found in .env: {placeholder_vars}")
            print("   Please update these with actual values")
            return False

        print("✅ .env file validation passed")
        return True

    except Exception as e:
        print(f"❌ Error validating .env file: {e}")
        return False

def validate_dependencies():
    """Validate required Python packages"""
    try:
        import selenium
        import pyotp
        import twilio
        from dotenv import load_dotenv

        print("✅ All required dependencies are installed")
        return True

    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   Run: pip install -r requirements.txt")
        return False

if __name__ == "__main__":
    print("Validating Quantman Auto-Login Configuration")
    print("=" * 45)

    print("\n1. Checking dependencies...")
    deps_ok = validate_dependencies()

    print("\n2. Validating config.json...")
    config_ok = validate_config()

    print("\n3. Validating .env file...")
    env_ok = validate_env()

    print("\n" + "=" * 45)

    if deps_ok and config_ok and env_ok:
        print("✅ All validations passed! Ready to use.")
    else:
        print("❌ Some validations failed. Please fix the issues above.")
