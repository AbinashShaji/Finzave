"""
Module: tests/test_monthly_analysis_periods.py

Purpose:
Validates analysis period generation and reporting accuracy:
- Removal of fake historical months before user data existed
- Data availability validation (0 months, 1-2 months, 3+ months)
- Category comparison using first_actual_data_month
- Pattern detection protection against zero-data comparisons
"""
import pytest
from datetime import date
from dateutil.relativedelta import relativedelta
from extensions import db
from models.user import User
from models.expense import Expense
from models.income import Income
from utils.rule_engine import FinancialPeriod
from utils.finance import build_financial_periods
from analysis.services import (
    build_monthly_analysis,
    build_yearly_analysis,
    validate_data_availability,
    get_available_financial_months
)


def test_test1_user_created_january_expenses_january_onwards(app):
    """
    Test 1:
    User created: 2026-01
    Expenses: January onwards
    Expected:
    Monthly analysis starts: 2026-01
    NOT: 2025-11
    """
    with app.app_context():
        user = User(
            username="test_jan_user",
            email="jan_user@test.com",
            password_hash="hash",
            created_at=date(2026, 1, 15)
        )
        db.session.add(user)
        db.session.commit()

        # Add expenses from January 2026 onwards through current month
        today = date.today()
        # Add income and expense in 2026-01
        inc_jan = Income(user_id=user.id, amount=50000.0, income_type="Fixed", date=date(2026, 1, 1), description="Salary")
        exp_jan = Expense(user_id=user.id, amount=15000.0, category="Rent & Housing", date=date(2026, 1, 2), description="Rent Jan")
        # Add income and expense in current month
        inc_now = Income(user_id=user.id, amount=50000.0, income_type="Fixed", date=today, description="Salary")
        exp_now = Expense(user_id=user.id, amount=17000.0, category="Rent & Housing", date=today, description="Rent Now")
        db.session.add_all([inc_jan, exp_jan, inc_now, exp_now])
        db.session.commit()

        periods = build_financial_periods(user.id, months=12, for_analysis=True)
        monthly = build_monthly_analysis(periods)

        # Verify analysis starts from 2026-01
        assert periods[0].period_id == "2026-01"
        assert monthly["has_data"] is True
        assert monthly["months_data"][0]["period"] == "2026-01"
        assert monthly["chart_data"]["labels"][0] == "2026-01"

        # Verify fake months 2025-11 and 2025-12 are NOT generated
        assert "2025-11" not in monthly["chart_data"]["labels"]
        assert "2025-12" not in monthly["chart_data"]["labels"]
        assert "2025-11" not in [m["period"] for m in monthly["months_data"]]
        assert "2025-12" not in [m["period"] for m in monthly["months_data"]]


def test_test2_user_has_only_one_month_data():
    """
    Test 2:
    User has only one month data.
    Expected:
    'Not enough financial history for trend analysis.'
    """
    period = FinancialPeriod(
        period_id="2026-10",
        fixed_income=50000.0,
        variable_income=0.0,
        expenses=[{'amount': 20000.0, 'category': 'Rent & Housing'}],
        is_current_month=True
    )

    # Validation function check
    msg = validate_data_availability([period])
    assert "Not enough financial history" in msg

    # Monthly analysis check
    monthly = build_monthly_analysis([period])
    assert monthly["has_data"] is False
    assert "enough financial history" in monthly["message"]

    # Yearly analysis check
    yearly = build_yearly_analysis([period])
    assert yearly["has_data"] is False
    assert "enough financial history" in yearly["message"]


def test_test2_user_has_zero_months_data():
    """
    Test 2 (0 months):
    User has no financial records.
    Expected:
    'No financial data available for analysis.'
    """
    period = FinancialPeriod(
        period_id="2026-10",
        fixed_income=0.0,
        variable_income=0.0,
        expenses=[],
        is_current_month=True
    )

    msg = validate_data_availability([period])
    assert msg == "No financial data available for analysis."

    monthly = build_monthly_analysis([period])
    assert monthly["has_data"] is False
    assert monthly["message"] == "No financial data available for analysis."


