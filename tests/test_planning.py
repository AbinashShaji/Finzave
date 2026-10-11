"""
Module: tests/test_planning.py

Purpose:
Contains Pytest test cases ensuring application stability.

Flow:
User Request -> Route Handler -> Business Logic -> Database

"""
import pytest
from planning.sip import calculate_sip
from planning.emi import calculate_emi
from planning.insights import generate_planning_insight
from planning.services import calculate_planning_capacity, calculate_loan_affordability
from utils.rule_engine import FinancialPeriod
import json

def test_sip_normal():
    res = calculate_sip(10000, 12, 1)
    assert res['total_invested'] == 120000
    assert res['future_value'] > 120000
    assert len(res['yearly_breakdown']) == 1

def test_sip_zero_interest():
    res = calculate_sip(10000, 0, 1)
    assert res['total_invested'] == 120000
    assert res['future_value'] == 120000
    assert res['est_returns'] == 0

def test_sip_invalid():
    res = calculate_sip(-100, 12, 1)
    assert res['total_invested'] == 0
    assert res['future_value'] == 0

def test_emi_normal():
    res = calculate_emi(100000, 12, 1)
    assert res['monthly_emi'] > 0
    assert res['total_interest'] > 0
    assert res['total_payment'] > 100000
    assert len(res['yearly_amortization']) == 1

def test_emi_zero_interest():
    res = calculate_emi(120000, 0, 1)
    assert res['monthly_emi'] == 10000
    assert res['total_interest'] == 0
    assert res['total_payment'] == 120000

def test_emi_invalid():
    res = calculate_emi(-100, 12, 1)
    assert res['monthly_emi'] == 0

def test_insights():
    # 20% -> SUCCESS
    res1 = generate_planning_insight(2000, 10000, "SIP")
    assert res1['status'] == 'SUCCESS'
    
    # 85% -> WARNING
    res2 = generate_planning_insight(8500, 10000, "EMI")
    assert res2['status'] == 'WARNING'
    assert '85%' in res2['message']
    
    # > 100% -> WARNING
    res3 = generate_planning_insight(12000, 10000, "EMI")
    assert res3['status'] == 'WARNING'
    assert 'exceeds' in res3['message']

@pytest.fixture
def auth_client(client, app):
    client.post('/api/auth/register', json={
        "username": "planuser",
        "email": "planuser@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "terms_accepted": True
    })
    response = client.post('/api/auth/login', json={
        "username": "planuser",
        "password": "Password123!"
    })
    
    csrf_token = None
    for header in response.headers.getlist('Set-Cookie'):
        if 'csrf_access_token=' in header:
            csrf_token = header.split('csrf_access_token=')[1].split(';')[0]
            break
            
    client.csrf_token = csrf_token
    yield client

def test_api_capacity(auth_client, monkeypatch):
    from utils.rule_engine import FinancialPeriod
    
    # Mock build_financial_periods
    def mock_build(user_id, months):
        return [FinancialPeriod("2023-10", 50000, 0, [])]
        
    monkeypatch.setattr('routes.planning.build_financial_periods', mock_build)
    
    res = auth_client.get('/app/api/planning/capacity', headers={'X-CSRF-TOKEN': auth_client.csrf_token})
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data['savings'] == 50000
    assert data['suggested_sip_min'] == 15000

def test_api_sip(auth_client):
    payload = {
        "monthly_investment": 10000,
        "annual_rate": 12,
        "years": 10
    }
    res = auth_client.post('/app/api/planning/calculate_sip', json=payload, headers={'X-CSRF-TOKEN': auth_client.csrf_token})
    assert res.status_code == 200
    data = json.loads(res.data)
    assert 'future_value' in data
    assert 'yearly_breakdown' in data

def test_api_emi_vehicle(auth_client):
    payload = {
        "principal": 0,
        "loan_type": "Car",
        "vehicle_price": 1000000,
        "down_payment": 200000,
        "annual_rate": 8.5,
        "years": 5
    }
    res = auth_client.post('/app/api/planning/calculate_emi', json=payload, headers={'X-CSRF-TOKEN': auth_client.csrf_token})
    assert res.status_code == 200
    data = json.loads(res.data)
    assert 'monthly_emi' in data
    assert data['total_payment'] > 800000

