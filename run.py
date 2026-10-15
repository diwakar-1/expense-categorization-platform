import uvicorn
import os
import sys

if __name__ == "__main__":
    print("=" * 70)
    print("  AUTOMATED EXPENSE CATEGORIZATION & SPENDING ANALYSIS PLATFORM")
    print("  Minor Project - Punjab College of Technical Education (PCTE)")
    print("  Team: Pratyush (B.Com 3B) & Komalpreet Kaur (BCA 3B)")
    print("=" * 70)
    print("\nStarting local development server on http://localhost:8000 ...")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
