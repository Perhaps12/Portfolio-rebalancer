# Stock Portfolio Rebalancer

A lightweight portfolio tool for reviewing allocations, testing target rebalances, and asking portfolio-related questions through a specialist agent workflow.

## Overview

Once a portfolio is oaded, the app shows two main pages:

- Rebalancing calculator: review current asset allocation and generate target-based trade suggestions.
- Portfolio advice: ask natural-language questions and receive a response assembled from multiple specialist agents.

The tool supports both manual entry and CSV upload. Portfolio data is stored by user ID in SQLite.

## Features

- Manual stock entry or CSV upload
- Asset-class allocation analysis
- Rebalancing suggestions across multiple strategies
- Natural-language portfolio Q&A routed through specialist agents
- Persistent storage by user ID

CSV files should include these headers:
- symbol
- quantity
- avg_cost
- sector
- asset_class

## How to use

### Initial setup

From the project root, create and activate a virtual environment if needed, then install the dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### Start the app

The easiest option on Windows is to double-click `start_app.bat` or run it from PowerShell:

```powershell
.\start_app.bat
```

This opens two terminal windows and starts both services:

- FastAPI backend at `http://127.0.0.1:8000`
- Streamlit frontend at the local URL shown in its terminal, usually `http://localhost:8501`

To start the services manually, use two terminals from the project root:

```powershell
# Terminal 1
.\.venv\Scripts\python.exe -m uvicorn backend.backend:app --reload

# Terminal 2
.\.venv\Scripts\python.exe -m streamlit run frontend\frontend.py
```

Open the Streamlit URL, enter a user ID, and begin adding or uploading portfolio data.

Once a portfolio exists, the app will show the main pages for allocation analysis and portfolio advice.

The database file at the project root, portfolio.db, already includes sample data for testing. Delete it to reset the database.

Sample CSV files are available under the sample_data/sample_data folder.

## Notes

- User ID 0 is intended for temporary testing and doesn't save any values beyond the current user session
- Other user IDs persist data across sessions.
- The advisor page uses a specialist-agent setup, with the supervisor routing questions to the most relevant agent.
