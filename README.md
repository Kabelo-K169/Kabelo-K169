# Bug Bounty Hunter Application

A lightweight Flask app to track bug bounty targets and vulnerability findings.

## Features
- Create and manage bug bounty targets (scope + reward range)
- Submit findings with severity, status, and notes
- Dashboard with quick statistics and tables
- SQLite storage with automatic schema initialization

## Run locally
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000.

## Data model
- `targets`: program name, scope, min/max reward, created timestamp
- `findings`: linked target, title, severity, status, submitted timestamp, notes
