import pytest
from utils.rule_engine import FinancialPeriod
from utils.finance import build_financial_periods

def test_financial_period_initialization():
    period = FinancialPeriod(
        period_id="2023-10",
        fixed_income=5000.0,
        variable_income=1000.0,
        expenses=[
            {'amount': 1500.0, 'category': 'Rent & Housing'},
            {'amount': 500.0, 'category': 'Food & Dining'}
        ],
        is_current_month=False
    )
    
    assert period.period_id == "2023-10"
    assert period.fixed_income == 5000.0
    assert period.variable_income == 1000.0
    assert period.total_income == 6000.0
    assert period.total_expenses == 2000.0
    assert period.savings == 4000.0
    assert period.savings_rate == pytest.approx(0.666, 0.01)
    assert period.status == "complete"
    assert period.categories["Rent & Housing"] == 1500.0
    assert period.categories["Food & Dining"] == 500.0

def test_financial_period_incomplete_month():
    # Only income, no expenses yet, current month
    period = FinancialPeriod(
        period_id="2023-10",
        fixed_income=5000.0,
        variable_income=0.0,
        expenses=[],
        is_current_month=True
    )
    
    assert period.total_income == 5000.0
    assert period.total_expenses == 0.0
    assert period.status == "incomplete"

def test_financial_period_no_data():
    period = FinancialPeriod(
        period_id="2023-10",
        fixed_income=0.0,
        variable_income=0.0,
        expenses=[],
        is_current_month=False
    )
    
    assert period.total_income == 0.0
    assert period.total_expenses == 0.0
    assert period.status == "no_data"
