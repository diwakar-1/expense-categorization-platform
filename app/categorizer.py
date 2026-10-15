import re
import sqlite3
import numpy as np
from typing import Tuple, Dict, List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from .db import get_connection

# Master list of standard expense categories (Academic Accounting Classification)
CATEGORIES = [
    "Food & Dining",
    "Groceries & Essentials",
    "Shopping & E-Commerce",
    "Travel & Commute",
    "Utilities & Bills",
    "Entertainment & Subscriptions",
    "Healthcare & Medical",
    "Investments & Savings",
    "Income & Salary",
    "Miscellaneous & Transfers"
]

# Curated training dataset reflecting Indian UPI, Cards, Netbanking & Merchant descriptions
TRAINING_DATA = [
    # Food & Dining
    ("Swiggy Bangalore Order 48291", "Food & Dining"),
    ("Zomato Ltd Gurgaon Food Delivery", "Food & Dining"),
    ("McDonalds India POS Connaught Place", "Food & Dining"),
    ("Starbucks Coffee Bombay Store 21", "Food & Dining"),
    ("Dominos Pizza Online UPI Order", "Food & Dining"),
    ("Burger King Mumbai Airport", "Food & Dining"),
    ("Chai Point POS Indiranagar", "Food & Dining"),
    ("Haldiram Sweets and Restaurant", "Food & Dining"),
    ("KFC Chicken Restaurant New Delhi", "Food & Dining"),
    ("Barbeque Nation Hospitality", "Food & Dining"),
    ("CCD Cafe Coffee Day MG Road", "Food & Dining"),
    ("Subway Sandwiches Sector 18", "Food & Dining"),
    ("Bikanervala Sweets and Snacks", "Food & Dining"),
    ("Biryani By Kilo Delivery", "Food & Dining"),
    ("Behrouz Biryani Order Food", "Food & Dining"),
    ("Chaayos Chai and Snacks Delhi", "Food & Dining"),
    ("Baskin Robbins Ice Cream Parlour", "Food & Dining"),
    ("Theobroma Patisserie Bakery", "Food & Dining"),
    ("Local Dhaba Lunch and Tea", "Food & Dining"),
    ("UPI-PIZZA HUT-ORDERPAY", "Food & Dining"),
    ("RESTAURANT BILL DINNER FOOD", "Food & Dining"),
    ("TEA STALL PAYMENT SCAN", "Food & Dining"),

    # Groceries & Essentials
    ("Blinkit Commerce Pvt Ltd Gurgaon", "Groceries & Essentials"),
    ("Zepto Quick Commerce Delivery", "Groceries & Essentials"),
    ("Instamart Swiggy Grocery Order", "Groceries & Essentials"),
    ("BigBasket Supermarket Bangalore", "Groceries & Essentials"),
    ("Reliance Smart Point Superstore", "Groceries & Essentials"),
    ("DMart Avenue Supermarts Ltd", "Groceries & Essentials"),
    ("Nature Basket Premium Grocery", "Groceries & Essentials"),
    ("Spencer Supermarket Retail", "Groceries & Essentials"),
    ("More Supermarket Provisions", "Groceries & Essentials"),
    ("Local Kirana Store Ration Milk", "Groceries & Essentials"),
    ("Mother Dairy Milk and Curd Booth", "Groceries & Essentials"),
    ("Amul Ice Cream and Dairy Store", "Groceries & Essentials"),
    ("Country Delight Pure Cow Milk", "Groceries & Essentials"),
    ("Otipy Fresh Vegetables and Fruits", "Groceries & Essentials"),
    ("FreshToHome Fish and Meat", "Groceries & Essentials"),
    ("Licious Meat & Poultry Bangalore", "Groceries & Essentials"),
    ("VEGETABLE VENDOR SABZI MANDI", "Groceries & Essentials"),
    ("GROCERY STORE GENERAL PROVISIONS", "Groceries & Essentials"),

    # Shopping & E-Commerce
    ("Amazon India Marketplace Payments", "Shopping & E-Commerce"),
    ("Flipkart Internet Pvt Ltd Bangalore", "Shopping & E-Commerce"),
    ("Myntra Designs Private Limited", "Shopping & E-Commerce"),
    ("Ajio Reliance Retail Fashion", "Shopping & E-Commerce"),
    ("Nykaa E-Retail Beauty Cosmetics", "Shopping & E-Commerce"),
    ("Tata CLiQ Luxury Fashion", "Shopping & E-Commerce"),
    ("Zara Retail India Store DLF", "Shopping & E-Commerce"),
    ("H&M Hennes Mauritz Retail Store", "Shopping & E-Commerce"),
    ("Uniqlo Apparels India Ambience", "Shopping & E-Commerce"),
    ("Decathlon Sports Goods Retail", "Shopping & E-Commerce"),
    ("Croma Electronics Infiniti Retail", "Shopping & E-Commerce"),
    ("Reliance Digital Electronic Store", "Shopping & E-Commerce"),
    ("Vijay Sales Electronics Store", "Shopping & E-Commerce"),
    ("Meesho Online Shopping App", "Shopping & E-Commerce"),
    ("Shoppers Stop Departmental Store", "Shopping & E-Commerce"),
    ("Lifestyle International Retail", "Shopping & E-Commerce"),
    ("Bata Footwear India Limited", "Shopping & E-Commerce"),
    ("CLOTHING STORE PURCHASE SHIRT", "Shopping & E-Commerce"),
    ("JEWELLERY ORNAMENTS PURCHASE", "Shopping & E-Commerce"),

    # Travel & Commute
    ("Uber India Technology Private Limited", "Travel & Commute"),
    ("Ola Cabs ANI Technologies Cab Trip", "Travel & Commute"),
    ("Rapido Bike Taxi Commute Bangalore", "Travel & Commute"),
    ("IRCTC Indian Railways Ticket Booking", "Travel & Commute"),
    ("MakeMyTrip India Flight Booking", "Travel & Commute"),
    ("Goibibo Flights and Hotels", "Travel & Commute"),
    ("Yatra Online Travel Portal", "Travel & Commute"),
    ("Cleartrip Air Tickets Reservation", "Travel & Commute"),
    ("IndiGo InterGlobe Aviation Flight", "Travel & Commute"),
    ("Air India Tickets New Delhi", "Travel & Commute"),
    ("Indian Oil Petrol Pump Fuel Station", "Travel & Commute"),
    ("Bharat Petroleum Petrol Pump Diesel", "Travel & Commute"),
    ("Hindustan Petroleum Fuel Station", "Travel & Commute"),
    ("Delhi Metro Rail Corporation DMRC", "Travel & Commute"),
    ("Bangalore Metro Rail Smart Card", "Travel & Commute"),
    ("FASTag Toll Plaza Highway NHAI", "Travel & Commute"),
    ("AUTO RICKSHAW FARE COMMUTE", "Travel & Commute"),
    ("PETROL DIESEL VEHICLE REFUEL", "Travel & Commute"),
    ("PARKING CHARGES MALL AIRPORT", "Travel & Commute"),

    # Utilities & Bills
    ("Electricity Bill Payment PSPCL Punjab", "Utilities & Bills"),
    ("Bescom Electricity Bill Bangalore", "Utilities & Bills"),
    ("Tata Power Electricity Bill Mumbai", "Utilities & Bills"),
    ("BSES Yamuna Power Limited Delhi", "Utilities & Bills"),
    ("Mahanagar Gas Limited PNG Bill", "Utilities & Bills"),
    ("Indane LPG Gas Cylinder Booking", "Utilities & Bills"),
    ("Bharat Gas Cylinder Refill", "Utilities & Bills"),
    ("Airtel Postpaid Mobile Broadband Bill", "Utilities & Bills"),
    ("Reliance Jio Prepaid Recharge 5G", "Utilities & Bills"),
    ("Vodafone Idea Vi Mobile Bill", "Utilities & Bills"),
    ("ACT Fibernet Internet Broadband Bill", "Utilities & Bills"),
    ("Tata Play DTH Satellite Television", "Utilities & Bills"),
    ("Municipal Water Supply Utility Tax", "Utilities & Bills"),
    ("Society Maintenance Charges Flat", "Utilities & Bills"),
    ("CRED Club Credit Card Bill Payment", "Utilities & Bills"),
    ("PAYTM BILLPAY WATER ELECTRICITY", "Utilities & Bills"),

    # Entertainment & Subscriptions
    ("Netflix Entertainment Services India", "Entertainment & Subscriptions"),
    ("Spotify Music Premium Subscription", "Entertainment & Subscriptions"),
    ("Amazon Prime Annual Membership", "Entertainment & Subscriptions"),
    ("Disney+ Hotstar Subscription Plan", "Entertainment & Subscriptions"),
    ("YouTube Premium Family Membership", "Entertainment & Subscriptions"),
    ("Apple.com/bill Services iTunes", "Entertainment & Subscriptions"),
    ("BookMyShow Bigtree Entertainment Cinema", "Entertainment & Subscriptions"),
    ("PVR Cinemas Movie Tickets Gurgaon", "Entertainment & Subscriptions"),
    ("INOX Leisure Movie Multiplex", "Entertainment & Subscriptions"),
    ("Sony LIV Entertainment OTT App", "Entertainment & Subscriptions"),
    ("Zee5 Entertainment Media OTT", "Entertainment & Subscriptions"),
    ("Audible India Audiobooks", "Entertainment & Subscriptions"),
    ("Kindle Unlimited Book Subscription", "Entertainment & Subscriptions"),
    ("OpenAI ChatGPT Plus Subscription", "Entertainment & Subscriptions"),
    ("Google One Storage Subscription", "Entertainment & Subscriptions"),
    ("GAMING STEAM VALVE SOFTWARE", "Entertainment & Subscriptions"),

    # Healthcare & Medical
    ("Apollo Pharmacy Medicines Bangalore", "Healthcare & Medical"),
    ("Tata 1mg Healthcare Technologies", "Healthcare & Medical"),
    ("PharmEasy Medicine Delivery App", "Healthcare & Medical"),
    ("Netmeds Marketplace Pharmacy", "Healthcare & Medical"),
    ("MedPlus Health Services Medical Store", "Healthcare & Medical"),
    ("Max Healthcare Institute Hospital", "Healthcare & Medical"),
    ("Fortis Hospital OPD Consultation", "Healthcare & Medical"),
    ("Manipal Hospital Medical Treatment", "Healthcare & Medical"),
    ("Dr Lal PathLabs Blood Test Pathology", "Healthcare & Medical"),
    ("Metropolis Healthcare Diagnostic Lab", "Healthcare & Medical"),
    ("Guardian Pharmacy Healthcare Store", "Healthcare & Medical"),
    ("Dental Clinic Teeth Checkup", "Healthcare & Medical"),
    ("CLINIC DOCTOR CONSULTATION FEE", "Healthcare & Medical"),
    ("SURGICAL EYE TESTING OPTICALS", "Healthcare & Medical"),

    # Investments & Savings
    ("Zerodha Broking Limited Stock Funds", "Investments & Savings"),
    ("Groww Nextbillion Technology Mutual Fund", "Investments & Savings"),
    ("Angel One Broking Share Trading", "Investments & Savings"),
    ("Upstox RKSV Securities Trading", "Investments & Savings"),
    ("HDFC Mutual Fund SIP Investment", "Investments & Savings"),
    ("SBI Mutual Fund Monthly SIP Debit", "Investments & Savings"),
    ("Nippon India Mutual Fund Growth", "Investments & Savings"),
    ("ICICI Prudential AMC Investment", "Investments & Savings"),
    ("PPF Public Provident Fund Deposit", "Investments & Savings"),
    ("Fixed Deposit Recurring Deposit Transfer", "Investments & Savings"),
    ("National Pension System NPS Contribution", "Investments & Savings"),
    ("Sovereign Gold Bonds RBI Investment", "Investments & Savings"),
    ("COIN ZERODHA SIP INVESTMENT", "Investments & Savings"),

    # Income & Salary
    ("SALARY CREDITED INFOSYS TECHNOLOGIES", "Income & Salary"),
    ("MONTHLY SALARY CREDITED TCS LTD", "Income & Salary"),
    ("SALARY DIRECT DEPOSIT ACCENTURE", "Income & Salary"),
    ("SALARY NEFT PAYMENT BY EMPLOYER", "Income & Salary"),
    ("INTEREST CREDITED SAVINGS ACCOUNT", "Income & Salary"),
    ("DIVIDEND RECEIVED TCS LIMITED", "Income & Salary"),
    ("TAX REFUND INCOME TAX DEPT CPC", "Income & Salary"),
    ("FREELANCE CONSULTING PROJECT PAYMENT", "Income & Salary"),
    ("CLIENT PAYMENT RECEIVED INWARD REMITTANCE", "Income & Salary"),
    ("STIPEND INTERNSHIP CREDITED", "Income & Salary"),
    ("CASH DEPOSIT CDM BRANCH BANK", "Income & Salary"),
    ("BONUS ANNUAL INCENTIVE CREDITED", "Income & Salary"),

    # Miscellaneous & Transfers
    ("ATM CASH WITHDRAWAL HDFC BANK", "Miscellaneous & Transfers"),
    ("ATM WDL CASH SBI BOOTH", "Miscellaneous & Transfers"),
    ("P2P UPI SENT TO FRIEND SHARMA", "Miscellaneous & Transfers"),
    ("UPI TRANSFER TO ROHIT PERSONAL", "Miscellaneous & Transfers"),
    ("SELF TRANSFER TO KOTAK ACCOUNT", "Miscellaneous & Transfers"),
    ("IMPS TRANSFER TO SAVINGS ACC", "Miscellaneous & Transfers"),
    ("BANK SERVICE CHARGES SMS FEE", "Miscellaneous & Transfers"),
    ("CHEQUE BOOK ISSUANCE CHARGE", "Miscellaneous & Transfers"),
    ("LAUNDRY DRY CLEANING PAYMENT", "Miscellaneous & Transfers"),
    ("PET CLINIC VET DOG FOOD", "Miscellaneous & Transfers"),
    ("DONATION CHARITY TEMPLE TRUST", "Miscellaneous & Transfers")
]

