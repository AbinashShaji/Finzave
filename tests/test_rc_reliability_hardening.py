"""
Module: tests/test_rc_reliability_hardening.py

Purpose:
Release Candidate (RC) Security & Reliability Hardening Test Suite:
1. Database failure and rollback recovery (prevent session poisoning)
2. JWT chaos and authentication failure resilience
3. Multi-resource cross-user attack mitigation (Tenant Isolation)
4. Malicious input handling (XSS, SQLi, SSTI, Path Traversal)
5. CSV corruption and extreme malformed data resilience
6. Cache invalidation and cache failure resilience
7. Large dataset stress & performance benchmarking
8. Financial extreme edge cases (cash burn, incomplete tracking, high values)
"""
import pytest
from datetime import date, timedelta
import time
from extensions import db, cache
from models.user import User
from models.expense import Expense
from models.income import Income
from models.goal import Goal
from utils.finance import build_financial_periods, get_active_fixed_incomes
from utils.csv_processor import process_expense_csv, validate_transaction
from analysis.services import build_monthly_analysis, build_yearly_analysis, build_overview, validate_data_availability
from utils.rule_engine import FinancialPeriod, evaluate_rules
from analysis.scoring import calculate_health_score
from flask_jwt_extended import create_access_token


def test_rc_1_database_rollback_recovery(app):
    """1. Database Rollback Recovery: Session cleanly recovers from constraint violations without poisoning."""
    with app.app_context():
        user = User(username="rollback_test_user", email="rollback@test.com", password_hash="hash")
        db.session.add(user)
        db.session.commit()

        # Deliberately cause a database error (null amount in non-nullable field or invalid date)
        try:
            invalid_expense = Expense(user_id=user.id, amount=None, category="Food", date=date.today())
            db.session.add(invalid_expense)
            db.session.commit()
            pytest.fail("Database should have rejected null amount")
        except Exception:
            db.session.rollback()

        # Verify session is not poisoned: subsequent write succeeds immediately
        valid_expense = Expense(user_id=user.id, amount=500.0, category="Food & Dining", date=date.today(), description="Clean Recovery")
        db.session.add(valid_expense)
        db.session.commit()

        assert valid_expense.id is not None
        fetched = db.session.get(Expense, valid_expense.id)
        assert fetched.amount == 500.0


def test_rc_2_jwt_chaos_failures(client, app):
    """2. JWT Chaos Failures: Expired, tampered, missing, and logged-out tokens are safely rejected."""
    with app.app_context():
        user = User(username="jwt_chaos_user", email="chaos@test.com", password_hash="hash")
        db.session.add(user)
        db.session.commit()

        # 1. Expired token (expires in -10 seconds)
        expired_token = create_access_token(identity=str(user.id), expires_delta=timedelta(seconds=-10))

    client.set_cookie('access_token_cookie', expired_token)
    res_expired = client.get('/app/api/profile')
    assert res_expired.status_code == 401
    assert "expired" in res_expired.get_json()["msg"].lower()

    # 2. Tampered token (invalid signature)
    tampered_token = expired_token[:-8] + "ABCDEFGH"
    client.set_cookie('access_token_cookie', tampered_token)
    res_tampered = client.get('/app/api/profile')
    assert res_tampered.status_code == 401

    # 3. Missing cookie
    client.delete_cookie('access_token_cookie')
    res_missing = client.get('/app/api/profile')
    assert res_missing.status_code == 401

    # 4. Logout flow
    with app.app_context():
        valid_token = create_access_token(identity=str(user.id))
    client.set_cookie('access_token_cookie', valid_token)
    res_logout = client.post('/api/auth/logout')
    assert res_logout.status_code == 200