def test_test3_category_exists_only_in_latest_month():
    """
    Test 3:
    Category exists only in latest month.
    Expected:
    'No previous data available for comparison.'
    NOT:
    '+₹12,000 increase'
    """
    p1 = FinancialPeriod(
        period_id="2026-08",
        fixed_income=50000.0,
        variable_income=0.0,
        expenses=[{'amount': 15000.0, 'category': 'Rent & Housing'}]
    )
    p2 = FinancialPeriod(
        period_id="2026-09",
        fixed_income=50000.0,
        variable_income=0.0,
        expenses=[{'amount': 15000.0, 'category': 'Rent & Housing'}]
    )
    # In latest month, shopping is added for the very first time (₹12,000)
    p3 = FinancialPeriod(
        period_id="2026-10",
        fixed_income=50000.0,
        variable_income=0.0,
        expenses=[
            {'amount': 15000.0, 'category': 'Rent & Housing'},
            {'amount': 12000.0, 'category': 'Shopping'}
        ],
        is_current_month=True
    )

    monthly = build_monthly_analysis([p1, p2, p3])
    assert monthly["has_data"] is True

    shopping = next((c for c in monthly["category_comparison"] if c["category"] == "Shopping"), None)
    assert shopping is not None
    assert shopping["has_previous_data"] is False
    assert shopping["diff"] is None
    assert shopping["change_pct"] is None
    assert "No previous data available" in shopping["change_display"]

    # Verify insights do not falsely claim Shopping increased by ₹12,000
    insights_str = " ".join(monthly["insights"])
    assert "Shopping spending increased" not in insights_str
    assert "Shopping was ₹12,000 higher" not in insights_str


def test_test4_existing_10_month_dataset(app):
    """
    Test 4:
    Existing 10 month dataset.
    Expected:
    Analysis unchanged except removal of fake months.
    """
    with app.app_context():
        user = User(
            username="test_10m_user",
            email="user10m@test.com",
            password_hash="hash",
            created_at=date(2026, 1, 1)
        )
        db.session.add(user)
        db.session.commit()

        # Add 10 continuous months of data: 2026-01 through 2026-10
        for m in range(1, 11):
            inc = Income(user_id=user.id, amount=50000.0, income_type="Fixed", date=date(2026, m, 1), description="Salary")
            exp = Expense(user_id=user.id, amount=20000.0, category="Rent & Housing", date=date(2026, m, 5), description="Rent")
            db.session.add_all([inc, exp])
        db.session.commit()

        periods = build_financial_periods(user.id, months=12, for_analysis=True)
        monthly = build_monthly_analysis(periods)

        # Expected: exactly 10 months generated
        assert len(monthly["months_data"]) == 10
        assert monthly["months_data"][0]["period"] == "2026-01"
        assert monthly["months_data"][-1]["period"] == "2026-10"

        # No fake 2025-11 or 2025-12
        all_periods = [m["period"] for m in monthly["months_data"]]
        assert "2025-11" not in all_periods
        assert "2025-12" not in all_periods

        # Financial averages are computed cleanly over the 10 real months
        assert monthly["avg_income"] == 50000.0
        assert monthly["avg_expenses"] == 20000.0
        assert monthly["avg_savings"] == 30000.0


# ===========================================================================
# PHASE 10 EDGE CASES 1 THROUGH 10
# ===========================================================================

def test_edge_case_1_brand_new_user_no_data():
    """Edge Case 1: Brand new user with no financial data."""
    period = FinancialPeriod(
        period_id="2026-10",
        fixed_income=0.0,
        variable_income=0.0,
        expenses=[],
        is_current_month=True
    )
    assert get_available_financial_months([period]) == 0
    msg = validate_data_availability([period])
    assert msg == "No financial data available for analysis."

    monthly = build_monthly_analysis([period])
    assert monthly["has_data"] is False
    assert monthly["message"] == "No financial data available for analysis."


def test_edge_case_2_user_one_month_data():
    """Edge Case 2: User with only one month data."""
    period = FinancialPeriod(
        period_id="2026-10",
        fixed_income=50000.0,
        variable_income=0.0,
        expenses=[{'amount': 15000.0, 'category': 'Rent & Housing'}],
        is_current_month=True
    )
    assert get_available_financial_months([period]) == 1
    msg = validate_data_availability([period])
    assert msg == "Not enough financial history for trend analysis."

    monthly = build_monthly_analysis([period])
    assert monthly["has_data"] is False
    assert monthly["message"] == "Not enough financial history for trend analysis."


def test_edge_case_3_user_two_months_data():
    """Edge Case 3: User with two months data (no misleading trend analysis)."""
    p1 = FinancialPeriod(
        period_id="2026-09",
        fixed_income=50000.0,
        variable_income=0.0,
        expenses=[{'amount': 15000.0, 'category': 'Rent & Housing'}]
    )
    p2 = FinancialPeriod(
        period_id="2026-10",
        fixed_income=50000.0,
        variable_income=0.0,
        expenses=[{'amount': 16000.0, 'category': 'Rent & Housing'}],
        is_current_month=True
    )
    assert get_available_financial_months([p1, p2]) == 2
    msg = validate_data_availability([p1, p2])
    assert msg == "Not enough financial history for trend analysis."

    monthly = build_monthly_analysis([p1, p2])
    assert monthly["has_data"] is False
    assert monthly["message"] == "Not enough financial history for trend analysis."


