# 🚀 pyQuantmanAutoLogin
### Automated Broker Login for Quantman.in
### [Cloudflare Bypass / Stealth Mode Enabled]

![Version](https://img.shields.io/badge/Version-1.1.0-blue)
![Python](https://img.shields.io/badge/Python-3.12+-green)
![License](https://img.shields.io/badge/License-MIT-purple)

Automatically log in to your **Quantman** dashboard using **Flattrade** as your broker with zero manual effort. This system handles 2FA (TOTP), same-origin redirects, and **bypasses Cloudflare's "Verify you are human" checks** using advanced stealth techniques.

---

## 🌟 Key Features
- **Total Automation**: Handles the full login sequence including the nested Flattrade popup.
- **Cloudflare Stealth Mode**: Uses `undetected-chromedriver` and `selenium-stealth` to bypass security challenges on GitHub Actions.
- **Smart 2FA**: Generates your TOTP (Time-Based OTP) on the fly.
- **Cross-Platform State**: Uses the GitHub API to check if you are already logged in for the day, preventing redundant attempts.
- **Real-time Notifications**: Get success or fail updates via **WhatsApp** or **SMS** through Twilio.
- **Diagnostic Forensics**: If anything fails, the system captures a screenshot and a snapshot of the page for diagnosis.

---

## 📁 Project Structure (Simplifed)

```text
pyQuantmanAutoLogin/
├── 📄 .env.example       # Example for your secret keys (Twilio, etc.)
├── 📂 config/            # Folder for your login settings
│   └── 📄 config.json    # YOUR REAL CREDENTIALS (Ignored by Git)
├── 📂 src/               # The brain of the automation
│   ├── 🐍 main.py        # The script you run
│   └── 🐍 scheduler.py   # To run it automatically at 9:00 AM
├── 📂 logs/              # Historical run reports and diagnostic images
└── 📄 README.md          # You are here!
```

---

## 🛠️ Installation (Step-by-Step)

### 1️⃣ Download and Install Python
Ensure you have **Python 3.11 or higher** installed from [python.org](https://www.python.org/downloads/). During installation, **make sure to check "Add Python to PATH"**.

### 2️⃣ Clone and Move
Download this folder and open your terminal (Command Prompt or PowerShell) inside this project directory.

### 3️⃣ Setup Your Environment (Non-Developers: Think of this as the "Plugin" install)
Install the required libraries:
```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuration (The Most Important Part!)

### 📝 Step A: Prepare your Secrets
1. Look for `.env.example` in the root and rename it to `.env`.
2. Open it with any text editor and fill in your Twilio details if you want notifications.

### 📝 Step B: Prepare your Credentials
1. Open the `config/` folder.
2. Look for `config.template.json` and rename it to `config.json`.
3. Fill in your **User ID**, **Password**, **PIN**, and **TOTP Secret** from Flattrade.

---

## 🏃 Ready to Run!

### Manual Run
When you want to log in immediately:
```bash
python src/quantman_auto_login.py
```

### Automatic Run (Scheduler)
If you want the computer to automatically run the login for you at market opening (9:00 AMIST):
```bash
python src/scheduler.py
```

---

## 🔍 Troubleshooting (If something goes wrong)

- **Popup not appearing?**: The script is optimized to run in "Headed" mode (visible browser). Check `config/config.json` and ensure `"headless": false` is set for first-time debugging.
- **Incorrect TOTP?**: Verify that your "TOTP Secret" matches the QR code secret provided by Flattrade during registration.
- **Check the Logs**: Look in `logs/quantman_login.log` for a detailed play-by-play or check `logs/flattrade_auth_error_state.png` for a screenshot of the failure.

---

## 📖 Deep Dives
For more technical details or cloud deployment guides:
- 🏗️ [System Architecture](docs/ARCHITECTURE.md)
- 🔒 [Securing Your Secrets on GitHub](docs/SECRET_MANAGEMENT.md)
- 🧪 [Technical Challenges & Learnings](docs/CHALLENGES_AND_LEARNINGS.md)
- 📝 [Package Inventory](docs/PACKAGE_SUMMARY.md)

---
*Disclaimer: Use this automation responsibly. Ensure compliance with Quantman and your broker's terms of service.*
