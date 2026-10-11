"""
Module: tests/test_goals.py

Purpose:
Contains Pytest test cases ensuring application stability.

Flow:
User Request -> Route Handler -> Business Logic -> Database

"""
import pytest
import datetime
from datetime import date, timedelta
from extensions import db
from models.goal import Goal
from models.user import User
from models.income import Income
from models.expense import Expense
from flask_jwt_extended import create_access_token

from goals.services import (
    calculate_goal_progress,
    calculate_goal_affordability,
    calculate_goal_health,
    calculate_goal_projection,
    build_goal_intelligence
)

class MockGoal:
    def __init__(self, target, saved, days_left):
        self.target_amount = target
        self.current_saved = saved
        self.target_date = date.today() + timedelta(days=days_left)
        self.id = 1
        self.goal_name = "Test"
        self.created_at = date.today()

class MockFinancialPeriod:
    def __init__(self, savings):
        self.savings = savings

def test_goal_progress():
    goal = MockGoal(10000, 2000, 30)
    prog = calculate_goal_progress(goal)
    assert prog["saved"] == 2000
    assert prog["target"] == 10000
    assert prog["remaining"] == 8000
    assert prog["completion_pct"] == 20.0
    assert not prog["is_completed"]
    assert not prog["is_overdue"]

def test_goal_progress_zero_target():
    goal = MockGoal(0, 2000, 30)
    prog = calculate_goal_progress(goal)
    assert prog["completion_pct"] == 0.0
    assert not prog["is_completed"]

def test_goal_progress_completed():
    goal = MockGoal(10000, 10000, 30)
    prog = calculate_goal_progress(goal)
    assert prog["completion_pct"] == 100.0
    assert prog["remaining"] == 0
    assert prog["is_completed"]

def test_goal_progress_overdue():
    goal = MockGoal(10000, 2000, -5)
    prog = calculate_goal_progress(goal)
    assert prog["is_overdue"]
    assert not prog["is_completed"]

def test_goal_affordability():
    goal = MockGoal(12000, 0, 365) # 12 months left approx
    prog = calculate_goal_progress(goal)
    
    # Needs 1000 per month
    period = MockFinancialPeriod(5000)
    aff = calculate_goal_affordability(goal, period, prog)
    
    assert aff["req_monthly"] > 900 # approx 1000
    assert aff["impact_pct"] > 0
    assert aff["current_savings_capacity"] == 5000

def test_goal_affordability_no_savings():
    goal = MockGoal(12000, 0, 365)
    prog = calculate_goal_progress(goal)
    period = MockFinancialPeriod(0)
    aff = calculate_goal_affordability(goal, period, prog)
    assert aff["impact_pct"] == 100.0 # Capped at 100%

def test_goal_health_green():
    aff = {"raw_impact_pct": 20, "req_monthly": 1000, "current_savings_capacity": 5000}
    prog = {"is_completed": False, "is_overdue": False}
    health = calculate_goal_health(aff, prog)
    assert health["status"] == "GREEN"

def test_goal_health_yellow():
    aff = {"raw_impact_pct": 60, "req_monthly": 3000, "current_savings_capacity": 5000}
    prog = {"is_completed": False, "is_overdue": False}
    health = calculate_goal_health(aff, prog)
    assert health["status"] == "YELLOW"

def test_goal_health_red_no_capacity():
    aff = {"raw_impact_pct": 200, "req_monthly": 2000, "current_savings_capacity": 1000}
    prog = {"is_completed": False, "is_overdue": False}
    health = calculate_goal_health(aff, prog)
    assert health["status"] == "RED"

def test_goal_health_overdue():
    aff = {"raw_impact_pct": 20, "req_monthly": 1000, "current_savings_capacity": 5000}
    prog = {"is_completed": False, "is_overdue": True}
    health = calculate_goal_health(aff, prog)
    assert health["status"] == "RED"

def test_goal_projection():
    aff = {"req_monthly": 1000, "months_left": 5}
    prog = {"is_completed": False, "saved": 2000, "target": 7000}
    proj = calculate_goal_projection(None, aff, prog)
    assert len(proj) == 5
    assert proj[0]["projected_amount"] == 3000
    assert proj[-1]["projected_amount"] == 7000

