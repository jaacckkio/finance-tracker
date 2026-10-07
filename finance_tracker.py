#!/usr/bin/env python3
"""Personal Finance Tracker — CLI app for tracking income and expenses."""

import sqlite3
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "finance.db")

EXPENSE_CATEGORIES = [
    "Food & Drink",
    "Transport",
    "Entertainment",
    "Shopping",
    "Bills & Utilities",
    "Rent",
    "Education",
    "Health",
    "Other",
]

INCOME_CATEGORIES = [
    "Salary",
    "Freelance",
    "Gifts",
    "Refunds",
    "Other",
]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
            amount REAL NOT NULL CHECK(amount > 0),
            category TEXT NOT NULL,
            description TEXT,
            date TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL UNIQUE,
            monthly_limit REAL NOT NULL CHECK(monthly_limit > 0)
        );
    """)
    conn.commit()
    conn.close()


def add_transaction(tx_type, amount, category, description="", date=None):
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    conn = get_db()
    conn.execute(
        "INSERT INTO transactions (type, amount, category, description, date) VALUES (?, ?, ?, ?, ?)",
        (tx_type, amount, category, description, date),
    )
    conn.commit()
    conn.close()
    print(f"  ✓ Added {tx_type}: £{amount:.2f} [{category}]")


def list_transactions(limit=20, tx_type=None):
    conn = get_db()
    query = "SELECT * FROM transactions"
    params = []
    if tx_type:
        query += " WHERE type = ?"
        params.append(tx_type)
    query += " ORDER BY date DESC, id DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()

    if not rows:
        print("  No transactions found.")
        return

    print(f"\n  {'Date':<12} {'Type':<9} {'Amount':>9}  {'Category':<18} {'Description'}")
    print("  " + "-" * 75)
    for r in rows:
        sign = "+" if r["type"] == "income" else "-"
        print(
            f"  {r['date']:<12} {r['type']:<9} {sign}£{r['amount']:>7.2f}  {r['category']:<18} {r['description'] or ''}"
        )


def delete_transaction(tx_id):
    conn = get_db()
    cursor = conn.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
    conn.commit()
    conn.close()
    if cursor.rowcount:
        print(f"  ✓ Deleted transaction #{tx_id}")
    else:
        print(f"  Transaction #{tx_id} not found.")


def monthly_summary(year=None, month=None):
    now = datetime.now()
    if year is None:
        year = now.year
    if month is None:
        month = now.month

    start = f"{year}-{month:02d}-01"
    if month == 12:
        end = f"{year + 1}-01-01"
    else:
        end = f"{year}-{month + 1:02d}-01"

    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM transactions WHERE date >= ? AND date < ? ORDER BY date",
        (start, end),
    ).fetchall()
    conn.close()

    income_total = 0.0
    expense_total = 0.0
    by_category = defaultdict(float)

    for r in rows:
        if r["type"] == "income":
            income_total += r["amount"]
        else:
            expense_total += r["amount"]
            by_category[r["category"]] += r["amount"]

    month_name = datetime(year, month, 1).strftime("%B %Y")
    print(f"\n  === {month_name} Summary ===")
    print(f"  Income:   £{income_total:>9.2f}")
    print(f"  Expenses: £{expense_total:>9.2f}")
    print(f"  Net:      £{income_total - expense_total:>9.2f}")

    if by_category:
        print(f"\n  Expenses by category:")
        for cat, total in sorted(by_category.items(), key=lambda x: -x[1]):
            bar = "█" * int(total / max(by_category.values()) * 20)
            print(f"    {cat:<18} £{total:>8.2f}  {bar}")

    return income_total, expense_total, by_category


def set_budget(category, limit_amount):
    conn = get_db()
    conn.execute(
        "INSERT INTO budgets (category, monthly_limit) VALUES (?, ?) "
        "ON CONFLICT(category) DO UPDATE SET monthly_limit = ?",
        (category, limit_amount, limit_amount),
    )
    conn.commit()
    conn.close()
    print(f"  ✓ Budget set: {category} → £{limit_amount:.2f}/month")


def check_budgets(year=None, month=None):
    now = datetime.now()
    if year is None:
        year = now.year
    if month is None:
        month = now.month

    start = f"{year}-{month:02d}-01"
    if month == 12:
        end = f"{year + 1}-01-01"
    else:
        end = f"{year}-{month + 1:02d}-01"

    conn = get_db()
    budgets = conn.execute("SELECT * FROM budgets").fetchall()
    if not budgets:
        print("  No budgets set. Use 'budget' to set one.")
        conn.close()
        return

    print(f"\n  === Budget Status ({datetime(year, month, 1).strftime('%B %Y')}) ===")
    for b in budgets:
        spent_row = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) as total FROM transactions "
            "WHERE type = 'expense' AND category = ? AND date >= ? AND date < ?",
            (b["category"], start, end),
        ).fetchone()
        spent = spent_row["total"]
        limit_val = b["monthly_limit"]
        pct = (spent / limit_val) * 100 if limit_val > 0 else 0
        status = "⚠️  OVER" if pct > 100 else "✓"
        bar_len = min(int(pct / 5), 20)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        print(
            f"  {b['category']:<18} £{spent:>7.2f} / £{limit_val:>7.2f}  [{bar}] {pct:.0f}% {status}"
        )
    conn.close()


def annual_report(year=None):
    if year is None:
        year = datetime.now().year

    print(f"\n  === {year} Annual Report ===\n")

    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM transactions WHERE date >= ? AND date < ?",
        (f"{year}-01-01", f"{year + 1}-01-01"),
    ).fetchall()
    conn.close()

    if not rows:
        print("  No transactions found for this year.")
        return

    monthly_income = defaultdict(float)
    monthly_expense = defaultdict(float)

    for r in rows:
        month = int(r["date"].split("-")[1])
        if r["type"] == "income":
            monthly_income[month] += r["amount"]
        else:
            monthly_expense[month] += r["amount"]

    print(f"  {'Month':<12} {'Income':>10} {'Expenses':>10} {'Net':>10}")
    print("  " + "-" * 45)

    total_in = 0.0
    total_out = 0.0
    for m in range(1, 13):
        inc = monthly_income.get(m, 0)
        exp = monthly_expense.get(m, 0)
        if inc == 0 and exp == 0:
            continue
        total_in += inc
        total_out += exp
        name = datetime(year, m, 1).strftime("%b")
        print(f"  {name:<12} £{inc:>9.2f} £{exp:>9.2f} £{inc - exp:>9.2f}")

    print("  " + "-" * 45)
    print(f"  {'Total':<12} £{total_in:>9.2f} £{total_out:>9.2f} £{total_in - total_out:>9.2f}")


def pick_option(prompt, options):
    print(f"\n  {prompt}")
    for i, opt in enumerate(options, 1):
        print(f"    {i}. {opt}")
    while True:
        try:
            choice = int(input("  > "))
            if 1 <= choice <= len(options):
                return options[choice - 1]
        except (ValueError, EOFError):
            pass
        print("  Invalid choice, try again.")


def input_amount(prompt="  Amount (£): "):
    while True:
        try:
            val = float(input(prompt))
            if val > 0:
                return val
            print("  Must be positive.")
        except (ValueError, EOFError):
            print("  Enter a number.")


def main():
    init_db()

    commands = {
        "1": "Add expense",
        "2": "Add income",
        "3": "View transactions",
        "4": "Monthly summary",
        "5": "Annual report",
        "6": "Set budget",
        "7": "Check budgets",
        "8": "Delete transaction",
        "9": "Exit",
    }

    print("\n  ╔══════════════════════════════╗")
    print("  ║   Personal Finance Tracker   ║")
    print("  ╚══════════════════════════════╝")

    while True:
        print("\n  What would you like to do?")
        for k, v in commands.items():
            print(f"    {k}. {v}")

        choice = input("\n  > ").strip()

        if choice == "1":
            cat = pick_option("Category:", EXPENSE_CATEGORIES)
            amount = input_amount()
            desc = input("  Description (optional): ").strip()
            date_str = input("  Date (YYYY-MM-DD, Enter for today): ").strip() or None
            add_transaction("expense", amount, cat, desc, date_str)

        elif choice == "2":
            cat = pick_option("Category:", INCOME_CATEGORIES)
            amount = input_amount()
            desc = input("  Description (optional): ").strip()
            date_str = input("  Date (YYYY-MM-DD, Enter for today): ").strip() or None
            add_transaction("income", amount, cat, desc, date_str)

        elif choice == "3":
            list_transactions()

        elif choice == "4":
            monthly_summary()

        elif choice == "5":
            annual_report()

        elif choice == "6":
            cat = pick_option("Set budget for:", EXPENSE_CATEGORIES)
            limit_val = input_amount("  Monthly limit (£): ")
            set_budget(cat, limit_val)

        elif choice == "7":
            check_budgets()

        elif choice == "8":
            list_transactions(10)
            try:
                tx_id = int(input("\n  Transaction ID to delete: "))
                delete_transaction(tx_id)
            except (ValueError, EOFError):
                print("  Cancelled.")

        elif choice == "9":
            print("  Goodbye!")
            break

        else:
            print("  Invalid option.")


if __name__ == "__main__":
    main()