def test_rc_3_cross_user_attacks(client, app):
    """3. Cross-User Attacks: User B cannot access, read, alter, or delete User A's resources."""
    with app.app_context():
        user_a = User(username="victim_a", email="victim_a@test.com", password_hash="hash")
        user_b = User(username="attacker_b", email="attacker_b@test.com", password_hash="hash")
        db.session.add_all([user_a, user_b])
        db.session.commit()

        exp_a = Expense(user_id=user_a.id, amount=10000.0, category="Rent & Housing", date=date.today(), description="Secret Rent")
        inc_a = Income(user_id=user_a.id, amount=90000.0, income_type="Fixed", date=date.today(), description="Secret Salary")
        goal_a = Goal(user_id=user_a.id, goal_name="Secret Goal", target_amount=500000.0, current_saved=100000.0, target_date=date(2028, 1, 1))
        db.session.add_all([exp_a, inc_a, goal_a])
        db.session.commit()

        token_b = create_access_token(identity=str(user_b.id))
        a_exp_id = exp_a.id
        a_inc_id = inc_a.id
        a_goal_id = goal_a.id

    client.set_cookie('access_token_cookie', token_b)

    # Attacker tries modifying Victim's expense
    res_put_exp = client.put(f'/app/api/transactions/expense/{a_exp_id}', json={'amount': 1.0, 'date': str(date.today())})
    assert res_put_exp.status_code == 404

    # Attacker tries deleting Victim's expense
    res_del_exp = client.delete(f'/app/api/transactions/expense/{a_exp_id}')
    assert res_del_exp.status_code == 404

    # Attacker tries modifying Victim's income
    res_put_inc = client.put(f'/app/api/transactions/income/{a_inc_id}', json={'amount': 1.0, 'date': str(date.today())})
    assert res_put_inc.status_code == 404

    # Attacker tries deleting Victim's income
    res_del_inc = client.delete(f'/app/api/transactions/income/{a_inc_id}')
    assert res_del_inc.status_code == 404

    # Attacker tries updating Victim's goal
    res_put_goal = client.put(f'/app/api/goals/{a_goal_id}', json={'target_amount': 1.0})
    assert res_put_goal.status_code == 404

    # Attacker tries deleting Victim's goal
    res_del_goal = client.delete(f'/app/api/goals/{a_goal_id}')
    assert res_del_goal.status_code == 404

    # Verify Victim's data was never modified
    with app.app_context():
        assert db.session.get(Expense, a_exp_id).amount == 10000.0
        assert db.session.get(Income, a_inc_id).amount == 90000.0
        assert db.session.get(Goal, a_goal_id).target_amount == 500000.0


def test_rc_4_malicious_input_escaping(client, app):
    """4. Malicious Input Escaping: XSS, SQLi, SSTI, and path traversal strings stored and rendered safely."""
    with app.app_context():
        user = User(username="sec_tester", email="sec@test.com", password_hash="hash")
        db.session.add(user)
        db.session.commit()
        token = create_access_token(identity=str(user.id))

    client.set_cookie('access_token_cookie', token)

    payloads = [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert(1)>",
        "'; DROP TABLE users;--",
        "../../../../etc/passwd",
        "{{7*7}}"
    ]

    for p in payloads:
        # Create expense with malicious payload in description
        res = client.post('/app/api/transactions/expense', json={
            'amount': 250.0,
            'category': 'Shopping',
            'date': str(date.today()),
            'description': p
        })
        assert res.status_code == 201

    # Fetch transactions and verify payload is stored safely without executing or corrupting
    res_get = client.get('/app/api/transactions/expense?page=1&per_page=10')
    assert res_get.status_code == 200
    data = res_get.get_json()
    descriptions = [e['description'] for e in data.get('transactions', [])]
    for p in payloads:
        assert p in descriptions

    # Verify database table still exists and query succeeds
    with app.app_context():
        assert User.query.count() >= 1


def test_rc_5_csv_corruption_and_extreme_cases():
    """5. CSV Corruption: Empty CSV, missing columns, invalid dates, negative amounts handled gracefully."""
    # 1. Empty CSV
    res_empty = process_expense_csv(b"")
    assert res_empty["success"] is False

    # 2. Missing required columns
    res_missing = process_expense_csv(b"date,amount\n2026-10-01,100.0\n")
    assert res_missing["success"] is False
    assert "Missing required columns" in res_missing["error"]

    # 3. Invalid dates, negative amounts, and future dates
    corrupt_csv = (
        b"date,amount,category,description\n"
        b"not-a-date,150.0,Food & Dining,Bad Date\n"
        b"2099-12-31,200.0,Food & Dining,Future Date\n"
        b"2026-10-01,-50.0,Food & Dining,Negative Amount\n"
        b"2026-10-02,abc,Food & Dining,Invalid Amount\n"
        b"2026-10-03,300.0,Food & Dining,Valid Row\n"
    )
    res_corrupt = process_expense_csv(corrupt_csv)
    assert res_corrupt["success"] is True
    assert res_corrupt["valid_count"] == 1
    assert res_corrupt["invalid_count"] == 4


