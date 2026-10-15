import os
import io
import csv
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .db import init_db, get_connection, DB_DIR
from .categorizer import categorizer, CATEGORIES
from .parser import parse_statement
from .sample_data import generate_sample_statements

app = FastAPI(
    title="Automated Expense Categorization & Spending Analysis Platform",
    description="Minor Project by Pratyush (B.Com) & Komalpreet Kaur (BCA) - PCTE",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Database and Sample files on startup
@app.on_event("startup")
def startup_event():
    init_db()
    generate_sample_statements(DB_DIR)

# Models
class ManualTransaction(BaseModel):
    date: str
    description: str
    amount: float
    type: str = "DEBIT"
    category: Optional[str] = None
    account: Optional[str] = "Manual Entry"

class CategoryUpdate(BaseModel):
    category: str
    apply_to_future: bool = True

class BudgetUpdate(BaseModel):
    category: str
    monthly_limit: float

# Routes
@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "project": "Automated Expense Categorization & Spending Analysis Platform",
        "team": "Pratyush (B.Com 3B) & Komalpreet Kaur (BCA 3B)",
        "institution": "Punjab College of Technical Education (PCTE)",
        "categories_count": len(CATEGORIES)
    }

@app.get("/api/categories")
def get_categories():
    return {"categories": CATEGORIES}

@app.get("/api/predict")
def predict_category(text: str, amount: float = 0.0, type: str = "DEBIT"):
    category, confidence, merchant = categorizer.categorize(text, amount, type)
    return {
        "text": text,
        "clean_merchant": merchant,
        "category": category,
        "confidence": confidence
    }

@app.get("/api/transactions")
def get_transactions(
    category: Optional[str] = None,
    txn_type: Optional[str] = None,
    search: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    account: Optional[str] = None,
    limit: int = 200,
    offset: int = 0
):
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM transactions WHERE 1=1"
    params = []
    
    if category and category != "All":
        query += " AND category = ?"
        params.append(category)
        
    if txn_type and txn_type != "ALL":
        query += " AND type = ?"
        params.append(txn_type.upper())
        
    if search:
        query += " AND (raw_description LIKE ? OR clean_merchant LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term])
        
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
        
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
        
    if account and account != "All":
        query += " AND account = ?"
        params.append(account)
        
    query += " ORDER BY date DESC, id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    
    # Get total count for pagination
    count_query = "SELECT COUNT(*) as total FROM transactions"
    cursor.execute(count_query)
    total_count = cursor.fetchone()["total"]
    
    conn.close()
    return {"transactions": rows, "total": total_count}

@app.post("/api/transactions")
def add_transaction(item: ManualTransaction):
    if not item.description or item.amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid description or amount")
        
    if item.category and item.category in CATEGORIES:
        category = item.category
        confidence = 1.0
        _, merchant = categorizer.clean_text(item.description)
    else:
        category, confidence, merchant = categorizer.categorize(item.description, item.amount, item.type)
        
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transactions (date, raw_description, clean_merchant, amount, type, category, confidence, source, account)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'MANUAL', ?)
    """, (item.date, item.description, merchant, item.amount, item.type.upper(), category, confidence, item.account or "Manual Entry"))
    
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    
    return {"status": "success", "id": new_id, "category": category, "merchant": merchant}

@app.put("/api/transactions/{txn_id}/category")
def update_transaction_category(txn_id: int, payload: CategoryUpdate):
    if payload.category not in CATEGORIES:
        raise HTTPException(status_code=400, detail="Invalid category")
        
    conn = get_connection()
    cursor = conn.cursor()
    
    # Fetch transaction
    cursor.execute("SELECT clean_merchant FROM transactions WHERE id = ?", (txn_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    merchant = row["clean_merchant"]
    
    # Update transaction
    cursor.execute("UPDATE transactions SET category = ?, confidence = 1.0 WHERE id = ?", (payload.category, txn_id))
    
    # If active learning is requested, save merchant override
    if payload.apply_to_future and merchant and len(merchant) > 2:
        cursor.execute("""
            INSERT OR REPLACE INTO category_overrides (merchant_pattern, category, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (merchant.lower(), payload.category))
        
        # Also update other existing transactions with same merchant
        cursor.execute("UPDATE transactions SET category = ?, confidence = 1.0 WHERE LOWER(clean_merchant) = ?", (payload.category, merchant.lower()))

    conn.commit()
    conn.close()
    return {"status": "success", "category": payload.category}