def test_goal_route_success(client, app):
    with app.app_context():
        # User is already created in conftest if we fetch it, or we just create a unique one
        user = User(username="test_goal_1", email="test_goal_1@ex.com", password_hash="hash")
        db.session.add(user)
        db.session.commit()
        g = Goal(
            user_id=user.id,
            goal_name="Test Route Goal",
            target_amount=10000,
            current_saved=500,
            target_date=datetime.date.today() + datetime.timedelta(days=30)
        )
        db.session.add(g)
        db.session.commit()
        goal_id = g.id
        token = create_access_token(identity=str(user.id))
        
    client.set_cookie('access_token_cookie', token)
    res = client.get(f'/app/goals/{goal_id}')
    assert res.status_code == 200
    assert b"Test Route Goal" in res.data
    assert b"Goal Intelligence" in res.data
    assert b"Average Monthly Savings Capacity" in res.data
    assert b"Not enough financial data to estimate savings capacity." in res.data

def test_goal_route_unauthorized(client, app):
    with app.app_context():
        user1 = User(username="test_goal_2", email="test_goal_2@ex.com", password_hash="hash")
        user2 = User(username="test_goal_3", email="test_goal_3@ex.com", password_hash="hash")
        db.session.add_all([user1, user2])
        db.session.commit()
        g = Goal(
            user_id=user2.id,
            goal_name="Other User Goal",
            target_amount=10000,
            current_saved=500,
            target_date=datetime.date.today() + datetime.timedelta(days=30)
        )
        db.session.add(g)
        db.session.commit()
        goal_id = g.id
        token1 = create_access_token(identity=str(user1.id))
        
    client.set_cookie('access_token_cookie', token1)
    res = client.get(f'/app/goals/{goal_id}')
    assert res.status_code == 404

def test_goal_route_missing(client, app):
    with app.app_context():
        user = User(username="test_goal_4", email="test_goal_4@ex.com", password_hash="hash")
        db.session.add(user)
        db.session.commit()
        token = create_access_token(identity=str(user.id))
        
    client.set_cookie('access_token_cookie', token)
    res = client.get('/app/goals/999999')
    assert res.status_code == 404

def test_goal_affordability_variable_savings():
    """
    Test case 1:
    Variable savings:
    Month1 savings ₹10,000
    Month2 savings ₹20,000
    Month3 savings ₹30,000

    Expected:
    Average capacity = ₹20,000
    """
    goal = MockGoal(60000, 0, 365)
    prog = calculate_goal_progress(goal)
    
    p1 = MockFinancialPeriod(10000)
    p2 = MockFinancialPeriod(20000)
    p3 = MockFinancialPeriod(30000)
    
    aff = calculate_goal_affordability(goal, [p1, p2, p3], prog)
    
    assert aff["average_savings_capacity"] == 20000.0
    assert aff["current_savings_capacity"] == 20000.0
    assert aff["active_months"] == 3
    assert aff["has_history"] is True
    assert aff["context_message"] == "Based on 3 months of financial history"
    assert "average monthly savings capacity" in aff["impact_message"]

def test_goal_affordability_variable_savings_income_expenses_and_no_data():
    """
    Test variable savings calculated from income - expenses, excluding no_data periods.
    Month1: income 30,000, expenses 20,000 -> savings = 10,000
    Month2: income 40,000, expenses 20,000 -> savings = 20,000
    Month3: no_data period (income 0, expenses 0) -> excluded
    Month4: income 50,000, expenses 20,000 -> savings = 30,000

    Expected:
    Active months = 3
    Average capacity = (10,000 + 20,000 + 30,000) / 3 = ₹20,000
    """
    goal = MockGoal(60000, 0, 365)
    prog = calculate_goal_progress(goal)
    
    class DetailedMockPeriod:
        def __init__(self, inc, exp, status=None):
            self.total_income = inc
            self.total_expenses = exp
            self.status = status
            
    p1 = DetailedMockPeriod(30000, 20000)
    p2 = DetailedMockPeriod(40000, 20000)
    p_nodata = DetailedMockPeriod(0, 0, status="no_data")
    p3 = DetailedMockPeriod(50000, 20000)
    
    aff = calculate_goal_affordability(goal, [p1, p2, p_nodata, p3], prog)
    
    assert aff["average_savings_capacity"] == 20000.0
    assert aff["active_months"] == 3
    assert aff["has_history"] is True
    assert aff["context_message"] == "Based on 3 months of financial history"

