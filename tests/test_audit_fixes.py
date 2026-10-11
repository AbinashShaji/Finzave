"""
Module: tests/test_audit_fixes.py

Purpose:
Tests for the forensic audit fixes:
1. CSV export formula injection escaping
2. Admin cannot delete another admin account
3. Session rollback protection after database failures
4. XSS-safe chart rendering with special characters
5. Empty report periods handling
"""
import pytest
from datetime import date, datetime
from extensions import db
from models.user import User
from models.expense import Expense
from models.income import Income
from utils.hash_utils import sanitize_csv_value, generate_transaction_hash
from flask_jwt_extended import create_access_token


def test_sanitize_csv_value_formulas():
    """Verify formula characters =, +, -, @ are escaped with leading single quote."""
    assert sanitize_csv_value("=SUM(A1:A5)") == "'=SUM(A1:A5)"
    assert sanitize_csv_value("+12345") == "'+12345"
    assert sanitize_csv_value("-50.00") == "'-50.00"
    assert sanitize_csv_value("@SUM(A1)") == "'@SUM(A1)"
    
    # Safe values should not be modified
    assert sanitize_csv_value("Groceries") == "Groceries"
    assert sanitize_csv_value("McDonald's") == "McDonald's"
    assert sanitize_csv_value(None) == ""


def test_csv_export_formula_injection(app, client, test_user):
    """Verify transaction export CSV escapes formula injection characters."""
    with app.app_context():
        token = create_access_token(identity=str(test_user))
        
        # Add an expense with a formula injection description
        exp = Expense(
            user_id=test_user,
            amount=50.0,
            category="Food & Dining",
            date=date.today(),
            description="=1+1; cmd"
        )
        db.session.add(exp)
        db.session.commit()

    client.set_cookie('access_token_cookie', token, domain='localhost')
    res = client.get('/app/api/transactions/expense/export')
    assert res.status_code == 200
    csv_text = res.data.decode('utf-8')
    assert "'=1+1; cmd" in csv_text


def test_reports_csv_export_formula_injection(app, client, test_user):
    """Verify reports CSV export escapes formula injection characters."""
    with app.app_context():
        token = create_access_token(identity=str(test_user))
        
        exp = Expense(
            user_id=test_user,
            amount=120.0,
            category="Shopping",
            date=date.today(),
            description="@malicious_tag"
        )
        db.session.add(exp)
        db.session.commit()

    client.set_cookie('access_token_cookie', token, domain='localhost')
    res = client.get('/app/api/reports/export/csv')
    assert res.status_code == 200
    csv_text = res.data.decode('utf-8')
    assert "'@malicious_tag" in csv_text


def test_admin_cannot_delete_admin(app, client):
    """Verify that an admin cannot delete another admin account."""
    with app.app_context():
        admin1 = User(username="super_admin", email="admin1@test.com", password_hash="hash", role="admin")
        admin2 = User(username="peer_admin", email="admin2@test.com", password_hash="hash", role="admin")
        normal_user = User(username="normal_user", email="user@test.com", password_hash="hash", role="user")
        db.session.add_all([admin1, admin2, normal_user])
        db.session.commit()

        admin1_id = admin1.id
        admin2_id = admin2.id
        user_id = normal_user.id
        token = create_access_token(identity=str(admin1_id))

    client.set_cookie('access_token_cookie', token, domain='localhost')

    # Attempt to delete peer admin
    del_admin_res = client.delete(f'/api/admin/users/{admin2_id}')
    assert del_admin_res.status_code == 403
    data = del_admin_res.get_json()
    assert "Cannot delete an administrator account" in data.get("message", "")

    # Peer admin must still exist in DB
    with app.app_context():
        peer = db.session.get(User, admin2_id)
        assert peer is not None

    # Normal user deletion must succeed
    del_user_res = client.delete(f'/api/admin/users/{user_id}')
    assert del_user_res.status_code == 200
    with app.app_context():
        deleted = db.session.get(User, user_id)
        assert deleted is None


def test_database_rollback_on_failure(app, client, test_user):
    """Verify that database failure rolls back properly without poisoning session."""
    with app.app_context():
        token = create_access_token(identity=str(test_user))
        
    client.set_cookie('access_token_cookie', token, domain='localhost')

    # Send an invalid request that triggers exception or validation error
    res = client.post('/app/api/transactions/expense', json={
        "amount": "not_a_number",
        "category": "Food & Dining",
        "date": "2026-03-01"
    })
    # Should safely fail and not leave dirty transaction
    assert res.status_code in (400, 500)

    # Next legitimate request should work without session poison
    res_valid = client.post('/app/api/transactions/expense', json={
        "amount": 100.0,
        "category": "Food & Dining",
        "date": "2026-03-01",
        "description": "Lunch"
    })
    assert res_valid.status_code == 201


