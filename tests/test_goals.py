import pytest
import datetime
from datetime import date, timedelta
from extensions import db
from models.goal import Goal
from models.user import User
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
