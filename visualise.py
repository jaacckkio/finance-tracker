#!/usr/bin/env python3
"""Generate charts from finance tracker data using Matplotlib."""

import sqlite3
import os
import sys
from datetime import datetime
from collections import defaultdict

try:
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
except ImportError:
    print("matplotlib is required: pip install matplotlib")
    sys.exit(1)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "finance.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def expense_pie_chart(year=None, month=None):
    """Pie chart of expenses by category for a given month."""
    now = datetime.now()
    year = year or now.year
    month = month or now.month

    start = f"{year}-{month:02d}-01"
    end = f"{year}-{month + 1:02d}-01" if month < 12 else f"{year + 1}-01-01"

    conn = get_db()
    rows = conn.execute(
        "SELECT category, SUM(amount) as total FROM transactions "
        "WHERE type = 'expense' AND date >= ? AND date < ? "
        "GROUP BY category ORDER BY total DESC",
        (start, end),
    ).fetchall()
    conn.close()

    if not rows:
        print("No expense data for this period.")
        return

    categories = [r["category"] for r in rows]
    amounts = [r["total"] for r in rows]

    fig, ax = plt.subplots(figsize=(8, 6))
    colours = plt.cm.Set3(range(len(categories)))
    wedges, texts, autotexts = ax.pie(
        amounts,
        labels=categories,
        autopct=lambda p: f"£{p * sum(amounts) / 100:.0f}",
        colors=colours,
        startangle=140,
    )
    for t in autotexts:
        t.set_fontsize(9)

    month_name = datetime(year, month, 1).strftime("%B %Y")
    ax.set_title(f"Expenses by Category — {month_name}", fontweight="bold", pad=20)
    plt.tight_layout()
    plt.savefig("expense_breakdown.png", dpi=150)
    plt.show()
    print("Saved: expense_breakdown.png")


def monthly_trend(year=None):
    """Bar chart comparing income vs expenses month by month."""
    year = year or datetime.now().year

    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM transactions WHERE date >= ? AND date < ?",
        (f"{year}-01-01", f"{year + 1}-01-01"),
    ).fetchall()
    conn.close()

    if not rows:
        print("No data for this year.")
        return

    income_by_month = defaultdict(float)
    expense_by_month = defaultdict(float)

    for r in rows:
        m = int(r["date"].split("-")[1])
        if r["type"] == "income":
            income_by_month[m] += r["amount"]
        else:
            expense_by_month[m] += r["amount"]

    months_present = sorted(set(list(income_by_month.keys()) + list(expense_by_month.keys())))
    month_labels = [datetime(year, m, 1).strftime("%b") for m in months_present]
    income_vals = [income_by_month.get(m, 0) for m in months_present]
    expense_vals = [expense_by_month.get(m, 0) for m in months_present]

    x = range(len(months_present))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar([i - width / 2 for i in x], income_vals, width, label="Income", color="#2ecc71")
    ax.bar([i + width / 2 for i in x], expense_vals, width, label="Expenses", color="#e74c3c")

    ax.set_xticks(list(x))
    ax.set_xticklabels(month_labels)
    ax.set_ylabel("Amount (£)")
    ax.set_title(f"Income vs Expenses — {year}", fontweight="bold")
    ax.legend()
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"£{v:,.0f}"))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.savefig("monthly_trend.png", dpi=150)
    plt.show()
    print("Saved: monthly_trend.png")


def savings_over_time(year=None):
    """Line chart showing cumulative savings throughout the year."""
    year = year or datetime.now().year

    conn = get_db()
    rows = conn.execute(
        "SELECT date, type, amount FROM transactions WHERE date >= ? AND date < ? ORDER BY date",
        (f"{year}-01-01", f"{year + 1}-01-01"),
    ).fetchall()
    conn.close()

    if not rows:
        print("No data for this year.")
        return

    cumulative = []
    running = 0.0
    dates = []
    for r in rows:
        if r["type"] == "income":
            running += r["amount"]
        else:
            running -= r["amount"]
        dates.append(datetime.strptime(r["date"], "%Y-%m-%d"))
        cumulative.append(running)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(dates, cumulative, color="#3498db", linewidth=2)
    ax.fill_between(dates, cumulative, alpha=0.1, color="#3498db")
    ax.axhline(y=0, color="#999", linewidth=0.5, linestyle="--")
    ax.set_ylabel("Cumulative Savings (£)")
    ax.set_title(f"Savings Over Time — {year}", fontweight="bold")
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda v, _: f"£{v:,.0f}"))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    plt.savefig("savings_trend.png", dpi=150)
    plt.show()
    print("Saved: savings_trend.png")


if __name__ == "__main__":
    print("\nFinance Tracker — Visualisations")
    print("  1. Expense breakdown (pie chart)")
    print("  2. Monthly income vs expenses (bar chart)")
    print("  3. Cumulative savings (line chart)")

    choice = input("\n> ").strip()
    if choice == "1":
        expense_pie_chart()
    elif choice == "2":
        monthly_trend()
    elif choice == "3":
        savings_over_time()
    else:
        print("Invalid choice.")
