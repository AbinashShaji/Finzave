"""
Module: utils/finance.py

Purpose:
Provides reusable helper functions and core business logic.

Flow:
User Request -> Route Handler -> Business Logic -> Database

"""
from datetime import date
import calendar
from sqlalchemy import func
from extensions import db
from models.income import Income

def get_active_fixed_incomes(user_id, as_of_date):
    """
    Returns the latest effective fixed income for each distinct source as of a specific date using database identity.
    Returns: dict with 'total_amount' and 'active_records'
    """
    fixed_incomes = Income.query.filter(
        Income.user_id == user_id,
        Income.income_type == 'Fixed',
        Income.date <= as_of_date
    ).order_by(Income.date.desc()).all()
    
    seen_ids = set()
    total_amount = 0.0
    active_records = []
    
    for record in fixed_incomes:
        key = record.id
        if key not in seen_ids:
            seen_ids.add(key)
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
    breakdown = get_monthly_income_breakdown(user_id, year, month)
    return breakdown['fixed'] + breakdown['variable']

def get_monthly_income_breakdown(user_id, year, month):
    variable_income = db.session.query(func.sum(Income.amount)).filter(
        Income.user_id == user_id,
        Income.income_type == 'Variable',
        func.extract('year', Income.date) == year,
        func.extract('month', Income.date) == month
    ).scalar() or 0.0
    
    last_day = calendar.monthrange(year, month)[1]
    end_of_month_date = date(year, month, last_day)
    
    active_fixed = get_active_fixed_incomes(user_id, end_of_month_date)
    return {
        'fixed': active_fixed['total_amount'],
        'variable': variable_income
    }

def build_financial_periods(user_id, months=12):
    """
    Builds FinancialPeriod objects for the user.
    If months > 1, spans at least `months` (default 12) or the user's available history so no data is lost.
    If months == 1, builds for the current month only.
    """
    from utils.rule_engine import FinancialPeriod
    from models.expense import Expense
    from dateutil.relativedelta import relativedelta
    from datetime import date
    import calendar
    
    today = date.today()
    effective_months = months or 12
    if effective_months > 1:
        earliest_expense = db.session.query(func.min(Expense.date)).filter(Expense.user_id == user_id).scalar()
        earliest_income = db.session.query(func.min(Income.date)).filter(Income.user_id == user_id).scalar()
        earliest_dates = [d for d in [earliest_expense, earliest_income] if d is not None]
        if earliest_dates:
            earliest_date = min(earliest_dates)
            history_months = (today.year - earliest_date.year) * 12 + (today.month - earliest_date.month) + 1
            effective_months = max(effective_months, history_months)
            
    periods = []
    start_date = (today - relativedelta(months=effective_months - 1)).replace(day=1)
    
    # 1. Fetch all expenses grouped by year, month, category
    expenses_query = db.session.query(
        func.extract('year', Expense.date).label('year'),
        func.extract('month', Expense.date).label('month'),
        Expense.category,
        func.sum(Expense.amount).label('total')
    ).filter(
        Expense.user_id == user_id,
        Expense.date >= start_date
    ).group_by(
        'year', 'month', Expense.category
    ).all()
    
    expense_dict = {}
    for r in expenses_query:
        key = (int(r.year), int(r.month))
        if key not in expense_dict:
            expense_dict[key] = []
        expense_dict[key].append({'amount': float(r.total), 'category': r.category})
        
    # 2. Fetch all variable incomes grouped by year, month
    variable_query = db.session.query(
        func.extract('year', Income.date).label('year'),
        func.extract('month', Income.date).label('month'),
        func.sum(Income.amount).label('total')
    ).filter(
        Income.user_id == user_id,
        Income.income_type == 'Variable',
        Income.date >= start_date
    ).group_by(
        'year', 'month'
    ).all()
    
    variable_dict = { (int(r.year), int(r.month)): float(r.total) for r in variable_query }
    
    # 3. Fetch all fixed incomes up to today to compute effective fixed incomes per month
    all_fixed = Income.query.filter(
        Income.user_id == user_id,
        Income.income_type == 'Fixed',
        Income.date <= today
    ).order_by(Income.date.desc()).all()
    
    # Generate periods from oldest to newest
    for i in range(effective_months - 1, -1, -1):
        target_date = today - relativedelta(months=i)
        year = target_date.year
        month = target_date.month
        
        period_id = f"{year}-{month:02d}"
        
        # Calculate active fixed for this month
        last_day = calendar.monthrange(year, month)[1]
        end_of_month_date = date(year, month, last_day)
        
        seen_ids = set()
        fixed_total = 0.0
        for record in all_fixed:
            if record.date <= end_of_month_date:
                key = record.id
                if key not in seen_ids:
                    seen_ids.add(key)
                    fixed_total += record.amount
                    
        variable_total = variable_dict.get((year, month), 0.0)
        expenses_list = expense_dict.get((year, month), [])
        
        is_current = (year == today.year and month == today.month)
        period = FinancialPeriod(
            period_id=period_id,
            fixed_income=fixed_total,
            variable_income=variable_total,
            expenses=expenses_list,
            is_current_month=is_current
        )
        periods.append(period)
        
    # If evaluating multi-month history, trim leading periods that have no data prior to earliest user activity
    if effective_months > 1 and periods:
        first_data_idx = 0
        for idx, p in enumerate(periods):
            if p.status != "no_data":
                first_data_idx = idx
                break
        if first_data_idx > 0:
            periods = periods[first_data_idx:]
            
    return periods