def test_goal_affordability_no_financial_history():
    """
    Test case 2:
    No financial history

    Expected:
    Graceful message:
    "Not enough financial data to estimate savings capacity."
    """
    goal = MockGoal(10000, 0, 365)
    prog = calculate_goal_progress(goal)
    
    # Case A: Empty periods list
    aff_empty = calculate_goal_affordability(goal, [], prog)
    assert aff_empty["average_savings_capacity"] == 0.0
    assert aff_empty["has_history"] is False
    assert aff_empty["active_months"] == 0
    assert aff_empty["context_message"] == "Not enough financial data to estimate savings capacity."
    assert aff_empty["message"] == "Not enough financial data to estimate savings capacity."
    assert aff_empty["impact_message"] == "Not enough financial data to estimate savings capacity."
    
    health_empty = calculate_goal_health(aff_empty, prog)
    assert health_empty["message"] == "Not enough financial data to estimate savings capacity."
    
    # Case B: None periods
    aff_none = calculate_goal_affordability(goal, None, prog)
    assert aff_none["average_savings_capacity"] == 0.0
    assert aff_none["has_history"] is False
    assert aff_none["context_message"] == "Not enough financial data to estimate savings capacity."
    assert aff_none["message"] == "Not enough financial data to estimate savings capacity."
    
    # Case C: Only no_data periods
    class NoDataPeriod:
        status = "no_data"
        total_income = 0
        total_expenses = 0
        
    aff_nodata = calculate_goal_affordability(goal, [NoDataPeriod()], prog)
    assert aff_nodata["average_savings_capacity"] == 0.0
    assert aff_nodata["has_history"] is False
    assert aff_nodata["context_message"] == "Not enough financial data to estimate savings capacity."
    assert aff_nodata["message"] == "Not enough financial data to estimate savings capacity."

def test_goal_route_with_variable_history(client, app):
    """
    Test goal page rendering with variable savings history:
    Month 1 savings ₹10,000, Month 2 savings ₹20,000, Month 3 savings ₹30,000.
    Verifies page displays:
    - Average Monthly Savings Capacity
    - ₹20,000
    - Based on 3 months of financial history
    - This goal uses X% of your average monthly savings capacity.
    """
    from dateutil.relativedelta import relativedelta
    today = date.today()
    m3_date = today # Month 3
    m2_date = today - relativedelta(months=1) # Month 2
    m1_date = today - relativedelta(months=2) # Month 1
    
    with app.app_context():
        user = User(
            username="test_goal_hist",
            email="goal_hist@ex.com",
            password_hash="hash",
            created_at=m1_date
        )
        db.session.add(user)
        db.session.commit()
        
        # Month 1: Income 30,000, Expense 20,000 -> Savings 10,000
        inc1 = Income(user_id=user.id, amount=30000.0, income_type="Variable", date=m1_date, description="M1 Inc")
        exp1 = Expense(user_id=user.id, amount=20000.0, category="Rent & Housing", date=m1_date, description="M1 Exp")
        
        # Month 2: Income 40,000, Expense 20,000 -> Savings 20,000
        inc2 = Income(user_id=user.id, amount=40000.0, income_type="Variable", date=m2_date, description="M2 Inc")
        exp2 = Expense(user_id=user.id, amount=20000.0, category="Rent & Housing", date=m2_date, description="M2 Exp")
        
        # Month 3: Income 50,000, Expense 20,000 -> Savings 30,000
        inc3 = Income(user_id=user.id, amount=50000.0, income_type="Variable", date=m3_date, description="M3 Inc")
        exp3 = Expense(user_id=user.id, amount=20000.0, category="Rent & Housing", date=m3_date, description="M3 Exp")
        
        g = Goal(
            user_id=user.id,
            goal_name="Vacation Fund",
            target_amount=60000,
            current_saved=10000,
            target_date=today + timedelta(days=365)
        )
        db.session.add_all([inc1, exp1, inc2, exp2, inc3, exp3, g])
        db.session.commit()
        
        goal_id = g.id
        token = create_access_token(identity=str(user.id))
        
    client.set_cookie('access_token_cookie', token)
    res = client.get(f'/app/goals/{goal_id}')
    assert res.status_code == 200
    assert b"Average Monthly Savings Capacity" in res.data
    assert b"20,000" in res.data
    assert b"Based on 3 months of financial history" in res.data
    assert b"average monthly savings capacity" in res.data
