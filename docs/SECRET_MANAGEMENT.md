# 🛡️ Secret Management Guide

This guide explains how to secure your sensitive credentials while maintaining the ability to run automated GitHub Workflows for the Quantman login system.

## 📐 Overview
To run the Quantman automation on GitHub Actions without checking your passwords or TOTP secret into the public repository, follow this three-phase approach:

## 🔒 Phase 1: Local Privacy (The .gitignore Rule)
Ensure your sensitive local files never reach GitHub in the first place:
1.  **`.env`**: Store your secrets like `TWILIO_ACCOUNT_SID` and `FLATTRADE_API_KEY` here.
2.  **`config/config.json`**: Make sure this file is added to your `.gitignore`.
3.  **`config/config.template.json`**: (Optional) Create a template file with dummy values (e.g., `"username": "YOUR_USERNAME_HERE"`) to serve as a guide for others, but never commit the real values.

## 🚀 Phase 2: Storing Secrets on GitHub
GitHub has a dedicated feature for this called **Repository Secrets**.
1.  Navigate to your repository on GitHub.
2.  Go to **Settings** > **Secrets and variables** > **Actions**.
3.  Click **New repository secret** for each of these:
    - `FLATTRADE_USERNAME`
    - `FLATTRADE_PASSWORD`
    - `FLATTRADE_PIN`
    - `TOTP_SECRET`
    - `GH_PAT` (Your GitHub Personal Access Token)

## 🔄 Phase 3: Injecting Secrets into the Workflow
Since the script in `src/quantman_auto_login.py` expects a configuration file at `config/config.json`, we will configure the GitHub Workflow to **generate this file on the fly** using the secrets you just created.

Update your `.github/workflows/scheduled-quantman-login.yml` to include a "Create Config" step:

```yaml
- name: Create Configuration File
  env:
    # Use the secrets mapped to environment variables
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
```

## 🧠 Why this works:
- **Zero Leakage**: Your secrets are never written to any file that gets committed. They only exist in the memory of the GitHub runner for the few seconds it takes to execute the login.
- **Environment Parity**: You keep the code exactly as it is (expecting a `config.json`), making it compatible with both your local machine and the cloud.
- **Security**: GitHub automatically masks these values in the logs (you'll see `***` instead of your real password).