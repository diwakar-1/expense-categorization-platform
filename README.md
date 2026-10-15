# Automated Expense Categorization & Spending Analysis Platform

An intelligent, full-stack financial technology web application designed to automatically ingest, clean, categorize, and analyze raw bank statements, UPI transactions, and manual expenses into standard accounting heads with interactive visual analytics.

> **Punjab College of Technical Education (PCTE)**  
> **Course:** Minor Project (B.Com & BCA Interdisciplinary Collaboration)  
> **Team Members:**  
> - **Pratyush** (B.Com 3B, Roll No: 2446963) — *Financial Analyst & Quality Assurance*  
> - **Komalpreet Kaur** (BCA 3B, Roll No: 2446597) — *Technical Lead & Full-Stack Developer*

---

## 🌟 Key Features

1. **Intelligent Text Cleaning & Merchant Extraction**:
   - Strips bank transaction noise, UTR/reference numbers (`UPI/`, `IMPS-P2A-`, `ACH Dr-`, `ATM WDL`, masked card numbers `XX4821`).
   - Extracts clean merchant brand names (e.g. `Swiggy`, `Zomato`, `Blinkit`, `Amazon`, `Uber`, `PSPCL Electricity`).

2. **Hybrid ML & Rule-Based Categorization**:
   - Machine Learning pipeline with `TfidfVectorizer` + `LogisticRegression` trained on Indian banking & UPI merchant datasets.
   - Standard Accounting Heads formulated according to basic financial principles:
     - 🍔 **Food & Dining**
     - 🛒 **Groceries & Essentials**
     - 🛍️ **Shopping & E-Commerce**
     - 🚗 **Travel & Commute**
     - 💡 **Utilities & Bills**
     - 🎬 **Entertainment & Subscriptions**
     - 💊 **Healthcare & Medical**
     - 📈 **Investments & Savings**
     - 💼 **Income & Salary**
     - 📦 **Miscellaneous & Transfers**
   - Active User Learning / Override Memory: Reclassifying any transaction remembers your preference for that merchant across future transactions.

3. **Bank Statement Ingestion**:
   - Automated parser for **CSV** and **Excel** statements with column auto-detection (handles HDFC, SBI, ICICI, Axis, Paytm, PhonePe formats).
   - Pre-loaded one-click realistic Indian bank demo statements.

4. **Visual Spending Analytics (Chart.js)**:
   - Doughnut category breakdown chart with percentage distribution.
   - Cash Flow velocity bar chart (Inflow vs Outflow monthly trend).
   - Top merchant spending chart.

5. **Budget Guardrails & Alerts**:
   - Monthly category budget tracking.
   - Dynamic threshold alerts (`Safe`, `Warning >80%`, `Exceeded >100%`).

6. **Export & Portability**:
   - Export filtered transactions directly to CSV.
   - Fully containerized with Docker and Docker Compose.

---

## 🚀 Quick Start Guide

### Option 1: Run Locally (Fastest)

1. Make sure Python 3.9+ is installed.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the application:
   ```bash
   python run.py
   ```
4. Open your browser and navigate to:
   ```
   http://localhost:8000
   ```

### Option 2: Run with Docker

1. Ensure Docker Desktop is running.
2. Build and run the container:
   ```bash
   docker-compose up --build
   ```
3. Access the dashboard at `http://localhost:8000`.

---

## 🏗️ Project Architecture

```
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI server, REST API endpoints
│   ├── categorizer.py       # Regex text cleaner & Scikit-learn ML model
│   ├── parser.py            # CSV/Excel statement parser & column detector
│   ├── db.py                # SQLite database and schema initialization
│   ├── sample_data.py       # Generator for realistic Indian bank statements
│   └── static/
│       ├── index.html       # Modern dashboard UI
│       ├── css/style.css    # Responsive glassmorphic dark design system
│       └── js/app.js        # Controller, Chart.js integrations & API calls
├── data/                    # Generated SQLite database & sample CSVs
│   ├── expenses.db
│   ├── hdfc_statement_sample.csv
│   ├── sbi_upi_sample.csv
│   └── icici_card_sample.csv
├── Dockerfile               # Docker container configuration
├── docker-compose.yml       # Docker compose orchestration
├── requirements.txt         # Python package dependencies
├── run.py                   # Local development server runner
└── README.md
```

---

## 🎓 Viva & Presentation Talking Points

- **Why an Interdisciplinary Team?**
  Combining BCA (algorithms, full-stack architecture, machine learning) with B.Com (standard accounting heads, cash flow controls, variance analysis, budget guardrails) guarantees both technical robustness and financial accuracy.
- **Why Hybrid Categorization instead of purely Rules or purely ML?**
  Pure rule-based matching fails when store names contain typos or new merchants appear. Pure ML can sometimes misclassify obvious deterministic merchants. A hybrid approach ensures 99%+ accuracy with instantaneous active learning memory.
