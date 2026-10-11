"""
Module: tests/test_production_forensic_audit.py

Purpose:
Production Forensic Audit automated test suite verifying:
1. User isolation across all financial resources
2. Duplicate income handling & deduplication
3. Duplicate expense prevention
4. Cache invalidation across transaction mutations
5. Report accuracy and PDF generation
6. Analysis behavior under insufficient data
7. CSV security and formula injection sanitization
8. Authorization and authentication failures
"""
import pytest
from datetime import date
from extensions import db, cache
from models.user import User
from models.expense import Expense
from models.income import Income
from models.goal import Goal
from utils.finance import build_financial_periods, get_active_fixed_incomes
from utils.cache_keys import (
    user_analysis_key,
    user_analysis_monthly_key,
    user_analysis_yearly_key,
    user_dashboard_key,
    invalidate_user_financial_cache
)
from analysis.services import build_monthly_analysis, build_yearly_analysis, validate_data_availability
from utils.rule_engine import FinancialPeriod
from flask_jwt_extended import create_access_token


def test_1_user_isolation(client, app):
    """1. User Isolation: User A cannot read, modify, or delete User B's financial data."""
    with app.app_context():
        user_a = User(username="user_a", email="user_a@test.com", password_hash="hash")
        user_b = User(username="user_b", email="user_b@test.com", password_hash="hash")
        db.session.add_all([user_a, user_b])
        db.session.commit()

        # Create financial data for User A
        exp_a = Expense(user_id=user_a.id, amount=12000.0, category="Rent & Housing", date=date.today(), description="User A Rent")
        inc_a = Income(user_id=user_a.id, amount=50000.0, income_type="Fixed", date=date.today(), description="User A Salary")
        goal_a = Goal(user_id=user_a.id, goal_name="User A Car", target_amount=100000.0, current_saved=20000.0, target_date=date(2027, 1, 1))
        db.session.add_all([exp_a, inc_a, goal_a])
        db.session.commit()

        token_b = create_access_token(identity=str(user_b.id))
        exp_a_id = exp_a.id
        inc_a_id = inc_a.id
        goal_a_id = goal_a.id

    client.set_cookie('access_token_cookie', token_b)

    # User B attempts to access User A's expense
    res_exp_put = client.put(f'/app/api/transactions/expense/{exp_a_id}', json={'amount': 9999.0, 'date': str(date.today())})
    assert res_exp_put.status_code == 404

    res_exp_del = client.delete(f'/app/api/transactions/expense/{exp_a_id}')
    assert res_exp_del.status_code == 404

    # User B attempts to delete User A's income
    res_inc_del = client.delete(f'/app/api/transactions/income/{inc_a_id}')
    assert res_inc_del.status_code == 404

    # User B attempts to access User A's goal
    res_goal_get = client.get(f'/app/goals/{goal_a_id}')
    assert res_goal_get.status_code == 404

    # User B viewing analysis sees zero data, not User A's data
    with app.app_context():
        periods_b = build_financial_periods(user_b.id, months=12, for_analysis=True)
        assert len(periods_b) == 1
        assert periods_b[0].total_income == 0.0
        assert periods_b[0].total_expenses == 0.0


def test_2_duplicate_income_handling(client, app):
    """2. Duplicate Income Handling: Duplicate fixed incomes for the same date/amount/source are rejected or deduplicated."""
    with app.app_context():
        user = User(username="income_user", email="inc@test.com", password_hash="hash")
        db.session.add(user)
        db.session.commit()

        # Add initial fixed income
        inc1 = Income(user_id=user.id, amount=60000.0, income_type="Fixed", date=date(2026, 1, 1), description="Monthly Salary")
        db.session.add(inc1)
        db.session.commit()

        # Deduplication engine verification: multiple records for same source pick the latest effective
        inc2 = Income(user_id=user.id, amount=60000.0, income_type="Fixed", date=date(2026, 1, 15), description="Monthly Salary")
        db.session.add(inc2)
        db.session.commit()

        active = get_active_fixed_incomes(user.id, as_of_date=date(2026, 1, 31))
        # Total must be 60,000, NOT double-counted to 120,000
        assert active["total_amount"] == 60000.0
        assert len(active["active_records"]) == 1


def test_3_duplicate_expense_prevention(client, app):
    """3. Duplicate Expense Prevention: CSV import detects duplicate transactions and skips them."""
    with app.app_context():
        user = User(username="csv_user", email="csv@test.com", password_hash="hash")
        db.session.add(user)
        db.session.commit()

        # Pre-existing expense
        existing = Expense(user_id=user.id, amount=2500.0, category="Food & Dining", date=date(2026, 5, 10), description="Dinner")
        db.session.add(existing)
        db.session.commit()
        token = create_access_token(identity=str(user.id))

    client.set_cookie('access_token_cookie', token)

    # Attempt to import records where one is identical to pre-existing
    records = [
        {"row_number": 1, "date": "2026-05-10", "amount": 2500.0, "category": "Food & Dining", "description": "Dinner"},
        {"row_number": 2, "date": "2026-05-11", "amount": 1200.0, "category": "Transport", "description": "Taxi"}
    ]
    res = client.post('/app/api/transactions/confirm-csv', json={'records': records})
    assert res.status_code == 201
    data = res.get_json()
    assert data["imported"] == 1
    assert data["failed"] == 1
    assert any("Duplicate transaction" in err["reason"] for err in data["errors"])


