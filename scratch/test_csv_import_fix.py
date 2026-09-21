
import io
from utils.csv_processor import process_expense_csv
from models.expense import normalize_category, CATEGORY_ALIASES

def test_normalize_category_canonical():
    """Test that existing canonical categories are mapped correctly."""
    assert normalize_category("Food & Dining") == "Food & Dining"
    assert normalize_category("shopping") == "Shopping"
    assert normalize_category("OTHER") == "Other"

def test_normalize_category_alias():
    """Test that alias categories map to their canonical versions."""
    assert normalize_category("Food") == "Food & Dining"
    assert normalize_category("groceries") == "Food & Dining"
    assert normalize_category("Transport") == "Transportation"
    assert normalize_category("electricity") == "Utilities"
    assert normalize_category("miscellaneous") == "Other"

def test_normalize_category_invalid():
    """Test that invalid categories return None."""
    assert normalize_category("Spaceship Fuel") is None
    assert normalize_category("") is None
    assert normalize_category("   ") is None

def test_csv_processor_with_aliases():
    """Test that the CSV processor correctly normalizes categories."""
    csv_content = """Date,Amount,Category,Description
2026-09-01,150.00,Food,Lunch
2026-09-02,50.00,Internet,Wifi bill
2026-09-03,200.00,UnknownCategory,Oops
"""
    file_stream = csv_content.encode('utf-8')
    result = process_expense_csv(file_stream)
    
    assert result['success'] is True
    assert result['total_rows'] == 3
    assert result['valid_count'] == 2
    assert result['invalid_count'] == 1
    
    valid_records = result['valid_records']
    invalid_records = result['invalid_records']
    
    # Food -> Food & Dining
    assert valid_records[0]['category'] == "Food & Dining"
    # Internet -> Utilities
    assert valid_records[1]['category'] == "Utilities"
    
    # UnknownCategory is invalid
    assert invalid_records[0]['is_valid'] is False
    assert "Invalid category: UnknownCategory" in invalid_records[0]['errors']

if __name__ == '__main__':
    test_normalize_category_canonical()
    test_normalize_category_alias()
    test_normalize_category_invalid()
    test_csv_processor_with_aliases()
    print("All tests passed successfully!")
