import pandas as pd
from datetime import datetime
import io
import logging
from models.expense import EXPENSE_CATEGORIES

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ['date', 'amount', 'category']
OPTIONAL_COLUMNS = ['description']

def process_expense_csv(file_stream: bytes) -> dict:
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
    
    for index, row in df.iterrows():
        record = {
            "row_number": index + 2, # Account for 0-index and header
            "is_valid": True,
            "errors": []
        }
        
        # Validate Date
        try:
            date_val = pd.to_datetime(row['date']).date()
            record['date'] = date_val.isoformat()
        except Exception:
            record['is_valid'] = False
            record['errors'].append("Invalid date format")
            
        # Validate Amount
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
        if not category or category.lower() == 'nan':
            record['is_valid'] = False
            record['errors'].append("Category cannot be empty")
        else:
            # Case insensitive match against EXPENSE_CATEGORIES
            matched = next((c for c in EXPENSE_CATEGORIES if c.lower() == category.lower()), None)
            if matched:
                record['category'] = matched
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
            valid_records.append(record)
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