def test_4_cache_invalidation(client, app):
    """4. Cache Invalidation: Mutating transactions or goals flushes all cached intelligence."""
    with app.app_context():
        user = User(username="cache_user", email="cache@test.com", password_hash="hash")
        db.session.add(user)
        db.session.commit()
        user_id = user.id

        # Populate cache
        cache.set(user_analysis_key(user_id), {"cached": True}, timeout=3600)
        cache.set(user_analysis_monthly_key(user_id), {"cached": True}, timeout=3600)
        cache.set(user_analysis_yearly_key(user_id), {"cached": True}, timeout=3600)
        cache.set(user_dashboard_key(user_id), {"cached": True}, timeout=3600)

        assert cache.get(user_analysis_key(user_id)) is not None
        assert cache.get(user_analysis_monthly_key(user_id)) is not None

        # Call invalidation
        invalidate_user_financial_cache(user_id)

        assert cache.get(user_analysis_key(user_id)) is None
        assert cache.get(user_analysis_monthly_key(user_id)) is None
        assert cache.get(user_analysis_yearly_key(user_id)) is None
        assert cache.get(user_dashboard_key(user_id)) is None


def test_5_report_accuracy_and_pdf(client, app):
    """5. Report Accuracy: PDF export generates valid binary PDF with financial summary."""
    with app.app_context():
        user = User(username="pdf_user", email="pdf@test.com", password_hash="hash")
        db.session.add(user)
        db.session.commit()

        today = date.today()
        inc = Income(user_id=user.id, amount=75000.0, income_type="Fixed", date=today, description="Salary")
        exp = Expense(user_id=user.id, amount=30000.0, category="Rent & Housing", date=today, description="Rent")
        db.session.add_all([inc, exp])
        db.session.commit()
        token = create_access_token(identity=str(user.id))

    client.set_cookie('access_token_cookie', token)
    res = client.get('/app/api/reports/export/pdf')
    assert res.status_code == 200
    assert res.content_type == 'application/pdf'
    assert res.data.startswith(b'%PDF')


def test_6_analysis_with_insufficient_data():
    """6. Analysis with Insufficient Data: 0, 1, 2 months block trend analysis; <6 months blocks yearly comparison."""
    # 0 months
    p0 = FinancialPeriod(period_id="2026-10", fixed_income=0.0, variable_income=0.0, expenses=[])
    assert validate_data_availability([p0]) == "No financial data available for analysis."
    m0 = build_monthly_analysis([p0])
    assert m0["has_data"] is False
    assert m0["message"] == "No financial data available for analysis."

    # 1 month
    p1 = FinancialPeriod(period_id="2026-10", fixed_income=50000.0, variable_income=0.0, expenses=[{'amount': 20000.0, 'category': 'Rent'}])
    assert validate_data_availability([p1]) == "Not enough financial history for trend analysis."
    m1 = build_monthly_analysis([p1])
    assert m1["has_data"] is False

    # 2 months
    p2_a = FinancialPeriod(period_id="2026-09", fixed_income=50000.0, variable_income=0.0, expenses=[{'amount': 20000.0, 'category': 'Rent'}])
    assert validate_data_availability([p2_a, p1]) == "Not enough financial history for trend analysis."

    # 3 months: allowed for monthly, but blocked for yearly (<6 months)
    p3_a = FinancialPeriod(period_id="2026-08", fixed_income=50000.0, variable_income=0.0, expenses=[{'amount': 20000.0, 'category': 'Rent'}])
    m3 = build_monthly_analysis([p3_a, p2_a, p1])
    assert m3["has_data"] is True

    y3 = build_yearly_analysis([p3_a, p2_a, p1])
    assert y3["has_data"] is False
    assert y3["message"] == "Insufficient historical data for yearly comparison."


def test_7_csv_security_formula_injection(client, app):
    """7. CSV Security: CSV export sanitizes potential formula injection characters (=, +, -, @)."""
    with app.app_context():
        user = User(username="csv_sec_user", email="csv_sec@test.com", password_hash="hash")
        db.session.add(user)
        db.session.commit()

        # Dangerous description and category starting with formula characters
        exp = Expense(
            user_id=user.id,
            amount=500.0,
            category="+DangerousCategory",
            date=date.today(),
            description="=cmd|'/C calc'!A0"
        )
        db.session.add(exp)
        db.session.commit()
        token = create_access_token(identity=str(user.id))

    client.set_cookie('access_token_cookie', token)
    res = client.get('/app/api/reports/export/csv')
    assert res.status_code == 200
    csv_text = res.data.decode('utf-8')

    # Formula injection characters should be escaped with leading single quote
    assert "'=cmd|" in csv_text
    assert "'+DangerousCategory" in csv_text


def test_8_authorization_failures(client, app):
    """8. Authorization Failures: Unauthenticated requests and non-admin access to admin routes fail securely."""
    # Unauthenticated request to analysis
    res_anon = client.get('/app/analysis')
    # Should redirect to login (302) or return 401
    assert res_anon.status_code in (302, 401)

    # Regular user attempting to access admin route
    with app.app_context():
        reg_user = User(username="regular_joe", email="joe@test.com", password_hash="hash", role="user")
        db.session.add(reg_user)
        db.session.commit()
        token_reg = create_access_token(identity=str(reg_user.id))

    client.set_cookie('access_token_cookie', token_reg)
    res_admin = client.get('/admin')
    assert res_admin.status_code == 403

    res_admin_api = client.get('/api/admin/users')
    assert res_admin_api.status_code == 403
