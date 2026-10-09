"""
Module: tests/test_analysis_incomplete.py

Purpose:
Contains Pytest test cases ensuring application stability.

Flow:
User Request -> Route Handler -> Business Logic -> Database

"""
import pytest
from datetime import date
from utils.rule_engine import FinancialPeriod, evaluate_rules
from analysis.services import build_overview, build_monthly_analysis, build_yearly_analysis
from utils.financial_metrics import calculate_period_metrics

def test_current_month_with_income_no_expenses():
    period_id = f"{date.today().year}-{date.today().month:02d}"
    
    # 1. Current month with income but no expenses
    current = FinancialPeriod(
        period_id=period_id,
        fixed_income=50000.0,
        variable_income=0.0,
        expenses=[],
        is_current_month=True
    )
    
    prev = FinancialPeriod(
        period_id="2023-01",
        fixed_income=50000.0,
        variable_income=0.0,
        expenses=[{'category': 'Rent', 'amount': 15000.0}],
        is_current_month=False
    )
    
    periods = [prev, current]
    
    assert current.status == "incomplete"
    
    # Check no savings growth calculation / category reduction
    overview = build_overview(periods)
    assert overview["is_incomplete"] is True
    assert overview["has_data"] is True
    assert overview["narrative_title"] == "Your financial tracking is incomplete."
    
    # trends should be None
    assert overview["trends"]["savings_change"] is None
    
    # Insights shouldn't have fake savings logic
    assert "Your expense data for this month is incomplete. Savings impact will be calculated after transactions are added." in overview["savings_insights"]

def test_normal_month():
    period_id = f"{date.today().year}-{date.today().month:02d}"
    current = FinancialPeriod(
        period_id=period_id,
        fixed_income=50000.0,
        variable_income=0.0,
        expenses=[{'category': 'Rent', 'amount': 15000.0}],
        is_current_month=True
    )
    
    assert current.status == "complete"
    overview = build_overview([current])
    assert overview["is_incomplete"] is False

def test_new_user_no_transactions():
    current = FinancialPeriod(
        period_id="2023-01",
        fixed_income=0.0,
        variable_income=0.0,
        expenses=[],
        is_current_month=True
    )
    
    assert current.status == "no_data"
    overview = build_overview([current])
    assert overview["has_data"] is False

def test_metrics_is_incomplete():
    period_id = f"{date.today().year}-{date.today().month:02d}"
    current = FinancialPeriod(
        period_id=period_id,
        fixed_income=50000.0,
        variable_income=0.0,
        expenses=[],
        is_current_month=True
    )
    
    metrics = calculate_period_metrics([current])
    assert metrics["is_incomplete"] is True