class ExpenseCategorizer:
    def __init__(self):
        self.pipeline = None
        self._train_model()

    def _train_model(self):
        texts = [item[0] for item in TRAINING_DATA]
        labels = [item[1] for item in TRAINING_DATA]
        
        # Word + Subword character n-grams to capture misspellings and bank codes
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                ngram_range=(1, 3),
                analyzer='word',
                token_pattern=r'(?u)\b\w+\b',
                lowercase=True
            )),
            ('clf', LogisticRegression(C=2.0, max_iter=500, random_state=42))
        ])
        self.pipeline.fit(texts, labels)

    def clean_text(self, raw_text: str) -> Tuple[str, str]:
        """
        Cleans bank statement/UPI descriptions and extracts the primary merchant name.
        Returns: (cleaned_description, extracted_merchant)
        """
        if not raw_text:
            return "Unknown Transaction", "Unknown"

        text = str(raw_text).strip()

        # Step 1: Detect and clean UPI patterns (e.g., UPI/48392019283/SWIGGY/swiggy@icici/...)
        upi_match = re.search(r'UPI(?:/|-)(?:CR/|DR/)?(?:[0-9A-Z]+/)?([^/]+)', text, re.IGNORECASE)
        merchant = ""
        if upi_match:
            candidate = upi_match.group(1).strip()
            # Clean if candidate contains email handles or numeric IDs
            candidate = re.sub(r'@[a-zA-Z0-9]+', '', candidate)
            candidate = re.sub(r'^[0-9\-_]+', '', candidate)
            if len(candidate) > 2:
                merchant = candidate

        # Step 2: Strip common bank transaction prefixes
        cleaned = re.sub(r'(?i)\b(UPI|IMPS|NEFT|RTGS|POS|ATM|WDL|ACH|NACH|INB|BIL|VPS|CMS|ECOM)\b[-/:]?', ' ', text)
        cleaned = re.sub(r'\b\d{6,}\b', ' ', cleaned) # Strip long numeric reference/UTR numbers
        cleaned = re.sub(r'(?i)\b(XX\d{4}|\*{4}\d{4})\b', ' ', cleaned) # Strip masked card numbers
        cleaned = re.sub(r'(?i)\b(pvt|ltd|limited|inc|corp|co|llp)\b', ' ', cleaned)
        cleaned = re.sub(r'[_\-\\/\|:;*#]+', ' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        # Step 3: Rule-based merchant identification for top Indian brands
        merchant_rules = [
            ("Swiggy", ["swiggy", "bundl"]),
            ("Zomato", ["zomato", "blinkit", "grofers"]),
            ("Blinkit", ["blinkit", "grofers"]),
            ("Zepto", ["zepto", "kiranakart"]),
            ("Amazon", ["amazon", "amzn"]),
            ("Flipkart", ["flipkart"]),
            ("Myntra", ["myntra"]),
            ("Uber", ["uber"]),
            ("Ola", ["ola cabs", "ani tech", "olacabs"]),
            ("Rapido", ["rapido"]),
            ("Starbucks", ["starbucks", "tata starbucks"]),
            ("McDonald's", ["mcdonald", "hardcastle"]),
            ("Domino's", ["dominos", "jubilant"]),
            ("KFC", ["kfc"]),
            ("Burger King", ["burger king"]),
            ("Apollo Pharmacy", ["apollo"]),
            ("Tata 1mg", ["1mg", "tata 1mg"]),
            ("PharmEasy", ["pharmeasy"]),
            ("Netflix", ["netflix"]),
            ("Spotify", ["spotify"]),
            ("Hotstar", ["hotstar", "disney"]),
            ("BookMyShow", ["bookmyshow", "bigtree"]),
            ("PVR Cinemas", ["pvr"]),
            ("Jio", ["reliance jio", "jio"]),
            ("Airtel", ["airtel", "bharti airtel"]),
            ("PSPCL", ["pspcl", "punjab state power"]),
            ("IRCTC", ["irctc"]),
            ("MakeMyTrip", ["makemytrip", "mmt"]),
            ("Zerodha", ["zerodha"]),
            ("Groww", ["groww"]),
            ("Salary", ["salary", "payroll", "stipend"]),
            ("ATM Cash", ["atm wdl", "cash wdl", "atm withdrawal"]),
            ("HPCL Petrol", ["hindustan petro", "hpcl"]),
            ("IOCL Petrol", ["indian oil", "iocl"]),
            ("BPCL Petrol", ["bharat petro", "bpcl"])
        ]

        lower_raw = text.lower()
        for brand, keywords in merchant_rules:
            if any(k in lower_raw for k in keywords):
                merchant = brand
                break

        # Fallback merchant extraction if not matched
        if not merchant:
            words = cleaned.split()
            if words:
                merchant = " ".join(words[:3]).title()
            else:
                merchant = text[:20].title()

        return cleaned if cleaned else text, merchant.strip()

    def categorize(self, raw_description: str, amount: float = 0.0, txn_type: str = "DEBIT") -> Tuple[str, float, str]:
        """
        Categorizes transaction based on user memory, rules, and ML model.
        Returns: (category, confidence, clean_merchant)
        """
        cleaned_text, merchant = self.clean_text(raw_description)

        # 1. Check user override rules in DB
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT category FROM category_overrides WHERE ? LIKE '%' || merchant_pattern || '%'", (merchant.lower(),))
            row = cursor.fetchone()
            conn.close()
            if row:
                return row["category"], 1.0, merchant
        except Exception:
            pass

        # 2. Strict Income Rule
        if txn_type.upper() == "CREDIT":
            income_keywords = ["salary", "stipend", "interest", "dividend", "refund", "reimbursement", "payroll", "deposit", "bonus"]
            if any(k in raw_description.lower() for k in income_keywords):
                return "Income & Salary", 0.99, merchant
            # If high amount credit without expense tags, default to Income & Salary
            if amount > 5000:
                return "Income & Salary", 0.90, merchant

        # 3. High-priority deterministic rules
        desc_lower = raw_description.lower()
        if any(w in desc_lower for w in ["swiggy", "zomato", "mcdonald", "starbucks", "domino", "restaurant", "cafe", "dhaba", "burger king", "kfc"]):
            return "Food & Dining", 0.98, merchant
        if any(w in desc_lower for w in ["blinkit", "zepto", "instamart", "bigbasket", "dmart", "groceries", "supermarket", "kirana", "milk", "vegetable"]):
            return "Groceries & Essentials", 0.98, merchant
        if any(w in desc_lower for w in ["amazon", "flipkart", "myntra", "ajio", "nykaa", "zara", "h&m", "retail", "croma", "electronics"]):
            return "Shopping & E-Commerce", 0.97, merchant
        if any(w in desc_lower for w in ["uber", "ola", "rapido", "irctc", "metro", "petrol", "diesel", "fuel", "makemytrip", "flight", "indigo"]):
            return "Travel & Commute", 0.97, merchant
        if any(w in desc_lower for w in ["electricity", "pspcl", "bescom", "airtel", "jio", "broadband", "water bill", "gas cylinder", "indane", "dth"]):
            return "Utilities & Bills", 0.98, merchant
        if any(w in desc_lower for w in ["netflix", "spotify", "prime", "hotstar", "youtube", "bookmyshow", "pvr", "cinema", "chatgpt"]):
            return "Entertainment & Subscriptions", 0.98, merchant
        if any(w in desc_lower for w in ["pharmacy", "apollo", "1mg", "hospital", "clinic", "doctor", "medicines", "lab test"]):
            return "Healthcare & Medical", 0.98, merchant
        if any(w in desc_lower for w in ["zerodha", "groww", "mutual fund", "sip", "trading", "stocks", "ppf", "nps", "fd "]):
            return "Investments & Savings", 0.98, merchant
        if any(w in desc_lower for w in ["atm wdl", "cash withdrawal", "transfer to"]):
            return "Miscellaneous & Transfers", 0.95, merchant

        # 4. Fallback to Machine Learning model with confidence score
        combined_features = f"{cleaned_text} {merchant}"
        probs = self.pipeline.predict_proba([combined_features])[0]
        max_idx = int(np.argmax(probs))
        predicted_category = self.pipeline.classes_[max_idx]
        confidence = float(probs[max_idx])

        # If confidence is too low (< 0.35), group into Miscellaneous
        if confidence < 0.35:
            return "Miscellaneous & Transfers", round(confidence, 2), merchant

        return predicted_category, round(confidence, 2), merchant

# Global instance
categorizer = ExpenseCategorizer()