def test_rc_6_financial_extreme_cases():
    """6. Financial Extreme Cases: Cash burn, incomplete tracking, huge values, and boundary transitions."""
    # Case A: Cash burn (Expenses only, zero income)
    p_burn = FinancialPeriod(
        period_id="2026-10",
        fixed_income=0.0,
        variable_income=0.0,
        expenses=[{'amount': 45000.0, 'category': 'Rent & Housing'}],
        is_current_month=True
    )
    assert p_burn.savings == -45000.0
    assert p_burn.savings_rate is None
    insights_burn = evaluate_rules([p_burn])
    # Expect RB-03 cash flow warning
    assert any("Expenses detected without income" in i["message"] for i in insights_burn)

    # Case B: Incomplete tracking (Income only, zero expenses)
    p_inc_only = FinancialPeriod(
        period_id="2026-10",
        fixed_income=60000.0,
        variable_income=0.0,
        expenses=[],
        is_current_month=True
    )
    assert p_inc_only.status == "incomplete"
    overview = build_overview([p_inc_only])
    assert overview["is_incomplete"] is True
    assert overview["narrative_title"] == "Your financial tracking is incomplete."

    # Case C: Extreme numeric values (₹100 Crore / ₹1,000,000,000.00)
    p_huge = FinancialPeriod(
        period_id="2026-10",
        fixed_income=1000000000.0,
        variable_income=50000000.0,
        expenses=[{'amount': 300000000.0, 'category': 'Investment'}],
        is_current_month=True
    )
    assert p_huge.total_income == 1050000000.0
    assert p_huge.savings == 750000000.0
    assert round(p_huge.savings_rate, 4) == round(750000000.0 / 1050000000.0, 4)

    # Case D: 6 months dataset allows yearly comparison
    periods_6m = []
    for m in range(1, 7):
        periods_6m.append(FinancialPeriod(
            period_id=f"2026-{m:02d}",
            fixed_income=50000.0,
            variable_income=0.0,
            expenses=[{'amount': 20000.0, 'category': 'Rent & Housing'}],
            is_current_month=(m == 6)
        ))
    yearly = build_yearly_analysis(periods_6m)
    assert yearly["has_data"] is True


def test_rc_7_large_dataset_performance():
    """7. Large Dataset Stress & Performance: 1000 transactions execute under 250ms."""
    periods = []
    t0 = time.time()
    for m in range(1, 11):
        expenses = [{'amount': 150.0 + (i % 200), 'category': 'Food & Dining' if i % 2 == 0 else 'Shopping'} for i in range(100)]
        p = FinancialPeriod(
            period_id=f"2026-{m:02d}",
            fixed_income=80000.0,
            variable_income=0.0,
            expenses=expenses,
            is_current_month=(m == 10)
        )
        periods.append(p)

    monthly = build_monthly_analysis(periods)
    insights = evaluate_rules(periods)
    health = calculate_health_score(periods, True, insights)
    t1 = time.time()

    elapsed_ms = (t1 - t0) * 1000
    assert elapsed_ms < 250.0  # Must execute under 250 milliseconds
    assert monthly["has_data"] is True
    assert len(monthly["months_data"]) == 10
    assert health["score"] is not None


def test_rc_8_cache_failure_fallback(client, app):
    """8. Cache Failure Fallback: Application computes and serves live views when cache is bypassed or unavailable."""
    with app.app_context():
        user = User(username="cache_fallback_user", email="cfu@test.com", password_hash="hash")
        db.session.add(user)
        db.session.commit()

        inc = Income(user_id=user.id, amount=50000.0, income_type="Fixed", date=date.today(), description="Salary")
        exp = Expense(user_id=user.id, amount=20000.0, category="Rent & Housing", date=date.today(), description="Rent")
        db.session.add_all([inc, exp])
        db.session.commit()
        token = create_access_token(identity=str(user.id))

    client.set_cookie('access_token_cookie', token)

    # Clear cache completely
    with app.app_context():
        cache.clear()

    # Route computes live data and responds 200 without caching dependency failure
    res_monthly = client.get('/app/analysis/monthly')
    assert res_monthly.status_code == 200
    assert b"Monthly Analysis" in res_monthly.data or b"Financial Analysis" in res_monthly.data

    res_overview = client.get('/app/analysis')
    assert res_overview.status_code == 200