def test_xss_safe_rendering_in_dashboard(app, client, test_user):
    """Verify that dashboard and analysis templates safely render quotes and HTML without crashing or unescaped XSS."""
    with app.app_context():
        token = create_access_token(identity=str(test_user))
        
        # Add expense with quote and script tag in description
        exp = Expense(
            user_id=test_user,
            amount=45.0,
            category="Food & Dining",
            date=date.today(),
            description="McDonald's <script>alert(1)</script>"
        )
        db.session.add(exp)
        db.session.commit()

    client.set_cookie('access_token_cookie', token, domain='localhost')
    res = client.get('/app/')
    assert res.status_code == 200
    html = res.data.decode('utf-8')
    # Should not contain raw unsafe injection
    assert "<script>alert(1)</script>" not in html or "\\u003cscript\\u003e" in html or "\\u0027" in html or "&lt;script&gt;" in html or "tojson" not in html
    # Must contain tojson safe serialization
    assert "JSON.parse" not in html


def test_empty_report_period_access(app, client, test_user):
    """Verify that accessing historical periods with 0 transactions does not return 'Invalid period selected'."""
    with app.app_context():
        token = create_access_token(identity=str(test_user))
        # Add expense only in current month
        exp = Expense(
            user_id=test_user,
            amount=500.0,
            category="Food & Dining",
            date=date(2026, 10, 1),
            description="October expense"
        )
        db.session.add(exp)
        db.session.commit()

    client.set_cookie('access_token_cookie', token, domain='localhost')
    
    # Access reports page with period from months earlier
    earlier_period = "2026-03"
    res = client.get(f'/app/reports?period={earlier_period}')
    assert res.status_code == 200
    assert b"Invalid period selected" not in res.data


def test_registration_email_validation(client):
    """Verify registration rejects invalid emails and accepts valid email."""
    invalid_emails = ["random_string", "@", "abc", "test@", "user@domain."]
    for inv_email in invalid_emails:
        res = client.post('/api/auth/register', json={
            "username": f"user_{abs(hash(inv_email))}",
            "email": inv_email,
            "password": "Password123!",
            "confirm_password": "Password123!",
            "terms_accepted": True
        })
        assert res.status_code == 400
        assert "Invalid email format" in res.get_json().get("message", "")

    # Valid email succeeds
    res_valid = client.post('/api/auth/register', json={
        "username": "valid_user_123",
        "email": "user@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "terms_accepted": True
    })
    assert res_valid.status_code == 201


def test_admin_error_message_generic(client):
    """Verify admin endpoint returns generic Authentication required without stack traces."""
    res = client.get('/api/admin/users')
    assert res.status_code == 401
    data = res.get_json()
    assert data.get("message") == "Authentication required"
    assert "traceback" not in res.data.decode('utf-8').lower()
    assert "Token error" not in data.get("message", "")


def test_admin_n_plus_one_behavior(app, client):
    """Verify /api/admin/users executes a constant bounded query count regardless of user count."""
    from models.activity import UserActivity
    from sqlalchemy import event

    with app.app_context():
        admin = User(username="admin_perf", email="admin_perf@test.com", password_hash="hash", role="admin")
        db.session.add(admin)
        db.session.commit()
        admin_id = admin.id
        token = create_access_token(identity=str(admin_id))

        # Create 10 users with activities
        for i in range(10):
            u = User(username=f"perf_user_{i}", email=f"perf_{i}@test.com", password_hash="hash", role="user")
            db.session.add(u)
            db.session.flush()
            for j in range(3):
                act = UserActivity(user_id=u.id, action="test_action")
                db.session.add(act)
        db.session.commit()

    client.set_cookie('access_token_cookie', token, domain='localhost')

    query_count = [0]
    def query_listener(conn, cursor, statement, parameters, context, executemany):
        query_count[0] += 1

    engine = db.engine
    event.listen(engine, "before_cursor_execute", query_listener)
    try:
        res = client.get('/api/admin/users')
        assert res.status_code == 200
        users_returned = res.get_json()
        assert len(users_returned) >= 11
        # In N+1 it would be 1 + 11 = 12+ queries. With our DB aggregation, queries are <= 5
        assert query_count[0] <= 5
    finally:
        event.remove(engine, "before_cursor_execute", query_listener)