def test_planning_capacity_variable_savings():
    """
    Test 1: Variable savings
    Month 1: Savings ₹10,000
    Month 2: Savings ₹20,000
    Month 3: Savings ₹30,000
    Expected:
    average_savings_capacity = ₹20,000
    SIP: ₹6,000 - ₹10,000
    """
    class MockPeriod:
        def __init__(self, inc, exp, status=None):
            self.total_income = inc
            self.total_expenses = exp
            self.savings = inc - exp
            self.status = status

    p1 = MockPeriod(50000, 40000) # savings = 10,000
    p2 = MockPeriod(50000, 30000) # savings = 20,000
    p3 = MockPeriod(50000, 20000) # savings = 30,000

    cap = calculate_planning_capacity([p1, p2, p3])
    assert cap["average_savings_capacity"] == 20000.0
    assert cap["current_savings_capacity"] == 20000.0
    assert cap["suggested_sip_min"] == 6000.0
    assert cap["suggested_sip_max"] == 10000.0
    assert cap["active_months"] == 3
    assert cap["has_history"] is True
    assert cap["context_message"] == "Based on 3 months of financial history"
    assert cap["capacity_message"] == "Calculated using your average monthly savings"
    assert cap["is_limited_history"] is False

def test_planning_capacity_single_high_month():
    """
    Test 2: Single high saving month
    Month 1: Savings ₹50,000
    Month 2: Savings ₹10,000
    Expected:
    Average: ₹30,000 (Not ₹10,000 or ₹50,000)
    """
    class MockPeriod:
        def __init__(self, inc, exp, status=None):
            self.total_income = inc
            self.total_expenses = exp
            self.savings = inc - exp
            self.status = status

    p1 = MockPeriod(80000, 30000) # savings = 50,000
    p2 = MockPeriod(40000, 30000) # savings = 10,000

    cap = calculate_planning_capacity([p1, p2])
    assert cap["average_savings_capacity"] == 30000.0
    assert cap["average_savings_capacity"] != 10000.0
    assert cap["average_savings_capacity"] != 50000.0
    assert cap["suggested_sip_min"] == 9000.0
    assert cap["suggested_sip_max"] == 15000.0
    assert cap["active_months"] == 2
    assert cap["is_limited_history"] is True
    assert "Limited financial history" in cap["history_note"]

def test_planning_capacity_no_financial_data():
    """
    Test 3: No financial data
    Expected:
    No planning capacity estimate.
    """
    # Empty list
    cap_empty = calculate_planning_capacity([])
    assert cap_empty["has_history"] is False
    assert cap_empty["average_savings_capacity"] == 0.0
    assert cap_empty["suggested_sip_min"] == 0.0
    assert cap_empty["suggested_sip_max"] == 0.0
    assert cap_empty["context_message"] == "Not enough financial data to estimate planning capacity."

    # None
    cap_none = calculate_planning_capacity(None)
    assert cap_none["has_history"] is False
    assert cap_none["average_savings_capacity"] == 0.0
    assert cap_none["suggested_sip_min"] == 0.0

    # Only no_data periods
    class MockNoData:
        status = "no_data"
        total_income = 0
        total_expenses = 0
        savings = 0

    cap_nodata = calculate_planning_capacity([MockNoData()])
    assert cap_nodata["has_history"] is False
    assert cap_nodata["average_savings_capacity"] == 0.0
    assert cap_nodata["suggested_sip_min"] == 0.0
    assert cap_nodata["context_message"] == "Not enough financial data to estimate planning capacity."

def test_api_planning_capacity_variable_savings(auth_client, monkeypatch):
    """
    Integration test: /app/api/planning/capacity with 3 months variable savings
    """
    class MockPeriod:
        def __init__(self, pid, inc, exp):
            self.period_id = pid
            self.total_income = inc
            self.total_expenses = exp
            self.savings = inc - exp
            self.status = "complete"

    def mock_build(user_id, months, **kwargs):
        return [
            MockPeriod("2026-01", 50000, 40000), # 10k
            MockPeriod("2026-02", 50000, 30000), # 20k
            MockPeriod("2026-03", 50000, 20000), # 30k
        ]

    monkeypatch.setattr('routes.planning.build_financial_periods', mock_build)

    res = auth_client.get('/app/api/planning/capacity', headers={'X-CSRF-TOKEN': auth_client.csrf_token})
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data['average_savings_capacity'] == 20000
    assert data['suggested_sip_min'] == 6000
    assert data['suggested_sip_max'] == 10000
    assert data['active_months'] == 3
    assert data['has_history'] is True
    assert data['context_message'] == "Based on 3 months of financial history"