@app.delete("/api/transactions/{txn_id}")
def delete_transaction(txn_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ?", (txn_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.delete("/api/transactions")
def clear_all_transactions():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions")
    conn.commit()
    conn.close()
    return {"status": "success", "message": "All transactions cleared"}

@app.post("/api/upload")
async def upload_statement(
    file: UploadFile = File(...),
    account_name: Optional[str] = Form("Uploaded Statement")
):
    try:
        contents = await file.read()
        parsed = parse_statement(contents, file.filename, account_name or "Uploaded Statement")
        
        if not parsed:
            raise HTTPException(status_code=400, detail="No valid transactions found in file.")
            
        conn = get_connection()
        cursor = conn.cursor()
        
        inserted = 0
        for txn in parsed:
            cursor.execute("""
                INSERT INTO transactions (date, raw_description, clean_merchant, amount, type, category, confidence, source, account)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                txn["date"], txn["raw_description"], txn["clean_merchant"],
                txn["amount"], txn["type"], txn["category"],
                txn["confidence"], txn["source"], txn["account"]
            ))
            inserted += 1
            
        conn.commit()
        conn.close()
        
        return {
            "status": "success",
            "filename": file.filename,
            "count": inserted,
            "message": f"Successfully parsed and categorized {inserted} transactions."
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process statement: {str(e)}")

@app.post("/api/load-sample/{sample_type}")
def load_sample_dataset(sample_type: str):
    file_map = {
        "hdfc": ("hdfc_statement_sample.csv", "HDFC Savings Account"),
        "sbi": ("sbi_upi_sample.csv", "SBI UPI Passbook"),
        "icici": ("icici_card_sample.csv", "ICICI Coral Card"),
    }
    
    if sample_type not in file_map and sample_type != "all":
        raise HTTPException(status_code=404, detail="Sample dataset not found")

    targets = [file_map[sample_type]] if sample_type != "all" else list(file_map.values())
    total_loaded = 0
    
    conn = get_connection()
    cursor = conn.cursor()
    
    for filename, account_name in targets:
        filepath = os.path.join(DB_DIR, filename)
        if not os.path.exists(filepath):
            generate_sample_statements(DB_DIR)
            
        with open(filepath, "rb") as f:
            bytes_data = f.read()
            txns = parse_statement(bytes_data, filename, account_name)
            for txn in txns:
                cursor.execute("""
                    INSERT INTO transactions (date, raw_description, clean_merchant, amount, type, category, confidence, source, account)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    txn["date"], txn["raw_description"], txn["clean_merchant"],
                    txn["amount"], txn["type"], txn["category"],
                    txn["confidence"], "SAMPLE", account_name
                ))
                total_loaded += 1
                
    conn.commit()
    conn.close()
    
    return {
        "status": "success",
        "loaded_count": total_loaded,
        "message": f"Successfully loaded {total_loaded} sample transactions."
    }

