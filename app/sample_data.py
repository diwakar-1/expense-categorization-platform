import os
import csv
from datetime import datetime, timedelta

def generate_sample_statements(data_dir: str):
    os.makedirs(data_dir, exist_ok=True)
    today = datetime.now()
    
    # 1. HDFC Bank Statement
    hdfc_path = os.path.join(data_dir, "hdfc_statement_sample.csv")
    hdfc_rows = [
        ["Date", "Narration", "Chq/Ref No", "Value Dt", "Withdrawal Amt", "Deposit Amt", "Closing Balance"],
        [(today - timedelta(days=28)).strftime("%d/%m/%Y"), "SALARY NEFT CR-INFOSYS TECHNOLOGIES LTD-MONTHLY", "00029102", (today - timedelta(days=28)).strftime("%d/%m/%Y"), "", "78500.00", "92340.50"],
        [(today - timedelta(days=26)).strftime("%d/%m/%Y"), "UPI/482910391/SWIGGY BANGALORE/PAYMENT", "UPI4829103", (today - timedelta(days=26)).strftime("%d/%m/%Y"), "640.00", "", "91700.50"],
        [(today - timedelta(days=24)).strftime("%d/%m/%Y"), "ACH DR-PSPCL ELECTRICITY BILL LUDHIANA", "ACH99281", (today - timedelta(days=24)).strftime("%d/%m/%Y"), "3420.00", "", "88280.50"],
        [(today - timedelta(days=22)).strftime("%d/%m/%Y"), "POS 402919 RELIANCE SMART POINT GROCERY", "POS1029", (today - timedelta(days=22)).strftime("%d/%m/%Y"), "2450.00", "", "85830.50"],
        [(today - timedelta(days=20)).strftime("%d/%m/%Y"), "UPI/492019283/AMZN Mktp IN/amzn@apl", "UPI492019", (today - timedelta(days=20)).strftime("%d/%m/%Y"), "1899.00", "", "83931.50"],
        [(today - timedelta(days=18)).strftime("%d/%m/%Y"), "UPI/582910283/UBER INDIA SYSTEMS/TRIP", "UPI582910", (today - timedelta(days=18)).strftime("%d/%m/%Y"), "385.00", "", "83546.50"],
        [(today - timedelta(days=16)).strftime("%d/%m/%Y"), "ACH DR-HDFC MUTUAL FUND SIP GROWTH", "ACH88371", (today - timedelta(days=16)).strftime("%d/%m/%Y"), "5000.00", "", "78546.50"],
        [(today - timedelta(days=14)).strftime("%d/%m/%Y"), "UPI/672819201/BLINKIT COMMERCE GURGAON", "UPI672819", (today - timedelta(days=14)).strftime("%d/%m/%Y"), "920.00", "", "77626.50"],
        [(today - timedelta(days=12)).strftime("%d/%m/%Y"), "POS 882910 APOLLO PHARMACY MEDICINES", "POS8829", (today - timedelta(days=12)).strftime("%d/%m/%Y"), "1240.00", "", "76386.50"],
        [(today - timedelta(days=10)).strftime("%d/%m/%Y"), "NETFLIX ENTERTAINMENT SERVICES MUMBAI", "ECOM8910", (today - timedelta(days=10)).strftime("%d/%m/%Y"), "649.00", "", "75737.50"],
        [(today - timedelta(days=8)).strftime("%d/%m/%Y"), "ATM WDL-HDFC ATM MALL ROAD LUDHIANA", "ATM2910", (today - timedelta(days=8)).strftime("%d/%m/%Y"), "4000.00", "", "71737.50"],
        [(today - timedelta(days=6)).strftime("%d/%m/%Y"), "UPI/719201928/ZOMATO LTD/DINNER", "UPI719201", (today - timedelta(days=6)).strftime("%d/%m/%Y"), "890.00", "", "70847.50"],
        [(today - timedelta(days=4)).strftime("%d/%m/%Y"), "DIVIDEND CR-TCS LIMITED EQUITY", "DIV9281", (today - timedelta(days=4)).strftime("%d/%m/%Y"), "", "1200.00", "72047.50"],
        [(today - timedelta(days=2)).strftime("%d/%m/%Y"), "UPI/819203912/AIRTEL BROADBAND RECHARGE", "UPI819203", (today - timedelta(days=2)).strftime("%d/%m/%Y"), "1179.00", "", "70868.50"],
        [(today - timedelta(days=1)).strftime("%d/%m/%Y"), "UPI/902910291/STARBUCKS COFFEE INDIA", "UPI902910", (today - timedelta(days=1)).strftime("%d/%m/%Y"), "450.00", "", "70418.50"],
    ]
    with open(hdfc_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(hdfc_rows)

    # 2. SBI UPI Statement
    sbi_path = os.path.join(data_dir, "sbi_upi_sample.csv")
    sbi_rows = [
        ["Txn Date", "Particulars", "Debit", "Credit", "Balance"],
        [(today - timedelta(days=25)).strftime("%Y-%m-%d"), "UPI-P2A-ZEPTO COMMERCE ORDER-zepto@hdfc", "485.00", "0.00", "34500.00"],
        [(today - timedelta(days=23)).strftime("%Y-%m-%d"), "UPI-P2P-PAYMENT TO SHARMA JI KIRANA", "1250.00", "0.00", "33250.00"],
        [(today - timedelta(days=21)).strftime("%Y-%m-%d"), "UPI-P2A-RAPIDO BIKE TAXI RIDE", "75.00", "0.00", "33175.00"],
        [(today - timedelta(days=19)).strftime("%Y-%m-%d"), "UPI-P2A-MCDONALDS CONNAUGHT PLACE", "540.00", "0.00", "32635.00"],
        [(today - timedelta(days=17)).strftime("%Y-%m-%d"), "UPI-P2A-RELIANCE JIO 5G PREPAID", "749.00", "0.00", "31886.00"],
        [(today - timedelta(days=15)).strftime("%Y-%m-%d"), "UPI-P2P-RENT SHARE FROM FLATMATES", "0.00", "12000.00", "43886.00"],
        [(today - timedelta(days=13)).strftime("%Y-%m-%d"), "UPI-P2A-BOOKMYSHOW MOVIE TICKETS PVR", "860.00", "0.00", "43026.00"],
        [(today - timedelta(days=11)).strftime("%Y-%m-%d"), "UPI-P2A-INDIAN OIL PETROL PUMP FUEL", "1500.00", "0.00", "41526.00"],
        [(today - timedelta(days=9)).strftime("%Y-%m-%d"), "UPI-P2A-TATA 1MG HEALTHCARE MEDICINES", "780.00", "0.00", "40746.00"],
        [(today - timedelta(days=7)).strftime("%Y-%m-%d"), "UPI-P2A-CHAAYOS TEA AND SNACKS", "260.00", "0.00", "40486.00"],
        [(today - timedelta(days=5)).strftime("%Y-%m-%d"), "UPI-P2A-MYNTRA SHOPPING APPARELS", "2499.00", "0.00", "37987.00"],
        [(today - timedelta(days=3)).strftime("%Y-%m-%d"), "UPI-P2A-GROWW MUTUAL FUND SIP", "3000.00", "0.00", "34987.00"],
        [(today - timedelta(days=1)).strftime("%Y-%m-%d"), "UPI-P2A-DOMINOS PIZZA DELIVERY", "620.00", "0.00", "34367.00"],
    ]
    with open(sbi_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(sbi_rows)

    # 3. ICICI Card Statement
    icici_path = os.path.join(data_dir, "icici_card_sample.csv")
    icici_rows = [
        ["Transaction Date", "Details", "Amount", "Type"],
        [(today - timedelta(days=27)).strftime("%d-%m-%Y"), "FLIPKART INTERNET BLR ORDER", "3499.00", "DR"],
        [(today - timedelta(days=24)).strftime("%d-%m-%Y"), "IRCTC RAILWAY TICKET RESERVATION", "1650.00", "DR"],
        [(today - timedelta(days=21)).strftime("%d-%m-%Y"), "BARBEQUE NATION HOSPITALITY", "2380.00", "DR"],
        [(today - timedelta(days=18)).strftime("%d-%m-%Y"), "SPOTIFY INDIA SUBSCRIPTION", "119.00", "DR"],
        [(today - timedelta(days=15)).strftime("%d-%m-%Y"), "DECATHLON SPORTS STORE PURCHASE", "4120.00", "DR"],
        [(today - timedelta(days=12)).strftime("%d-%m-%Y"), "AMAZON PRIME ANNUAL MEMBERSHIP", "1499.00", "DR"],
        [(today - timedelta(days=9)).strftime("%d-%m-%Y"), "BHARAT PETROLEUM FUEL DEBIT", "2000.00", "DR"],
        [(today - timedelta(days=6)).strftime("%d-%m-%Y"), "MAKETMYTRIP FLIGHT TICKETS", "5800.00", "DR"],
        [(today - timedelta(days=3)).strftime("%d-%m-%Y"), "CASHBACK REWARD CREDITED", "350.00", "CR"],
        [(today - timedelta(days=1)).strftime("%d-%m-%Y"), "SWIGGY INSTAMART ESSENTIALS", "840.00", "DR"],
    ]
    with open(icici_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(icici_rows)

    return [hdfc_path, sbi_path, icici_path]