def test_edge_case_4_user_three_months_data():
    """Edge Case 4: User with three months data (full analysis allowed)."""
    p1 = FinancialPeriod(
        period_id="2026-08",
        fixed_income=50000.0,
        variable_income=0.0,
        expenses=[{'amount': 15000.0, 'category': 'Rent & Housing'}]
    )
    p2 = FinancialPeriod(
        period_id="2026-09",
        fixed_income=50000.0,
        variable_income=0.0,
        expenses=[{'amount': 15000.0, 'category': 'Rent & Housing'}]
    )
    p3 = FinancialPeriod(
        period_id="2026-10",
        fixed_income=50000.0,
        variable_income=0.0,
        expenses=[{'amount': 15000.0, 'category': 'Rent & Housing'}],
        is_current_month=True
    )
    assert get_available_financial_months([p1, p2, p3]) == 3
    assert validate_data_availability([p1, p2, p3]) is None

    monthly = build_monthly_analysis([p1, p2, p3])
    assert monthly["has_data"] is True
    assert len(monthly["months_data"]) == 3
    assert monthly["avg_income"] == 50000.0
    assert monthly["avg_expenses"] == 15000.0
    assert monthly["avg_savings"] == 35000.0


def test_edge_case_5_user_ten_month_dataset():
    """Edge Case 5: User with ten month dataset calculates averages on 10 months, NOT 12 calendar padding."""
    periods = []
    for m in range(1, 11):
        p = FinancialPeriod(
            period_id=f"2026-{m:02d}",
            fixed_income=50000.0,
            variable_income=0.0,
            expenses=[{'amount': 20000.0, 'category': 'Rent & Housing'}],
            is_current_month=(m == 10)
        )
        periods.append(p)

    monthly = build_monthly_analysis(periods)
    assert monthly["has_data"] is True
    assert len(monthly["months_data"]) == 10
    # Average Income must be exactly 50,000, NOT 41,666 (50000 * 10 / 12)
    assert monthly["avg_income"] == 50000.0
    assert monthly["avg_expenses"] == 20000.0
    assert monthly["avg_savings"] == 30000.0


def test_edge_case_6_category_appearing_only_in_latest_month():
    """Edge Case 6: Category appearing only in latest month."""
    p1 = FinancialPeriod(
        period_id="2026-08",
        fixed_income=50000.0,
        variable_income=0.0,
        expenses=[{'amount': 10000.0, 'category': 'Rent & Housing'}]
    )
    p2 = FinancialPeriod(
        period_id="2026-09",
        fixed_income=50000.0,
        variable_income=0.0,
        expenses=[{'amount': 10000.0, 'category': 'Rent & Housing'}]
    )
    p3 = FinancialPeriod(
        period_id="2026-10",
        fixed_income=50000.0,
        variable_income=0.0,
        expenses=[
            {'amount': 10000.0, 'category': 'Rent & Housing'},
            {'amount': 5000.0, 'category': 'Travel'}
        ],
        is_current_month=True
    )
    monthly = build_monthly_analysis([p1, p2, p3])
    travel = next(c for c in monthly["category_comparison"] if c["category"] == "Travel")
    assert travel["has_previous_data"] is False
    assert travel["diff"] is None
    assert travel["change_pct"] is None
    assert travel["change_display"] == "No previous data available for comparison."


def test_edge_case_7_category_disappearing_completely():
    """Edge Case 7: Category disappearing completely in latest month."""
    p1 = FinancialPeriod(
        period_id="2026-08",
        fixed_income=50000.0,
        variable_income=0.0,
        expenses=[
            {'amount': 10000.0, 'category': 'Rent & Housing'},
            {'amount': 4000.0, 'category': 'Shopping'}
        ]
    )
    p2 = FinancialPeriod(
        period_id="2026-09",
        fixed_income=50000.0,
        variable_income=0.0,
        expenses=[
            {'amount': 10000.0, 'category': 'Rent & Housing'},
            {'amount': 3000.0, 'category': 'Shopping'}
        ]
    )
    p3 = FinancialPeriod(
        period_id="2026-10",
        fixed_income=50000.0,
        variable_income=0.0,
        expenses=[
            {'amount': 10000.0, 'category': 'Rent & Housing'}
            # Shopping completely disappears (0)
        ],
        is_current_month=True
    )
    monthly = build_monthly_analysis([p1, p2, p3])
    shopping = next(c for c in monthly["category_comparison"] if c["category"] == "Shopping")
    assert shopping["last_month"] == 0.0
    assert shopping["first_month"] == 4000.0
    assert shopping["diff"] == -4000.0
    assert shopping["is_zero_spending"] is True
    assert shopping["change_display"] == "No spending recorded this month"


