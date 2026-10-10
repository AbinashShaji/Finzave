"""
Module: tests/test_finance.py

Purpose:
Contains Pytest test cases ensuring application stability.

Flow:
User Request -> Route Handler -> Business Logic -> Database

"""
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


def test_high_saver_with_12_months_history():
    """1. High saver with 12 months history: Expected score Excellent."""
    from analysis.scoring import calculate_health_score, calculate_data_confidence
    periods = []
    for m in range(1, 13):
        p = FinancialPeriod(
            period_id=f"2025-{m:02d}",
            fixed_income=100000.0,
            variable_income=0.0,
            expenses=[
                {'amount': 15000.0, 'category': 'Rent & Housing'},
                {'amount': 5000.0, 'category': 'Mutual Funds'}  # Investment dimension present
            ],
            is_current_month=(m == 12)
        )
        periods.append(p)

    confidence = calculate_data_confidence(periods)
    res = calculate_health_score(periods, True, [])
    assert confidence == 1.0
    assert res["raw_score"] >= 95
    assert res["score"] >= 95
    assert res["category"] == "Excellent"


def test_new_user_with_only_1_month_history():
    """2. New user with only 1 month history: Confidence adjustment prevents premature 100/100."""
    from analysis.scoring import calculate_health_score, calculate_data_confidence
    p = FinancialPeriod(
        period_id="2026-10",
        fixed_income=100000.0,
        variable_income=0.0,
        expenses=[{'amount': 20000.0, 'category': 'Rent & Housing'}],
        is_current_month=True
    )
    confidence = calculate_data_confidence([p])
    res = calculate_health_score([p], True, [])
    assert confidence <= 0.65
    assert res["category"] != "Excellent"
    assert res["score"] <= 65


def test_salary_plus_freelance_income():
    """3. Salary + freelance income: Recognizes recurring stability and variable bonus."""
    from analysis.services import build_yearly_analysis
    periods = []
    for m in range(1, 11):
        var_inc = 10000.0 if m == 1 else 0.0
        p = FinancialPeriod(
            period_id=f"2026-{m:02d}",
            fixed_income=50000.0,
            variable_income=var_inc,
            expenses=[{'amount': 17200.0, 'category': 'Rent & Housing'}],
            is_current_month=(m == 10)
        )
        periods.append(p)

    yearly = build_yearly_analysis(periods)
    assert yearly["h1_data"]["fixed_income"] == 250000.0
    assert yearly["h1_data"]["variable_income"] == 10000.0
    assert yearly["h2_data"]["fixed_income"] == 250000.0
    assert yearly["h2_data"]["variable_income"] == 0.0
    # Check context-aware explanations
    insights_str = " ".join(yearly["long_term_insights"])
    assert "freelance" in insights_str.lower()
    assert "50,000" in insights_str


def test_multiple_fixed_incomes():
    """4. Multiple fixed incomes: Preserves combined recurring salary sources."""
    p = FinancialPeriod(
        period_id="2026-10",
        fixed_income=70000.0,  # e.g., Salary A 40,000 + Salary B 30,000
        variable_income=0.0,
        expenses=[{'amount': 20000.0, 'category': 'Living'}],
        is_current_month=True
    )
    assert p.fixed_income == 70000.0
    assert p.total_income == 70000.0


def test_zero_income_with_expenses():
    """5. Zero income with expenses: Triggers cash flow burn warning and low health score."""
    from utils.rule_engine import evaluate_rules
    from analysis.scoring import calculate_health_score
    p = FinancialPeriod(
        period_id="2026-10",
        fixed_income=0.0,
        variable_income=0.0,
        expenses=[{'amount': 25000.0, 'category': 'Living'}],
        is_current_month=True
    )
    insights = evaluate_rules([p])
    assert any("Expenses detected without income" in i["message"] for i in insights)
    
    score_res = calculate_health_score([p], True, insights)
    assert score_res["category"] == "Needs Improvement"
    assert score_res["score"] < 25


def test_fixed_rent_with_reduced_variable_spending():
    """6. Fixed rent with reduced variable spending: Safeguards against false concentration warning."""
    from utils.rule_engine import evaluate_rules
    p1 = FinancialPeriod(
        period_id="2026-09",
        fixed_income=50000.0,
        variable_income=0.0,
        expenses=[
            {'amount': 12000.0, 'category': 'Rent & Housing'},
            {'amount': 15000.0, 'category': 'Shopping'}
        ]
    )
    p2 = FinancialPeriod(
        period_id="2026-10",
        fixed_income=50000.0,
        variable_income=0.0,
        expenses=[
            {'amount': 12000.0, 'category': 'Rent & Housing'},
            {'amount': 2000.0, 'category': 'Shopping'}
        ],
        is_current_month=True
    )
    insights = evaluate_rules([p1, p2])
    # Rent is 12000 / 14000 = 85.7% of expenses, but stable.
    # Must NOT trigger false RB-02 or RB-07 concentration warning for Rent & Housing.
    rent_warnings = [i for i in insights if i.get("rule_id") in ("RB-02", "RB-07") and "Rent & Housing" in i["message"]]
    assert len(rent_warnings) == 0


def test_fixed_income_deduplication_database(app):
    """Test that multiple historical fixed income entries for the same source do not accumulate."""
    from datetime import date
    from extensions import db
    from models.user import User
    from models.income import Income
    from utils.finance import get_active_fixed_incomes

    with app.app_context():
        user = User(username='test_dedup_user', email='dedup@test.com')
        user.set_password('Password123!')
        db.session.add(user)
        db.session.commit()

        # Jan Salary: 50,000
        inc1 = Income(user_id=user.id, amount=50000.0, income_type='Fixed', date=date(2026, 1, 1), description='Salary')
        # Feb Salary update: 55,000
        inc2 = Income(user_id=user.id, amount=55000.0, income_type='Fixed', date=date(2026, 2, 1), description='Salary')
        db.session.add_all([inc1, inc2])
        db.session.commit()

        # As of Feb 15, active salary must be 55,000 (latest), NOT 105,000
        active = get_active_fixed_incomes(user.id, date(2026, 2, 15))
        assert active['total_amount'] == 55000.0
        assert len(active['active_records']) == 1
        assert active['active_records'][0]['amount'] == 55000.0


def test_multiple_fixed_sources_database(app):
    """Test that distinct fixed income sources remain separate and sum together."""
    from datetime import date
    from extensions import db
    from models.user import User
    from models.income import Income
    from utils.finance import get_active_fixed_incomes

    with app.app_context():
        user = User(username='test_multi_sources', email='sources@test.com')
        user.set_password('Password123!')
        db.session.add(user)
        db.session.commit()

        inc1 = Income(user_id=user.id, amount=50000.0, income_type='Fixed', date=date(2026, 1, 1), description='Salary')
        inc2 = Income(user_id=user.id, amount=10000.0, income_type='Fixed', date=date(2026, 1, 15), description='Rental Income')
        db.session.add_all([inc1, inc2])
        db.session.commit()

        active = get_active_fixed_incomes(user.id, date(2026, 2, 1))
        assert active['total_amount'] == 60000.0
        assert len(active['active_records']) == 2

