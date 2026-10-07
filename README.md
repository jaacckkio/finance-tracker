# Personal Finance Tracker

A command-line application for tracking personal income and expenses with category-based analysis and data visualisation.

## Features

- **Transaction tracking** — Log income and expenses with categories, descriptions and dates
- **Budget management** — Set monthly spending limits per category with progress bars
- **Monthly summaries** — View income, expenses and net savings with category breakdowns
- **Annual reports** — Year-at-a-glance income vs expense comparison
- **Data visualisation** — Pie charts, bar charts and cumulative savings graphs via Matplotlib
- **SQLite storage** — Persistent local database, no account or cloud needed

## Usage

```bash
# Run the tracker
python finance_tracker.py

# Generate charts
python visualise.py
```

## Requirements

- Python 3.8+
- matplotlib (for visualisations only)

```bash
pip install matplotlib
```

## Tech Stack

- **Python** — Core application logic
- **SQLite** — Persistent data storage
- **Matplotlib** — Data visualisation and charting

## Screenshots

Run `visualise.py` to generate:
- `expense_breakdown.png` — Pie chart of spending by category
- `monthly_trend.png` — Bar chart of income vs expenses by month
- `savings_trend.png` — Cumulative savings line chart
