from datetime import date
import calendar
from sqlalchemy import func
from extensions import db
from models.income import Income

def get_active_fixed_incomes(user_id, as_of_date):
    """
    Returns the latest effective fixed income for each distinct source as of a specific date.
    Returns: dict with 'total_amount' and 'active_records'
    """
    fixed_incomes = Income.query.filter(
        Income.user_id == user_id,
        Income.income_type == 'Fixed',
        Income.date <= as_of_date
    ).order_by(Income.date.desc()).all()
    
    seen_sources = set()
    total_amount = 0.0
    active_records = []
    
    for record in fixed_incomes:
        source = (record.description or "").strip().lower()
        if source not in seen_sources:
            seen_sources.add(source)
            total_amount += record.amount
            active_records.append({
                "id": record.id,
                "amount": record.amount,
                "date": record.date.isoformat(),
                "description": record.description
            })
            
    return {
        "total_amount": total_amount,
        "active_records": active_records
    }

def get_monthly_income(user_id, year, month):
    """
    Calculates the total income for a specific month.
    Total = (Sum of Variable Income for the month) + (Sum of Latest Fixed Income sources where effective_date <= end_of_month)
    """
    # Variable Income for the specific month
    variable_income = db.session.query(func.sum(Income.amount)).filter(
        Income.user_id == user_id,
        Income.income_type == 'Variable',
        func.extract('year', Income.date) == year,
        func.extract('month', Income.date) == month
    ).scalar() or 0.0
    
    # Active Fixed Income (latest on or before end of month for EACH distinct source)
    last_day = calendar.monthrange(year, month)[1]
    end_of_month_date = date(year, month, last_day)
    
    active_fixed = get_active_fixed_incomes(user_id, end_of_month_date)
    
    return active_fixed['total_amount'] + variable_income
