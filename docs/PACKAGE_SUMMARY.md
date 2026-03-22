# Quantman Auto-Login Script - Complete Package

## 📋 Overview
This package provides a complete Python automation solution for logging into quantman.in with flattrade broker integration. The script includes TOTP generation, automatic form filling, and notification system via WhatsApp/SMS.

## 🚀 Features
- ✅ Automated login to quantman.in with flattrade broker
- ✅ Automatic TOTP (Time-based One-Time Password) generation
- ✅ WhatsApp and SMS notifications for login status
- ✅ Comprehensive error handling and logging
- ✅ Configurable settings via JSON and environment variables
- ✅ Headless browser operation support
- ✅ Testing utilities for validation
- ✅ Scheduling capabilities for automated runs

## 📁 Package Contents

### Core Files
1. **src/quantman_auto_login.py** - Main automation script
2. **config/config.json** - Configuration file template
3. **.env** - Environment variables template (Root)
4. **requirements.txt** - Python dependencies (Root)

### Utility Files
5. **tests/test_totp.py** - Test TOTP generation
6. **tests/test_notifications.py** - Test SMS/WhatsApp notifications
7. **src/scheduler.py** - Schedule automatic runs
8. **src/utils/validate_config.py** - Validate configuration setup

### Documentation
9. **README.md** - Complete setup instructions
10. **.gitignore** - Git ignore file for security
11. **docs/SECRET_MANAGEMENT.md** - Guide for secure credential handling

## 🔧 Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Settings
Update **config.json** with your flattrade credentials:
```json
{
    "username": "your_flattrade_username",
    "password": "your_flattrade_password",
    "pin": "your_flattrade_pin",
    "totp_secret": "your_totp_secret_key"
}
```

Update **.env** with Twilio credentials:
```
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890
NOTIFICATION_PHONE_NUMBER=+1234567890
```

### 3. Validate Configuration
```bash
python validate_config.py
```

### 4. Test Components
```bash
# Test TOTP generation
python test_totp.py

# Test notifications
python test_notifications.py
```

### 5. Run the Script
```bash
python src/quantman_auto_login.py
```

## 📊 Key Components

### 1. Web Automation (Selenium)
- Chrome WebDriver setup with options
- Element waiting and interaction
- Error handling for web elements

### 2. TOTP Generation (pyotp)
- Time-based OTP generation
- Secret key management
- Synchronization with authenticator apps

### 3. Notifications (Twilio)
- WhatsApp Business API integration
- SMS messaging
- Success/failure notifications

### 4. Configuration Management
- JSON configuration files
- Environment variable support
- Secure credential storage

### 5. Logging and Monitoring
- Comprehensive logging system
- Error tracking and debugging
- Activity monitoring

## 🔐 Security Features

### Data Protection
- Sensitive data in environment variables
- Configuration files in .gitignore
- No hardcoded credentials

### Error Handling
- Comprehensive try-catch blocks
- Graceful failure handling
- Detailed error logging

### Browser Security
- Headless operation support
- Automatic resource cleanup
- Secure element interaction

## 🎯 Usage Scenarios

### Manual Execution
```python
from quantman_auto_login import QuantmanAutoLogin

login_system = QuantmanAutoLogin()
success = login_system.login()
```

### Scheduled Execution
```bash
# Run scheduler for automated daily logins
python scheduler.py
```

### Testing and Validation
```bash
# Validate all configurations
python validate_config.py

# Test individual components
python test_totp.py
python test_notifications.py
```

## 🚨 Important Notes

### Legal Compliance
- Ensure compliance with quantman.in terms of service
- Respect rate limits and usage policies
- Use responsibly and ethically

### Security Practices
- Never commit sensitive files to version control
- Use strong passwords and enable 2FA
- Regularly update credentials and keys

### Maintenance
- Keep dependencies updated
- Monitor for website structure changes
- Test regularly in development environment

## 🛠️ Troubleshooting

### Common Issues
1. **Chrome Driver Problems**: Update Chrome and ChromeDriver
2. **TOTP Errors**: Check secret key and time synchronization
3. **Element Not Found**: Website structure may have changed
4. **Notification Failures**: Verify Twilio credentials and phone numbers

### Debugging Steps
1. Check logs in `quantman_login.log`
2. Run validation scripts
3. Test components individually
4. Verify all configurations

## 📈 Future Enhancements

### Potential Improvements
- Support for multiple brokers
- GUI interface for configuration
- Database logging for analytics
- Advanced scheduling options
- Multi-account support

### Customization Options
- Custom notification templates
- Configurable retry logic
- Extended logging options
- Additional security measures

## 📞 Support

For technical support:
1. Check the comprehensive logs
2. Validate configuration files
3. Test individual components
4. Review error messages and stack traces

---

**Package Created**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Author**: Python Automation System
**Version**: 1.0.0
**License**: MIT (Please ensure compliance with all applicable terms of service)

---

## 🎉 Ready to Use!

Your complete quantman.in auto-login system is now ready. Follow the quick setup guide above and you'll be automating your login process in minutes!

Remember to:
- ✅ Test in development environment first
- ✅ Keep credentials secure
- ✅ Monitor logs for issues
- ✅ Update dependencies regularly

Happy automating! 🚀
