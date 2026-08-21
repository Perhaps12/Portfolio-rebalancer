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

1. Install the required Python dependencies:  
```bash
    pip install requirements.txt
```
2. Start the backend in one terminal:
```bash
   uvicorn backend.backend:app --reload
   ```
3. Start the frontend in a second terminal:
```bash
   streamlit run frontend/frontend.py
   ```
4. Open the local Streamlit URL, enter a user ID, and begin adding or uploading portfolio data.

Once a portfolio exists, the app will show the main pages for allocation analysis and portfolio advice.

The database file at the project root, portfolio.db, already includes sample data for testing. Delete it to reset the database.

Sample CSV files are available under the sample_data/sample_data folder.

## Notes

- User ID 0 is intended for temporary testing and doesn't save any values beyond the current user session
- Other user IDs persist data across sessions.
- The advisor page uses a specialist-agent setup, with the supervisor routing questions to the most relevant agent.