def test_api_planning_capacity_no_data(auth_client, monkeypatch):
    """
    Integration test: /app/api/planning/capacity with no data
    """
    def mock_build(user_id, months, **kwargs):
        return []

    monkeypatch.setattr('routes.planning.build_financial_periods', mock_build)

    res = auth_client.get('/app/api/planning/capacity', headers={'X-CSRF-TOKEN': auth_client.csrf_token})
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data['has_history'] is False
    assert data['average_savings_capacity'] == 0
    assert data['suggested_sip_min'] == 0
    assert data['suggested_sip_max'] == 0
    assert data['context_message'] == "Not enough financial data to estimate planning capacity."

def test_planning_page_render_and_no_single_month(auth_client):
    """
    Verifies /app/planning renders without single-month misleading labels.
    """
    res = auth_client.get('/app/planning')
    assert res.status_code == 200
    assert b"Average Monthly Savings" in res.data
    assert b"Current Savings" not in res.data
    assert b"Based on your current month" not in res.data

def test_planning_and_goals_consistency():
    """
    Test 4 / Consistency requirement:
    Verify Goal Intelligence and Planning use the identical calculation rules
    and produce consistent capacity values.
    """
    from goals.services import calculate_goal_affordability
    from datetime import date, timedelta

    class MockGoal:
        target_amount = 60000
        current_saved = 0
        target_date = date.today() + timedelta(days=365)
        id = 1
        goal_name = "Consistency Test"
        created_at = date.today()

    class MockPeriod:
        def __init__(self, inc, exp):
            self.total_income = inc
            self.total_expenses = exp
            self.savings = inc - exp
            self.status = "complete"

    periods = [
        MockPeriod(50000, 40000), # 10k
        MockPeriod(50000, 30000), # 20k
        MockPeriod(50000, 20000), # 30k
    ]

    prog = {"saved": 0, "target": 60000, "remaining": 60000, "is_completed": False, "is_overdue": False}
    goal_aff = calculate_goal_affordability(MockGoal(), periods, prog)
    plan_cap = calculate_planning_capacity(periods)

    assert goal_aff["average_savings_capacity"] == plan_cap["average_savings_capacity"] == 20000.0
    assert goal_aff["active_months"] == plan_cap["active_months"] == 3
    assert goal_aff["has_history"] == plan_cap["has_history"] == True

def test_existing_users_regression(client, app):
    """
    Regression Test:
    Verifies that existing users can access:
    - GET /app/planning
    - GET /app/goals/<id>
    - GET /app/analysis
    - GET /app/dashboard
    with zero regressions and correct status code 200.
    """
    import datetime
    from datetime import date, timedelta
    from extensions import db
    from models.user import User
    from models.goal import Goal
    from models.income import Income
    from models.expense import Expense
    from flask_jwt_extended import create_access_token

    with app.app_context():
        user = User(username="plan_reg_user", email="plan_reg@example.com", password_hash="hash")
        db.session.add(user)
        db.session.commit()

        inc = Income(user_id=user.id, amount=60000.0, income_type="Fixed", date=date.today(), description="Salary")
        exp = Expense(user_id=user.id, amount=20000.0, category="Rent & Housing", date=date.today(), description="Rent")
        g = Goal(
            user_id=user.id,
            goal_name="Regression Goal",
            target_amount=50000,
            current_saved=10000,
            target_date=date.today() + timedelta(days=180)
        )
        db.session.add_all([inc, exp, g])
        db.session.commit()

        goal_id = g.id
        token = create_access_token(identity=str(user.id))

    client.set_cookie('access_token_cookie', token)

    # 1. GET /app/planning
    res_plan = client.get('/app/planning')
    assert res_plan.status_code == 200
    assert b"Average Monthly Savings" in res_plan.data

    # 2. GET /app/goals/<id>
    res_goal = client.get(f'/app/goals/{goal_id}')
    assert res_goal.status_code == 200
    assert b"Average Monthly Savings Capacity" in res_goal.data

    # 3. GET /app/analysis
    res_analysis = client.get('/app/analysis')
    assert res_analysis.status_code == 200

    # 4. GET /app/ (Dashboard)
    res_dash = client.get('/app/')
    assert res_dash.status_code == 200


