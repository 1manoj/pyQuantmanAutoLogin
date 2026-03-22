#!/usr/bin/env python3
"""
Test notification system (WhatsApp/SMS) to verify Twilio setup
"""

import os
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.base.exceptions import TwilioException

def test_sms():
    """Test SMS notification"""
    try:
        load_dotenv()

        # Check environment variables
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        from_number = os.getenv('TWILIO_PHONE_NUMBER')
        to_number = os.getenv('NOTIFICATION_PHONE_NUMBER')

        if not all([account_sid, auth_token, from_number, to_number]):
            print("❌ Missing Twilio configuration in .env file")
            return False

        # Create client
        client = Client(account_sid, auth_token)

        # Send test SMS
        message = client.messages.create(
            body="🧪 Test SMS from Quantman Auto-Login Script",
            from_=from_number,
            to=to_number
        )

        print(f"✅ SMS sent successfully!")
        print(f"Message SID: {message.sid}")
        return True

    except TwilioException as e:
        print(f"❌ Twilio error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error sending SMS: {e}")
        return False

def test_whatsapp():
    """Test WhatsApp notification"""
    try:
        load_dotenv()

        # Check environment variables
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        from_number = os.getenv('TWILIO_WHATSAPP_NUMBER')
        to_number = os.getenv('NOTIFICATION_PHONE_NUMBER')

        if not all([account_sid, auth_token, from_number, to_number]):
            print("❌ Missing Twilio configuration in .env file")
            return False

        # Create client
        client = Client(account_sid, auth_token)

        # Send test WhatsApp message
        message = client.messages.create(
            body="🧪 Test WhatsApp from Quantman Auto-Login Script",
            from_=f"whatsapp:{from_number}",
            to=f"whatsapp:{to_number}"
        )

        print(f"✅ WhatsApp message sent successfully!")
        print(f"Message SID: {message.sid}")
        return True

    except TwilioException as e:
        print(f"❌ Twilio error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error sending WhatsApp: {e}")
        return False

if __name__ == "__main__":
    print("Testing notification system...")
    print("\n1. Testing SMS...")
    test_sms()

    print("\n2. Testing WhatsApp...")
    test_whatsapp()

    print("\n✅ Test complete! Check your phone for messages.")
