pyQuantmanAutoLogin/
├── src/
│   ├── main.py                 # (Not present, using quantman_auto_login.py)
│   ├── quantman_auto_login.py  # Main automation script
│   ├── scheduler.py            # Automated scheduling
│   ├── test_totp.py            # TOTP testing utility
│   ├── test_notifications.py   # Notification testing utility
│   └── validate_config.py      # Configuration validator
├── config/
│   ├── config.template.json    # Configuration template
│   └── config.json             # YOUR REAL CREDENTIALS (Ignored)
├── docs/
│   ├── ARCHITECTURE.md         # System design
│   ├── CHALLENGES_AND_LEARNINGS.md # Debugging history
│   ├── SECRET_MANAGEMENT.md    # GitHub Secrets guide
│   └── ...                     # Other docs
├── requirements.txt            # Python dependencies
└── README.md                  # Setup instructions
```

## Maintenance Note
Last updated: 2026-03-23
The `quantman_auto_login.py` script has been significantly enhanced with Cloudflare Turnstile bypass logic and robust artifact saving for CI environments.
