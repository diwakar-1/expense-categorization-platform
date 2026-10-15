import io
import re
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Tuple
from .categorizer import categorizer

def parse_date(date_val: Any) -> str:
    """Standardizes various date formats into ISO YYYY-MM-DD."""
    if pd.isna(date_val) or not date_val:
        return datetime.now().strftime("%Y-%m-%d")
    
    date_str = str(date_val).strip()
    
    # Try common bank date formats
    formats = [
        "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y",
        "%Y-%m-%d", "%Y/%m/%d",
        "%d %b %Y", "%d-%b-%Y", "%d %B %Y", "%d-%B-%Y",
        "%m/%d/%Y", "%m-%d-%Y"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str[:11].strip(), fmt).strftime("%Y-%m-%d")
        except Exception:
            continue
            
    # Fallback to dateutil or current date
    try:
        from dateutil import parser as dt_parser
        return dt_parser.parse(date_str).strftime("%Y-%m-%d")
    except Exception:
        return datetime.now().strftime("%Y-%m-%d")

def clean_amount(val: Any) -> float:
    """Parses currency strings like '₹ 1,450.50' or '1,450.00' to float."""
    if pd.isna(val) or val is None:
        return 0.0
    val_str = str(val).replace(',', '').replace('₹', '').replace('$', '').replace('Rs.', '').replace('INR', '').strip()
    try:
        return abs(float(val_str))
    except Exception:
        return 0.0

def detect_columns(df: pd.DataFrame) -> Dict[str, str]:
    """
    Intelligently maps varying bank statement column headers to standard fields:
    'date', 'description', 'debit', 'credit', 'amount', 'type'.
    """
    col_mapping = {}
    cols = [str(c).strip() for c in df.columns]
    cols_lower = [c.lower() for c in cols]
    
    # Match Date
    for i, col in enumerate(cols_lower):
        if any(term in col for term in ['date', 'txn date', 'transaction date', 'value date', 'posting']):
            col_mapping['date'] = cols[i]
            break
            
    # Match Description / Narration
    for i, col in enumerate(cols_lower):
        if any(term in col for term in ['narration', 'particulars', 'description', 'remarks', 'details', 'merchant']):
            col_mapping['description'] = cols[i]
            break
            
    # Match Debit / Withdrawal
    for i, col in enumerate(cols_lower):
        if any(term in col for term in ['debit', 'withdrawal', 'dr', 'expense', 'spent']):
            col_mapping['debit'] = cols[i]
            break
            
    # Match Credit / Deposit
    for i, col in enumerate(cols_lower):
        if any(term in col for term in ['credit', 'deposit', 'cr', 'income', 'received']):
            col_mapping['credit'] = cols[i]
            break

    # Match Single Amount column if separate debit/credit not found
    if 'debit' not in col_mapping and 'credit' not in col_mapping:
        for i, col in enumerate(cols_lower):
            if any(term in col for term in ['amount', 'txn amount', 'transaction amount']):
                col_mapping['amount'] = cols[i]
                break

    # Match Type column (DR/CR)
    for i, col in enumerate(cols_lower):
        if any(term == col for term in ['type', 'cr/dr', 'd/c', 'txn type']):
            col_mapping['type'] = cols[i]
            break

    return col_mapping

def parse_statement(file_bytes: bytes, filename: str, account_name: str = "Uploaded Statement") -> List[Dict[str, Any]]:
    """
    Reads CSV or Excel bank statement and runs auto-categorization on all transactions.
    """
    filename_lower = filename.lower()
    
    if filename_lower.endswith('.csv'):
        # Try reading with utf-8 or latin1
        try:
            df = pd.read_csv(io.BytesIO(file_bytes), encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(io.BytesIO(file_bytes), encoding='latin1')
    elif filename_lower.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(io.BytesIO(file_bytes))
    else:
        raise ValueError("Unsupported file format. Please upload a CSV or Excel file.")

    # Drop fully empty rows
    df = df.dropna(how='all')
    
    # Auto detect headers
    col_map = detect_columns(df)
    
    if 'description' not in col_map:
        # Fallback: Pick the first object/string column as description
        for col in df.columns:
            if df[col].dtype == object and col != col_map.get('date'):
                col_map['description'] = col
                break
                
    if 'date' not in col_map:
        # Fallback: Pick the first column
        col_map['date'] = df.columns[0]

    transactions = []
    
    for _, row in df.iterrows():
        raw_desc = str(row.get(col_map.get('description'), '')).strip()
        if not raw_desc or raw_desc.lower() in ['nan', 'none', 'total', 'opening balance', 'closing balance']:
            continue
            
        date_str = parse_date(row.get(col_map.get('date'), ''))
        
        # Determine Amount and Debit/Credit Type
        amount = 0.0
        txn_type = "DEBIT"
        
        if 'debit' in col_map and 'credit' in col_map:
            debit_val = clean_amount(row.get(col_map['debit'], 0.0))
            credit_val = clean_amount(row.get(col_map['credit'], 0.0))
            if debit_val > 0:
                amount = debit_val
                txn_type = "DEBIT"
            elif credit_val > 0:
                amount = credit_val
                txn_type = "CREDIT"
            else:
                continue
        elif 'amount' in col_map:
            raw_amt = row.get(col_map['amount'], 0.0)
            amount = clean_amount(raw_amt)
            if amount <= 0:
                continue
                
            if 'type' in col_map:
                type_indicator = str(row.get(col_map['type'], '')).upper().strip()
                if 'CR' in type_indicator or 'CREDIT' in type_indicator:
                    txn_type = "CREDIT"
                else:
                    txn_type = "DEBIT"
            else:
                # Check if raw amount was negative or description has credit cues
                try:
                    if float(str(raw_amt).replace(',', '')) < 0:
                        txn_type = "DEBIT"
                    elif any(c in raw_desc.lower() for c in ['credit', 'salary', 'refund', 'interest']):
                        txn_type = "CREDIT"
                except Exception:
                    pass
        else:
            continue

        # Run Categorization Engine
        category, confidence, clean_merchant = categorizer.categorize(
            raw_description=raw_desc,
            amount=amount,
            txn_type=txn_type
        )
        
        transactions.append({
            "date": date_str,
            "raw_description": raw_desc,
            "clean_merchant": clean_merchant,
            "amount": round(amount, 2),
            "type": txn_type,
            "category": category,
            "confidence": confidence,
            "source": "UPLOAD",
            "account": account_name
        })

    return transactions