def test_edge_case_8_fixed_expense_remaining_constant():
    """Edge Case 8: Fixed expense remaining constant (shows 'Stable fixed expense', not 'Rent increased')."""
    periods = []
    for m in range(8, 11):
        p = FinancialPeriod(
            period_id=f"2026-{m:02d}",
            fixed_income=50000.0,
            variable_income=0.0,
            expenses=[{'amount': 12000.0, 'category': 'Rent & Housing'}],
            is_current_month=(m == 10)
        )
        periods.append(p)

    monthly = build_monthly_analysis(periods)
    rent = next(c for c in monthly["category_comparison"] if c["category"] == "Rent & Housing")
    assert rent["diff"] == 0.0
    assert rent["change_display"] == "Stable fixed expense"

    # Verify insights do not state Rent increased
    insights_str = " ".join(monthly["insights"])
    assert "Rent & Housing spending increased" not in insights_str
    assert "Rent & Housing was ₹" not in insights_str
    assert "remained stable at ₹12,000/month" in insights_str


def test_edge_case_9_variable_income_appearing_once():
    """Edge Case 9: Variable income appearing once does not corrupt recurring income trend."""
    periods = []
    for m in range(1, 11):
        var_inc = 15000.0 if m == 3 else 0.0
        p = FinancialPeriod(
            period_id=f"2026-{m:02d}",
            fixed_income=50000.0,
            variable_income=var_inc,
            expenses=[{'amount': 15000.0, 'category': 'Rent & Housing'}],
            is_current_month=(m == 10)
        )
        periods.append(p)

    monthly = build_monthly_analysis(periods)
    insights_str = " ".join(monthly["insights"])
    assert "recurring income remained stable at ₹50,000/month" in insights_str
    assert "₹15,000 in 2026-03" in insights_str
    assert "temporary boosts" in insights_str


def test_edge_case_10_dashboard_and_analysis_matching(app):
    """Edge Case 10: Dashboard and monthly analysis share identical financial periods and metrics."""
    with app.app_context():
        user = User(
            username="test_consistency_user",
            email="consistency@test.com",
            password_hash="hash",
            created_at=date(2026, 1, 1)
        )
        db.session.add(user)
        db.session.commit()

        # Add 5 months of records
        for m in range(1, 6):
            inc = Income(user_id=user.id, amount=60000.0, income_type="Fixed", date=date(2026, m, 1), description="Salary")
            exp = Expense(user_id=user.id, amount=25000.0, category="Rent & Housing", date=date(2026, m, 5), description="Rent")
            db.session.add_all([inc, exp])
        db.session.commit()

        # Fetch for dashboard
        dashboard_periods = build_financial_periods(user.id, months=12, for_analysis=True)
        # Fetch for monthly analysis
        analysis_periods = build_financial_periods(user.id, months=12, for_analysis=True)
        monthly = build_monthly_analysis(analysis_periods)

        assert len(dashboard_periods) == len(monthly["months_data"])
        d_curr = dashboard_periods[-1]
        a_curr = monthly["months_data"][-1]

        # Verify exact alignment between dashboard and analysis
        assert d_curr.period_id == a_curr["period"]
        assert d_curr.total_income == a_curr["income"]
        assert d_curr.total_expenses == a_curr["expenses"]
        assert d_curr.savings == a_curr["savings"]
        assert round(d_curr.savings_rate * 100, 1) == round(a_curr["savings_rate"], 1)


def test_phase6_yearly_analysis_empty_prior_year_protection():
    """Phase 6: Yearly analysis returns 'Insufficient historical data for yearly comparison' when prior period/year has no data."""
    # Simulate user joining in 2026 where first half has 0 data and second half has data (e.g. 3 months in 2026)
    empty_p1 = FinancialPeriod(period_id="2025-10", fixed_income=0.0, variable_income=0.0, expenses=[])
    empty_p2 = FinancialPeriod(period_id="2025-11", fixed_income=0.0, variable_income=0.0, expenses=[])
    empty_p3 = FinancialPeriod(period_id="2025-12", fixed_income=0.0, variable_income=0.0, expenses=[])
    data_p4 = FinancialPeriod(period_id="2026-01", fixed_income=50000.0, variable_income=0.0, expenses=[{'amount': 15000.0, 'category': 'Rent'}])
    data_p5 = FinancialPeriod(period_id="2026-02", fixed_income=50000.0, variable_income=0.0, expenses=[{'amount': 15000.0, 'category': 'Rent'}])
    data_p6 = FinancialPeriod(period_id="2026-03", fixed_income=50000.0, variable_income=0.0, expenses=[{'amount': 15000.0, 'category': 'Rent'}])

    # Without filtering (e.g. if padded periods were supplied), first_half has 0 records
    yearly = build_yearly_analysis([empty_p1, empty_p2, empty_p3, data_p4, data_p5, data_p6])
    assert yearly["has_data"] is False
    assert yearly["message"] == "Insufficient historical data for yearly comparison."
