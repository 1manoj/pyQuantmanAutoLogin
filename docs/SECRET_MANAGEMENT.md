# 🛡️ Secret Management Guide

This guide explains how to secure your sensitive credentials while maintaining the ability to run automated GitHub Workflows for the Quantman login system.

## 📐 Overview
To run the Quantman automation on GitHub Actions without checking your passwords or TOTP secret into the public repository, follow this four-phase approach:

---

## 🔒 Phase 1: Local Privacy (The .gitignore Rule)
Ensure your sensitive local files never reach GitHub in the first place:
1.  **`.env`**: Store your secrets like `TWILIO_ACCOUNT_SID` and `FLATTRADE_API_KEY` here.
2.  **`config/config.json`**: This is your real, active credentials file.
3.  **The Templates**: 
    - Use **`.env.example`** and **`config/config.template.json`** to share the structure of your setup with others safely.
    - **NEVER** put real passwords in these template files.

---

## 🚀 Phase 2: Storing Secrets on GitHub
GitHub has a dedicated feature for this called **Repository Secrets**.
1.  Navigate to your repository on GitHub.
2.  Go to **Settings** > **Secrets and variables** > **Actions**.
3.  Click **New repository secret** for each of these:
    - `FLATTRADE_USERNAME`
    - `FLATTRADE_PASSWORD`
    - `FLATTRADE_PIN`
    - `TOTP_SECRET`
    - **`GH_PAT`**: (Personal Access Token) This replaces the built-in `GITHUB_TOKEN` for repository-wide write permissions.
    - **Twilio Secrets**: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, etc.

---

## 🔄 Phase 3: Injecting Secrets into the Workflow
The system generates a temporary `config.json` on the GitHub runner at runtime. 

Update your `.github/workflows/scheduled-quantman-login.yml` as follows:

```yaml
- name: Create Configuration File
  env:
    USERNAME: ${{ secrets.FLATTRADE_USERNAME }}
    PASSWORD: ${{ secrets.FLATTRADE_PASSWORD }}
    PIN: ${{ secrets.FLATTRADE_PIN }}
    TOTP_SECRET: ${{ secrets.TOTP_SECRET }}
    GH_TOKEN: ${{ secrets.GH_PAT }}
  run: |
    mkdir -p config
    echo '{
      "broker": "Flattrade",
      "username": "'$USERNAME'",
      "password": "'$PASSWORD'",
      "pin": "'$PIN'",
      "totp_secret": "'$TOTP_SECRET'",
      "GITHUB_OWNER": "1manoj",
      "GITHUB_REPO": "pyQuantmanAutoLogin",
      "GITHUB_TOKEN": "'$GH_TOKEN'",
      "browser_settings": { "headless": true }
    }' > config/config.json

- name: Run scheduled Quantman Login
  env:
    # Map .env secrets directly to the runner env
    TWILIO_ACCOUNT_SID: ${{ secrets.TWILIO_ACCOUNT_SID }}
    TWILIO_AUTH_TOKEN: ${{ secrets.TWILIO_AUTH_TOKEN }}
    # ... more env variables here ...
  run: |
    python src/quantman_auto_login.py
```

---

## 🚨 Phase 4: Cleaning up the History (IMPORTANT)
If you previously pushed your `.env` or `config.json` to GitHub, they are still in your **Git History**. To ensure no one can access them even after you make the repo public:

### Option A: Scrub Existing History
Use the `git-filter-repo` tool (recommended):
```bash
git filter-repo --path config/config.json --invert-paths
git filter-repo --path .env --invert-paths
git push origin --force --all
```

### Option B: Fresh Start (Safest)
1. Delete the `.git` folder locally.
2. Run `git init`.
3. Add and commit your files (ensuring `.gitignore` is active).
4. Push to a brand new repository.

---

## 🧠 Why this works:
- **Zero Leakage**: Your secrets are never written to any file that gets committed.
- **Environment Parity**: Your Python code stays clean; it just reads from the `config/` it finds.
- **Automatic Masking**: GitHub automatically masks these values in the logs (you'll see `***` instead of your real password).