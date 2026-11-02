
import sqlite3
from pathlib import Path
from datetime import date
import pandas as pd

DB_PATH = Path(__file__).with_name("money_coach.db")


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connect() as conn:
        # Existing transactions table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('Income','Expense')),
                category TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                note TEXT DEFAULT ''
            )
        """)

        # Keep the old budgets table for compatibility
        conn.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                category TEXT PRIMARY KEY,
                monthly_limit REAL NOT NULL CHECK(monthly_limit > 0)
            )
        """)

        # New customizable expense budgets
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expense_budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                monthly_limit REAL NOT NULL CHECK(monthly_limit > 0)
            )
        """)

        # Migrate old budgets into the new table
        conn.execute("""
            INSERT INTO expense_budgets (name, monthly_limit)
            SELECT category, monthly_limit
            FROM budgets
            WHERE NOT EXISTS (
                SELECT 1
                FROM expense_budgets
                WHERE expense_budgets.name = budgets.category
            )
        """)

        # New savings goals
        conn.execute("""
            CREATE TABLE IF NOT EXISTS savings_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                goal_type TEXT NOT NULL DEFAULT 'Personal',
                target_amount REAL NOT NULL CHECK(target_amount > 0),
                target_date TEXT DEFAULT ''
            )
        """)

        # Individual savings contributions
        conn.execute("""
            CREATE TABLE IF NOT EXISTS savings_contributions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER NOT NULL,
                contribution_date TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                note TEXT DEFAULT '',
                FOREIGN KEY (goal_id)
                    REFERENCES savings_goals(id)
                    ON DELETE CASCADE
            )
        """)


def add_transaction(tx_date, tx_type, category, amount, note=""):
    with connect() as conn:
        conn.execute(
            """INSERT INTO transactions
            (date, type, category, amount, note)
            VALUES (?, ?, ?, ?, ?)""",
            (tx_date, tx_type, category, amount, note)
        )


def get_transactions():
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM transactions ORDER BY date DESC, id DESC"
        ).fetchall()

    return pd.DataFrame(
        [dict(r) for r in rows],
        columns=["id", "date", "type", "category", "amount", "note"]
    )


def delete_transaction(tx_id):
    with connect() as conn:
        conn.execute(
            "DELETE FROM transactions WHERE id = ?",
            (tx_id,)
        )


# Old budget functions: kept for compatibility with the current app.py
def get_budgets():
    with connect() as conn:
        rows = conn.execute(
            "SELECT category, monthly_limit FROM budgets ORDER BY category"
        ).fetchall()

    return {
        r["category"]: r["monthly_limit"]
        for r in rows
    }


def set_budget(category, limit):
    with connect() as conn:
        conn.execute("""
            INSERT INTO budgets (category, monthly_limit)
            VALUES (?, ?)
            ON CONFLICT(category)
            DO UPDATE SET monthly_limit = excluded.monthly_limit
        """, (category, limit))


# New expense budget functions
def get_expense_budgets():
    with connect() as conn:
        rows = conn.execute("""
            SELECT id, name, monthly_limit
            FROM expense_budgets
            ORDER BY id
        """).fetchall()

    return pd.DataFrame(
        [dict(r) for r in rows],
        columns=["id", "name", "monthly_limit"]
    )


def add_expense_budget(name, monthly_limit):
    with connect() as conn:
        conn.execute("""
            INSERT INTO expense_budgets (name, monthly_limit)
            VALUES (?, ?)
        """, (name, monthly_limit))


def update_expense_budget(budget_id, name, monthly_limit):
    with connect() as conn:
        conn.execute("""
            UPDATE expense_budgets
            SET name = ?, monthly_limit = ?
            WHERE id = ?
        """, (name, monthly_limit, budget_id))


def delete_expense_budget(budget_id):
    with connect() as conn:
        conn.execute(
            "DELETE FROM expense_budgets WHERE id = ?",
            (budget_id,)
        )


# New savings goal functions
def add_savings_goal(
    name,
    goal_type,
    target_amount,
    target_date=""
):
    with connect() as conn:
        cursor = conn.execute("""
            INSERT INTO savings_goals
            (name, goal_type, target_amount, target_date)
            VALUES (?, ?, ?, ?)
        """, (name, goal_type, target_amount, target_date))

        return cursor.lastrowid


def get_savings_goals():
    with connect() as conn:
        rows = conn.execute("""
            SELECT
                g.id,
                g.name,
                g.goal_type,
                g.target_amount,
                g.target_date,
                COALESCE(SUM(c.amount), 0) AS saved_amount
            FROM savings_goals g
            LEFT JOIN savings_contributions c
                ON g.id = c.goal_id
            GROUP BY g.id
            ORDER BY g.id DESC
        """).fetchall()

    return pd.DataFrame(
        [dict(r) for r in rows],
        columns=[
            "id", "name", "goal_type",
            "target_amount", "target_date", "saved_amount"
        ]
    )


def update_savings_goal(
    goal_id,
    name,
    goal_type,
    target_amount,
    target_date=""
):
    with connect() as conn:
        conn.execute("""
            UPDATE savings_goals
            SET name = ?,
                goal_type = ?,
                target_amount = ?,
                target_date = ?
            WHERE id = ?
        """, (name, goal_type, target_amount, target_date, goal_id))


def delete_savings_goal(goal_id):
    with connect() as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            "DELETE FROM savings_goals WHERE id = ?",
            (goal_id,)
        )


# Savings contribution functions
def add_savings_contribution(
    goal_id,
    amount,
    contribution_date=None,
    note=""
):
    if contribution_date is None:
        contribution_date = date.today().isoformat()

    with connect() as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("""
            INSERT INTO savings_contributions
            (goal_id, contribution_date, amount, note)
            VALUES (?, ?, ?, ?)
        """, (goal_id, contribution_date, amount, note))


def get_savings_contributions(goal_id=None):
    with connect() as conn:
        if goal_id is None:
            rows = conn.execute("""
                SELECT c.*, g.name AS goal_name
                FROM savings_contributions c
                JOIN savings_goals g ON c.goal_id = g.id
                ORDER BY c.contribution_date DESC, c.id DESC
            """).fetchall()
        else:
            rows = conn.execute("""
                SELECT c.*, g.name AS goal_name
                FROM savings_contributions c
                JOIN savings_goals g ON c.goal_id = g.id
                WHERE c.goal_id = ?
                ORDER BY c.contribution_date DESC, c.id DESC
            """, (goal_id,)).fetchall()

    return pd.DataFrame(
        [dict(r) for r in rows],
        columns=[
            "id", "goal_id", "contribution_date",
            "amount", "note", "goal_name"
        ]
    )


def delete_savings_contribution(contribution_id):
    with connect() as conn:
        conn.execute(
            "DELETE FROM savings_contributions WHERE id = ?",
            (contribution_id,)
        )


def get_month_summary(month=None):
    """Return income, expenses and net balance for a given month."""
    if month is None:
        month = date.today().strftime("%Y-%m")

    with connect() as conn:
        row = conn.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN type = 'Income'
                    THEN amount ELSE 0 END), 0) AS income,
                COALESCE(SUM(CASE WHEN type = 'Expense'
                    THEN amount ELSE 0 END), 0) AS expenses
            FROM transactions
            WHERE date LIKE ?
        """, (f"{month}%",)).fetchone()

    income = float(row["income"])
    expenses = float(row["expenses"])

    return {
        "income": income,
        "expenses": expenses,
        "balance": income - expenses
    }


def seed_demo_data():
    with connect() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM transactions"
        ).fetchone()[0]

        if count:
            return

        samples = [
            ("2026-10-02", "Income", "Salary", 4800, "Example monthly salary"),
            ("2026-10-03", "Expense", "Food & Dining", 24.5, "Example lunch"),
            ("2026-10-05", "Expense", "Shopping", 68, "Example household items"),
            ("2026-10-07", "Expense", "Transport", 18, "Example transport"),
            ("2026-10-09", "Expense", "Bills", 85, "Example utilities"),
            ("2026-10-12", "Expense", "Entertainment", 32, "Example movie"),
        ]

        conn.executemany("""
            INSERT INTO transactions
            (date, type, category, amount, note)
            VALUES (?, ?, ?, ?, ?)
        """, samples)


def clear_all_data():
    # Preserve budgets and savings goals.
    # Only delete transaction records.
    with connect() as conn:
        conn.execute("DELETE FROM transactions")
