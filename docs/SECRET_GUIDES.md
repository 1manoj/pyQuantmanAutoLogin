#How to Obtain Your Automation Secrets 🔑

This guide explains how to find the specific credentials needed for the pyQuantmanAutoLogin system. Follow these steps for each service.

---

## 📈 1. Flattrade API (Broker Login)
Flattrade requires two layers of credentials: your **Normal Account** and **API Access**.

### A. Your Standard Credentials:
- **Username**: Your FZ-ID.
- **Password**: Your trading password.
- **PIN**: Your 6-digit transaction PIN.

### B. TOTP Secret (2FA):
1.  Log in to the Flattrade web dashboard.
2.  Enable TOTP (if not already active).
3.  **Pro Tip**: When the QR code appears, **do not just scan it.** Use a "QR Code to Text" scanner (online or via phone app) to find the URL. Extract the `secret=...` parameter. 
4.  *Already scanned?*: If you've already scanned it into Google Authenticator or Microsoft Authenticator, we recommend **disabling TOTP and re-enabling it** once to get the raw Secret Key again.

### C. Flattrade API Keys:
1.  Log in to the [Flattrade API Dashboard](https://desk.flattrade.in/).
2.  Navigate to **API Documentation** or **API Dashboard**.
3.  Generate your **API Key** and **API Secret**.

---

## 💬 2. Twilio (Notifications)
Twilio is used to send you success/fail alerts via WhatsApp or SMS.

1.  **Sign Up**: Create an account at [Twilio.com](https://www.twilio.com/).
2.  **Dashboard**: Navigate to your **Console Home**.
3.  **Find Credentials**:
    - `TWILIO_ACCOUNT_SID`: (Starts with `AC...`)
    - `TWILIO_AUTH_TOKEN`: (Hidden by default, click "Show")
4.  **Sandbox setup (WhatsApp)**:
    - Go to **Messaging** > **Try it Out** > **Send a WhatsApp Message**.
    - Follow the instructions to join your own sandbox (usually by texting `join <random-word>` to a number).
    - Use that number as your `TWILIO_WHATSAPP_NUMBER`.

---

## 🐙 3. GitHub Personal Access Token (PAT)
The script uses this token to upload a daily login file so it knows not to try logging in again if you've already succeeded.

1.  Log in to GitHub.
2.  Go to **Settings** > **Developer settings** > **Personal access tokens** > **Tokens (classic)**.
3.  Click **Generate new token (classic)**.
4.  **Permissions Required**:
    - **`repo`**: (Check the **entire** box) This allows the script to read/write to your repository contents. Without this, the system will hit a `403 Forbidden` error.
    - `workflow`: (Optional, but recommended)

> [!IMPORTANT]
> If you get a **403 Forbidden** error in your logs, your token doesn't have the correct write permissions. Re-edit your token and ensure the entire **repo** scope is selected.

5.  **Copy the Token**: Copy it immediately! It starts with `ghp_...` or `github_pat_...`. 

---

## 🔒 4. Local Setup (Putting it all together)
Now that you have all the pieces:
1.  Fill in your `config/config.json` with the Flattrade details and the `GH_PAT`.
2.  Fill in your `.env` with the Twilio details.
3.  Keep these files **Private**.

*Disclaimer: Never share these secrets with anyone. If you accidentally push them to GitHub, follow the [History Scrubbing Guide](SECRET_MANAGEMENT.md#phase-4-cleaning-up-the-history-important) immediately.*
