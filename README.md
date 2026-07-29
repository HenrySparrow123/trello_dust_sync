## Overview

This repository contains an automated Python data pipeline designed to transform unstructured project management data from Trello into structured, LLM-optimized Markdown chunks, syncing them directly into a Dust Data Source. 

This infrastructure enables a downstream Dust AI Agent to act as an instant "Changelog Writer" and assist customer support teams with real-time deployment and release status queries.

## Full Technical Documentation
The comprehensive architectural write-up—including detailed data workflows, unit testing strategies, alternative approaches handled, and our Push API vs. Remote MCP Server trade-off analysis—is fully detailed in the accompanying document located in this directory: Dust - Assignment Henry Sparrow.pdf

---

## Getting Started (Local Setup)

### 1. Prerequisites
Copy `.env.example` to `.env` and fill in your credentials (Trello key/token/board ID, and Dust API key/workspace/space/data source IDs). The `.env` file is gitignored and never committed.

```bash
cp .env.example .env
```

### 2. Installation & Execution
Open your terminal, navigate to this project directory, and run the following commands to install dependencies and execute a manual sync sequence:

```bash
# Install required dependencies
pip3 install -r requirements.txt

# Run the pipeline data synchronization script
python3 trello_dust_sync.py
```

### 3. Enabling the Automation (Cron)
The script is designed to run as a stateless utility. To automate the sync on a recurring 1-minute block (as configured for this demo), you can apply the provided cron rule in crontab.txt to your system

