# 🏗 Project Architecture - pyQuantmanAutoLogin

The pyQuantmanAutoLogin system is designed for **high reliability and autonomous execution** of the login process for a specifically complex Quantman + Flattrade workflow.

## 📐 System Map
The system is built on three main pillars:

### 1. Automation Pillar (Selenium + Chrome)
This layer directly interacts with the Quantman web application and the Flattrade authentication popup. It behaves like a human user by:
- Navigating URLs.
- Clicking buttons.
- Handling redirects from `quantman.trade` to `auth.flattrade.in`.
- Identifing elements using **placeholder-based CSS selectors** (not dynamic IDs) for long-term stability.

### 2. Authentication Pillar (pyotp)
This layer generates **time-based one-time passwords (TOTP)** on the fly to bypass 2FA challenges. It eliminates the need for any manual intervention at the two-factor authentication stage.

### 3. Persistence & Notification Pillar (Requests + Twilio + GitHub API)
- **GitHub API Persistence**: The system checks the GitHub repository's content (the `logins/` path) to see if you have already logged in today. This minimizes the risk of multiple login attempts and prevents session locks.
- **Twilio Notifications**: Upon success or failure, the system sends an instant alert via **WhatsApp** or **SMS** based on your configuration.

---

## 🔄 The Login Flow (Sequence)
1.  **Check Condition**: The `QuantmanAutoLogin` class probes the GitHub repo for a login file from the current date.
2.  **WebDriver Setup**: Chrome is initialized with specific options to stabilize popup handling (`--disable-features=IsolateOrigins,site-per-process`, `--disable-popup-blocking`).
3.  **Headless Stealth Mode**: The system runs in a "Modern Headless" mode (`--headless=new`) which is much harder for security services to detect compared to legacy headless modes.
4.  **Broker Selection**: The script triggers the broker dialog using the `Ctrl+K` shortcut, searches for "Flattrade," and selects it.
5.  **Flattrade Auth Popup**: 
    - The script identifies a new window handle after clicking the login button.
    - It switches to the new window and waits for the redirect.
    - It fills out User ID, Password, and TOTP on the Flattrade auth page.
6.  **Submission**: The script submits the Flattrade form and waits for the popup to close automatically, signaling success.
7.  **Cloudflare Handling**: Before verifying elements, the script proactively checks for and solves Cloudflare Turnstile challenges using specialized stealth parameters and simulated user interactions.
8.  **Verification**: The script returns to the main window and probes for specific "Broker Integration" and "Live Credits" elements on the dashboard to confirm a successful session.
8.  **Status Propagation**: Success or error messages are sent via Twilio, and a new login status file is created on GitHub.

---

## 🛡️ Stability & reliability
- **Retry Mechanism**: If a transient network glitch or selector issue occurs, the system will automatically retry based on your `retry_settings` in `config.json`.
- **Diagnostic Forensics**: If the login fails after all retries, the script dumps the target window's HTML source to `logs/flattrade_auth_dom.html` and captures a screenshot to `logs/flattrade_auth_error_state.png` for instant debugging.
- **Configurable Buffers**: The script includes delays (`buffer_small_delay_seconds`, etc.) to account for slow-loading broker modals and modals that use Vuetify transitions.

---
## 📜 Developer Notes
-   **Security**: Ensure your `.env` and `config/config.json` are **never committed** to the repository (the `.gitignore` is already configured for this).
-   **Credentials**: Always keep your `TOTP_SECRET` and `PAT` (GitHub Token) as secret as possible.
