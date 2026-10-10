"""
Module: utils/csv_processor.py

Purpose:
Provides reusable helper functions and core business logic.

Flow:
User Request -> Route Handler -> Business Logic -> Database

"""
import pandas as pd
from datetime import datetime
import io
import logging
from models.expense import EXPENSE_CATEGORIES, normalize_category, Expense
from utils.hash_utils import generate_transaction_hash

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ['date', 'amount', 'category']
OPTIONAL_COLUMNS = ['description']

def validate_transaction(row_dict: dict) -> dict:
    """Validates an individual transaction row dictionary."""
    errors = []
    raw_date = str(row_dict.get('date', '')).strip()
    formatted_date = None
    try:
        date_val = pd.to_datetime(raw_date).date()
        if date_val > datetime.now().date():
            errors.append("Future transaction date is not allowed")
        else:
            formatted_date = date_val.isoformat()
    except Exception:
        errors.append("Invalid date format")

    amount = None
    try:
        amt = float(row_dict.get('amount', 0))
        if amt <= 0:
            errors.append("Amount must be a positive number")
        else:
            amount = round(amt, 2)
    except Exception:
        errors.append("Amount must be a positive number")

    category = str(row_dict.get('category', '')).strip()
    normalized_cat = None
    if not category or category.lower() == 'nan':
        errors.append("Category cannot be empty")
    else:
        normalized_cat = normalize_category(category)
        if not normalized_cat:
            errors.append(f"Invalid category: {category}")

    desc = str(row_dict.get('description', '') or '').strip()
    if desc.lower() == 'nan':
        desc = ''
    desc = desc[:255]

    is_valid = len(errors) == 0
    record = {
        "date": formatted_date,
        "amount": amount,
        "category": normalized_cat,
        "description": desc
    }
    return {
        "is_valid": is_valid,
        "errors": errors,
        "record": record
    }

def process_expense_csv(file_stream: bytes, user_id: int = None) -> dict:
    """
    Parses an uploaded CSV file containing expenses.
    Validates structure, values, and returns valid/invalid row counts.
    """
    try:
        df = pd.read_csv(io.BytesIO(file_stream))
    except Exception as e:
        logger.error(f"CSV Parse Error: {str(e)}")
        return {"success": False, "error": "Invalid CSV file format."}
        
    if len(df) > 1000:
        return {"success": False, "error": "Maximum of 1000 rows allowed per upload."}
        
    # Check headers (case insensitive)
    df.columns = df.columns.str.lower().str.strip()
    
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        return {"success": False, "error": f"Missing required columns: {', '.join(missing_cols)}"}
        
    valid_records = []
    invalid_records = []
    

    existing_hashes = set()
    if user_id:
        try:
            existing_expenses = Expense.query.filter_by(user_id=user_id).all()
            for ex in existing_expenses:
                h = generate_transaction_hash(ex.date, ex.amount, ex.category, ex.description)
                existing_hashes.add(h)
        except Exception as e:
            logger.error(f"Error fetching existing expenses: {str(e)}")
    
    for index, row in df.iterrows():
        record = {
            "row_number": index + 2, # Account for 0-index and header
            "is_valid": True,
            "errors": []
        }
        
        # Validate Date
        raw_date = str(row['date']).strip()
        if raw_date.lower() == 'nan': raw_date = ''
        record['date'] = raw_date
        try:
            date_val = pd.to_datetime(row['date']).date()
            if date_val > datetime.now().date():
                record['is_valid'] = False
                record['errors'].append("Future transaction date is not allowed")
            else:
                record['date'] = date_val.isoformat()
        except Exception:
            record['is_valid'] = False
            record['errors'].append("Invalid date format")
            
        # Validate Amount
        raw_amount = str(row['amount']).strip()
        if raw_amount.lower() == 'nan': raw_amount = ''
        record['amount'] = raw_amount
        try:
            amount = float(row['amount'])
            if amount <= 0:
                raise ValueError
            record['amount'] = round(amount, 2)
        except Exception:
            record['is_valid'] = False
            record['errors'].append("Amount must be a positive number")
            
        # Validate Category
        category = str(row['category']).strip()
        if category.lower() == 'nan': category = ''
        record['category'] = category
        if not category:
            record['is_valid'] = False
            record['errors'].append("Category cannot be empty")
        else:
            normalized_cat = normalize_category(category)
            if normalized_cat:
                record['category'] = normalized_cat
            else:
                record['is_valid'] = False
                record['errors'].append(f"Invalid category: {category}")
            
        # Optional Description
        desc = ""
        if 'description' in df.columns:
            val = str(row['description']).strip()
            if val.lower() != 'nan':
                desc = val[:255]
        record['description'] = desc
        

        if record['is_valid']:
            # Check for duplicates
            row_hash = generate_transaction_hash(record['date'], record['amount'], record['category'], record.get('description'))
            if user_id and row_hash in existing_hashes:
                record['is_valid'] = False
                record['errors'].append("Duplicate transaction")
                
        if record['is_valid']:
            valid_records.append(record)
            existing_hashes.add(row_hash) # Prevent intra-CSV duplicates
        else:
            invalid_records.append(record)
            
    return {
        "success": True,
        "total_rows": len(df),
        "valid_count": len(valid_records),
        "invalid_count": len(invalid_records),
        "valid_records": valid_records,
        "invalid_records": invalid_records
    }