def test_foir_loan_affordability_healthy():
    """
    Test 1:
    Income: ₹1,00,000
    EMI: ₹30,000
    Expected:
    FOIR: 30%
    Risk: Healthy
    """
    res = calculate_loan_affordability(monthly_income=100000, monthly_emi=30000)
    assert res['foir'] == 30.0 or res['foir'] == 30
    assert res['risk_level'] == 'Healthy'
    assert res['risk'] == 'Healthy'
    assert res['status'] == 'SUCCESS'
    assert 'manageable' in res['message'].lower()


def test_foir_loan_affordability_high_risk():
    """
    Test 2:
    Income: ₹50,000
    EMI: ₹40,000
    Expected:
    FOIR: 80%
    Risk: High Risk
    """
    res = calculate_loan_affordability(monthly_income=50000, monthly_emi=40000)
    assert res['foir'] == 80.0 or res['foir'] == 80
    assert res['risk_level'] == 'High Risk'
    assert res['risk'] == 'High Risk'
    assert res['status'] == 'WARNING'
    assert 'financial stress' in res['message'].lower()
    assert res['reason'] == "EMI consumes most of your monthly income."


def test_reducing_balance_emi_amortization():
    """
    Test 3:
    Verify EMI calculation:
    Loan: ₹50,00,000
    Rate: 9%
    Years: 30
    Expected:
    EMI: around ₹40,231
    """
    res = calculate_emi(5000000, 9, 30)
    assert round(res['monthly_emi']) == 40231
    assert 40230 <= res['monthly_emi'] <= 40232
    assert len(res['yearly_amortization']) == 30
    assert res['interest_cost_pct'] >= 189
    assert res['total_payment'] > 14000000
    assert round(res['total_interest']) == 9483210 or round(res['total_interest']) == 9483207


def test_sip_planning_unchanged():
    """
    Test 4:
    Verify existing SIP planning is unchanged.
    """
    # 1. SIP calculation formula intact
    res_sip = calculate_sip(10000, 12, 10)
    assert res_sip['total_invested'] == 1200000
    assert res_sip['future_value'] > 2300000
    assert len(res_sip['yearly_breakdown']) == 10
    
    # 2. SIP planning insight uses monthly savings
    sip_insight = generate_planning_insight(3000, 10000, "SIP")
    assert sip_insight['status'] == 'SUCCESS'
    assert 'uses 30% of your average monthly savings' in sip_insight['message']

    # 3. SIP capacity recommendations intact
    class MockPeriod:
        def __init__(self, inc, exp, status=None):
            self.total_income = inc
            self.total_expenses = exp
            self.savings = inc - exp
            self.status = status

    periods = [MockPeriod(50000, 30000), MockPeriod(50000, 30000)]
    cap = calculate_planning_capacity(periods)
    assert cap['average_savings_capacity'] == 20000
    assert cap['suggested_sip_min'] == 6000.0
    assert cap['suggested_sip_max'] == 10000.0


def test_api_calculate_emi_foir_affordability(auth_client, monkeypatch):
    """
    E2E test verifying /app/api/planning/calculate_emi returns
    FOIR affordability with average monthly income and risk analysis.
    """
    def mock_build(user_id, months, *args, **kwargs):
        return [FinancialPeriod("2026-01", 50000, 0, [{"amount": 20000}])]
        
    monkeypatch.setattr('routes.planning.build_financial_periods', mock_build)
    
    payload = {
        "principal": 5000000,
        "loan_type": "Home",
        "annual_rate": 9.0,
        "years": 30
    }
    res = auth_client.post('/app/api/planning/calculate_emi', json=payload, headers={'X-CSRF-TOKEN': auth_client.csrf_token})
    assert res.status_code == 200
    data = json.loads(res.data)
    
    assert round(data['monthly_emi']) == 40231
    assert 'loan_affordability' in data
    afford = data['loan_affordability']
    assert afford['income'] == 50000
    assert round(afford['emi']) == 40231
    assert afford['foir'] == 80.5 or afford['foir'] == 80.4 or afford['foir'] == 80.0
    assert afford['risk_level'] == 'High Risk'
    assert 'financial stress' in afford['message'].lower()



