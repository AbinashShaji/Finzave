"""
Module: utils/hash_utils.py

Purpose:
Provides standardized hashing functions for duplicate detection across transactions
and security sanitization utilities for CSV exports.
"""
from datetime import date, datetime
from decimal import Decimal


def generate_transaction_hash(date_val, amount, category, description=None) -> str:
    """
    Generates a normalized hash key for duplicate transaction detection.
    Normalizes:
    - date: YYYY-MM-DD string
    - amount: 2-decimal string representation (e.g. 50.00)
    - category: stripped lowercase
    - description: stripped lowercase (safely handling None)
    """
    # Normalize date
    if isinstance(date_val, (date, datetime)):
        norm_date = date_val.strftime('%Y-%m-%d')
    else:
        norm_date = str(date_val or '').strip()
        if len(norm_date) >= 10:
            norm_date = norm_date[:10]

    # Normalize amount
    try:
        norm_amount = f"{float(amount):.2f}"
    except (ValueError, TypeError):
        norm_amount = str(amount or '').strip()

    # Normalize category
    norm_category = str(category or '').strip().lower()

    # Normalize description safely handling None
    norm_description = str(description or '').strip().lower()

    return f"{norm_date}_{norm_amount}_{norm_category}_{norm_description}"


def sanitize_csv_value(value) -> str:
    """
    Escapes CSV values starting with formula trigger characters (=, +, -, @)
    to prevent CSV formula injection / spreadsheet execution.
    """
    if value is None:
        return ""
    val_str = str(value)
    if val_str and val_str[0] in ('=', '+', '-', '@'):
        return f"'{val_str}"
    return val_str