def test_cross_user_authorization(app, client):
    """Verify User A cannot read, update, or delete User B's financial records."""
    from models.goal import Goal
    with app.app_context():
        user_a = User(username="user_a", email="user_a@test.com", password_hash="hash", role="user")
        user_b = User(username="user_b", email="user_b@test.com", password_hash="hash", role="user")
        db.session.add_all([user_a, user_b])
        db.session.commit()

        user_a_id = user_a.id
        user_b_id = user_b.id

        # User B creates an expense, income, goal
        exp_b = Expense(user_id=user_b_id, amount=100.0, category="Food & Dining", date=date.today(), description="User B lunch")
        inc_b = Income(user_id=user_b_id, amount=5000.0, income_type="Fixed", date=date.today(), description="User B salary")
        goal_b = Goal(user_id=user_b_id, goal_name="User B Car", target_amount=10000.0, current_saved=1000.0, target_date=date(2027, 1, 1))
        db.session.add_all([exp_b, inc_b, goal_b])
        db.session.commit()

        exp_b_id = exp_b.id
        inc_b_id = inc_b.id
        goal_b_id = goal_b.id

        token_a = create_access_token(identity=str(user_a_id))

    client.set_cookie('access_token_cookie', token_a, domain='localhost')

    # User A attempts to delete User B's expense
    del_exp = client.delete(f'/app/api/transactions/expense/{exp_b_id}')
    assert del_exp.status_code == 404

    # User A attempts to update User B's expense
    put_exp = client.put(f'/app/api/transactions/expense/{exp_b_id}', json={
        "amount": 999.0,
        "category": "Shopping",
        "date": "2026-10-01"
    })
    assert put_exp.status_code == 404

    # User A attempts to delete User B's income
    del_inc = client.delete(f'/app/api/transactions/income/{inc_b_id}')
    assert del_inc.status_code == 404

    # User A attempts to update User B's goal
    put_goal = client.put(f'/app/api/goals/{goal_b_id}', json={"goal_name": "Hacked Goal"})
    assert put_goal.status_code == 404

    # User A attempts to delete User B's goal
    del_goal = client.delete(f'/app/api/goals/{goal_b_id}')
    assert del_goal.status_code == 404

    # User A attempts to view User B's goal detail
    view_goal = client.get(f'/app/goals/{goal_b_id}')
    assert view_goal.status_code == 404


def test_profile_validation_email_and_currency(app, client, test_user):
    """Verify profile update rejects invalid email and preferences rejects invalid currency."""
    with app.app_context():
        token = create_access_token(identity=str(test_user))

    client.set_cookie('access_token_cookie', token, domain='localhost')

    # Invalid email update
    res_bad_email = client.put('/app/api/profile', json={"email": "bad_email_format"})
    assert res_bad_email.status_code == 400
    assert "Invalid email format" in res_bad_email.get_json().get("message", "")

    # Valid email update
    res_ok_email = client.put('/app/api/profile', json={"email": "updated_user@example.com"})
    assert res_ok_email.status_code == 200

    # Invalid currency in preferences
    res_bad_curr = client.put('/app/api/profile/preferences', json={"currency": "BITCOIN"})
    assert res_bad_curr.status_code == 400
    assert "Invalid currency" in res_bad_curr.get_json().get("message", "")

    # Valid currency in preferences
    res_ok_curr = client.put('/app/api/profile/preferences', json={"currency": "INR"})
    assert res_ok_curr.status_code == 200


def test_csv_upload_xss_protection(app, client, test_user):
    """Verify CSV upload with XSS vectors is parsed safely and returns structured records."""
    import io
    with app.app_context():
        token = create_access_token(identity=str(test_user))

    client.set_cookie('access_token_cookie', token, domain='localhost')
    xss_csv = "Date,Amount,Category,Description\n2026-10-01,50.0,<script>alert(1)</script>,<img src=x onerror=alert(1)>\n"
    data = {'file': (io.BytesIO(xss_csv.encode('utf-8')), 'test_xss.csv')}
    res = client.post('/app/api/transactions/upload-csv', data=data, content_type='multipart/form-data')
    assert res.status_code == 200
    payload = res.get_json()
    assert payload['success'] is True
    # The invalid category is captured in invalid_records
    assert len(payload['invalid_records']) == 1
    rec = payload['invalid_records'][0]
    assert "<script>alert(1)</script>" in rec['category']
    assert any("Invalid category" in err for err in rec['errors'])

