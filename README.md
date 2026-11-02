# AI Money Coach 💰

A personal finance tracking MVP built with Streamlit, SQLite, Pandas and Plotly.

## Features
- Dashboard with balance, income and expense summaries
- Add, filter, delete and export transactions
- Monthly category budgets with over-budget warnings
- Spending analytics
- Local SQLite storage (no bank connection or cloud sync)

## Run locally
```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## Data and privacy
Transactions are stored in `money_coach.db` beside the app. Do not commit this file or enter sensitive account credentials. The public demo should use fictional sample data only.

## Disclaimer
For personal tracking and educational purposes only. Not financial, tax or investment advice.
