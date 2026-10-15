import sqlite3
import os
from typing import List, Dict, Any, Optional

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "expenses.db")

def init_db():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Transactions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        raw_description TEXT NOT NULL,
        clean_merchant TEXT NOT NULL,
        amount REAL NOT NULL,
        type TEXT NOT NULL DEFAULT 'DEBIT',
        category TEXT NOT NULL,
        confidence REAL DEFAULT 1.0,
        source TEXT DEFAULT 'MANUAL',
        account TEXT DEFAULT 'Default Account',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Category Budgets table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS budgets (
        category TEXT PRIMARY KEY,
        monthly_limit REAL NOT NULL,
        period TEXT DEFAULT 'MONTHLY'
    )
    """)
    
    # User-defined Category Overrides (Active Learning memory)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS category_overrides (
        merchant_pattern TEXT PRIMARY KEY,
        category TEXT NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Initialize default budgets if empty
    cursor.execute("SELECT COUNT(*) FROM budgets")
    if cursor.fetchone()[0] == 0:
        default_budgets = [
            ("Food & Dining", 8000.0),
            ("Groceries & Essentials", 6000.0),
            ("Shopping & E-Commerce", 5000.0),
            ("Travel & Commute", 4000.0),
            ("Utilities & Bills", 4500.0),
            ("Entertainment & Subscriptions", 2000.0),
            ("Healthcare & Medical", 3000.0),
            ("Investments & Savings", 10000.0),
            ("Miscellaneous & Transfers", 3000.0)
        ]
        cursor.executemany("INSERT INTO budgets (category, monthly_limit) VALUES (?, ?)", default_budgets)
        
    conn.commit()
    conn.close()

def get_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