@app.get("/api/analytics")
def get_analytics():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. KPI Totals
    cursor.execute("""
        SELECT 
            COALESCE(SUM(CASE WHEN type = 'CREDIT' THEN amount ELSE 0 END), 0) as total_income,
            COALESCE(SUM(CASE WHEN type = 'DEBIT' THEN amount ELSE 0 END), 0) as total_expense,
            COUNT(*) as total_txns
        FROM transactions
    """)
    kpi = dict(cursor.fetchone())
    total_income = round(kpi["total_income"], 2)
    total_expense = round(kpi["total_expense"], 2)
    net_savings = round(total_income - total_expense, 2)
    savings_rate = round((net_savings / total_income * 100), 1) if total_income > 0 else 0.0

    # 2. Category Breakdown (Expenses only)
    cursor.execute("""
        SELECT 
            category,
            ROUND(SUM(amount), 2) as total_amount,
            COUNT(*) as count
        FROM transactions
        WHERE type = 'DEBIT'
        GROUP BY category
        ORDER BY total_amount DESC
    """)
    category_rows = [dict(r) for r in cursor.fetchall()]
    
    # Compute percentages
    for r in category_rows:
        r["percentage"] = round((r["total_amount"] / total_expense * 100), 1) if total_expense > 0 else 0.0

    # 3. Monthly Spend Trend
    cursor.execute("""
        SELECT 
            strftime('%Y-%m', date) as month,
            ROUND(SUM(CASE WHEN type = 'CREDIT' THEN amount ELSE 0 END), 2) as income,
            ROUND(SUM(CASE WHEN type = 'DEBIT' THEN amount ELSE 0 END), 2) as expense
        FROM transactions
        GROUP BY month
        ORDER BY month ASC
    """)
    monthly_trend = [dict(r) for r in cursor.fetchall()]

    # 4. Top Merchants by Spending
    cursor.execute("""
        SELECT 
            clean_merchant as merchant,
            category,
            ROUND(SUM(amount), 2) as total_spent,
            COUNT(*) as txn_count
        FROM transactions
        WHERE type = 'DEBIT'
        GROUP BY clean_merchant
        ORDER BY total_spent DESC
        LIMIT 6
    """)
    top_merchants = [dict(r) for r in cursor.fetchall()]

    # 5. Budgets vs Actuals
    cursor.execute("SELECT * FROM budgets")
    budgets_dict = {b["category"]: b["monthly_limit"] for b in cursor.fetchall()}
    
    budget_analysis = []
    # Current month expenses per category
    cursor.execute("""
        SELECT 
            category,
            ROUND(SUM(amount), 2) as spent
        FROM transactions
        WHERE type = 'DEBIT'
        GROUP BY category
    """)
    spent_map = {row["category"]: row["spent"] for row in cursor.fetchall()}
    
    for cat in CATEGORIES:
        if cat == "Income & Salary":
            continue
        limit = budgets_dict.get(cat, 5000.0)
        spent = spent_map.get(cat, 0.0)
        pct = round((spent / limit * 100), 1) if limit > 0 else 0.0
        
        status = "SAFE"
        if pct >= 100:
            status = "EXCEEDED"
        elif pct >= 80:
            status = "WARNING"
            
        budget_analysis.append({
            "category": cat,
            "monthly_limit": limit,
            "spent": spent,
            "percentage": pct,
            "remaining": max(0.0, round(limit - spent, 2)),
            "status": status
        })

    conn.close()

    return {
        "kpis": {
            "total_income": total_income,
            "total_expense": total_expense,
            "net_savings": net_savings,
            "savings_rate": savings_rate,
            "total_txns": kpi["total_txns"]
        },
        "category_breakdown": category_rows,
        "monthly_trend": monthly_trend,
        "top_merchants": top_merchants,
        "budget_analysis": budget_analysis
    }

@app.get("/api/budgets")
def get_budgets():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM budgets ORDER BY monthly_limit DESC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"budgets": rows}

@app.put("/api/budgets")
def update_budget(item: BudgetUpdate):
    if item.monthly_limit < 0:
        raise HTTPException(status_code=400, detail="Budget limit cannot be negative")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO budgets (category, monthly_limit)
        VALUES (?, ?)
    """, (item.category, item.monthly_limit))
    conn.commit()
    conn.close()
    return {"status": "success", "category": item.category, "monthly_limit": item.monthly_limit}

@app.get("/api/export")
def export_transactions_csv():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT date, raw_description, clean_merchant, amount, type, category, confidence, account FROM transactions ORDER BY date DESC")
    rows = cursor.fetchall()
    conn.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date", "Description", "Clean Merchant", "Amount (INR)", "Type", "Category", "Confidence", "Account"])
    for r in rows:
        writer.writerow([r[0], r[1], r[2], r[3], r[4], r[5], f"{int(r[6]*100)}%", r[7]])
        
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=Expense_Analysis_Report.csv"}
    )

# Static files for the Web UI
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
def serve_index():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Expense Categorization Platform API is online. Frontend loading..."}
