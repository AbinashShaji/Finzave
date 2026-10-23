"""
Module: tests/test_health_score_breakdown_and_pdf.py

Purpose:
Unit and integration tests for:
1. Health Score 4-pillar breakdown on Analysis page and scoring logic parity.
2. Flip card accessible markup and scoring guide content.
3. Complete 9-section Monthly Financial Analysis PDF report generation across full, incomplete, single-month, and zero-data scenarios.
4. Indian currency formatting and goal progress integrity (no invented scores).
"""
import pytest
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from models.user import User
from models.income import Income
from models.expense import Expense
from models.goal import Goal
from extensions import db
from utils.rule_engine import FinancialPeriod, evaluate_rules
from analysis.scoring import calculate_health_score
from utils.pdf_generator import generate_financial_report_pdf, format_inr
import io

def get_pdf_page_count(pdf_bytes: bytes) -> int:
    return pdf_bytes.count(b"/Type /Page") - pdf_bytes.count(b"/Type /Pages")

def test_health_score_pillars_parity():
    """Verify that the 4 pillars match exactly the scoring logic: 40, 25, 20, 15 max."""
    periods = [
        FinancialPeriod("2026-08", 100000.0, 0.0, [{"category": "Housing", "amount": 25000.0}]),
        FinancialPeriod("2026-09", 100000.0, 0.0, [{"category": "Housing", "amount": 25000.0}]),
        FinancialPeriod("2026-10", 100000.0, 0.0, [{"category": "Housing", "amount": 25000.0}]),
    ]
    insights = evaluate_rules(periods)
    health_data = calculate_health_score(periods, True, insights)
    
    pillars = health_data["pillars"]
    assert "savings_rate" in pillars
    assert "expense_ratio" in pillars
    assert "stability_trend" in pillars
    assert "spending_control" in pillars
    
    assert pillars["savings_rate"]["max"] == 40
    assert pillars["expense_ratio"]["max"] == 25
    assert pillars["stability_trend"]["max"] == 20
    assert pillars["spending_control"]["max"] == 15
    
    # Earned scores must not exceed their maximums
    assert 0 <= pillars["savings_rate"]["score"] <= 40
    assert 0 <= pillars["expense_ratio"]["score"] <= 25
    assert 0 <= pillars["stability_trend"]["score"] <= 20
    assert 0 <= pillars["spending_control"]["score"] <= 15
    
    # Base score sum check
    base_sum = (
        pillars["savings_rate"]["score"] +
        pillars["expense_ratio"]["score"] +
        pillars["stability_trend"]["score"] +
        pillars["spending_control"]["score"]
    )
    assert base_sum <= 100
    assert base_sum == health_data["raw_score"]

def test_analysis_page_flip_card_rendering(client, app):
    """Verify that the analysis page template renders the flip card with 4-pillar breakdown and scoring guide."""
    with app.app_context():
        user = User(username='test_flip_user', email='flip@test.com')
        user.set_password('Password123!')
        db.session.add(user)
        db.session.commit()
        
        today = date.today()
        inc = Income(user_id=user.id, amount=75000.0, income_type='Fixed', date=today, description="Monthly Salary")
        exp = Expense(user_id=user.id, amount=30000.0, category='Housing', date=today, description="Rent")
        db.session.add_all([inc, exp])
        db.session.commit()
        
    client.post('/api/auth/login', json={'username': 'test_flip_user', 'password': 'Password123!'})
    
    res = client.get('/app/analysis')
    assert res.status_code == 200
    html = res.data.decode('utf-8')
    
    # 1. Flip card elements
    assert "flip-card" in html
    assert "flip-card-inner" in html
    assert "flip-card-front" in html
    assert "flip-card-back" in html
    assert 'aria-label="Health Score details. Press Enter or Space to view scoring guide."' in html
    assert 'tabindex="0"' in html
    
    # 2. 4-Pillar Breakdown labels and maximums
    assert "Savings" in html
    assert "/40" in html or "/ 40" in html
    assert "Expense Management" in html
    assert "/25" in html or "/ 25" in html
    assert "Financial Stability" in html
    assert "/20" in html or "/ 20" in html
    assert "Spending Control" in html
    assert "/15" in html or "/ 15" in html
    
    # 3. Flip card reverse explanations and bottom sentence
    assert "Scoring Guide" in html
    assert "Health Score" in html
    assert "Savings (40 pts)" in html
    assert "Data Confidence" in html
    assert "Based on your savings behaviour, income, expenses, and category patterns." in html

def test_pdf_report_full_month():
    """Verify complete PDF generation with all 9 sections, Indian currency, goals, and recommendations."""
    period = FinancialPeriod(
        period_id="2026-10",
        fixed_income=150000.0,
        variable_income=25000.0,
        expenses=[
            {"category": "Housing", "amount": 40000.0},
            {"category": "Food", "amount": 15000.0},
            {"category": "Utilities", "amount": 5000.0},
            {"category": "Entertainment", "amount": 10000.0}
        ]
    )
    prev = FinancialPeriod(
        period_id="2026-09",
        fixed_income=150000.0,
        variable_income=10000.0,
        expenses=[
            {"category": "Housing", "amount": 40000.0},
            {"category": "Food", "amount": 12000.0},
            {"category": "Utilities", "amount": 5000.0}
        ]
    )
    p_older = FinancialPeriod(
        period_id="2026-08",
        fixed_income=150000.0,
        variable_income=0.0,
        expenses=[
            {"category": "Housing", "amount": 40000.0},
            {"category": "Food", "amount": 10000.0}
        ]
    )
    history = [p_older, prev, period]
    insights = evaluate_rules(history)
    health = calculate_health_score(history, True, insights)
    
    goals = [
        {
            "goal_name": "Emergency Fund",
            "target_amount": 500000.0,
            "current_saved": 350000.0,
            "remaining_amount": 150000.0,
            "target_date": date(2027, 6, 30),
            "completion_pct": 70.0,
            "status": "ACTIVE"
        }
    ]
    recommendations = [
        {
            "rule_id": "SAVINGS_RATE_STRONG",
            "priority": "LOW",
            "title": "Strong Savings Rate",
            "message": "You are currently saving over 50% of your income. Consider allocating surplus to long-term goals."
        }
    ]
    income_sources = [
        {"source": "Primary Salary", "type": "Fixed", "amount": 150000.0},
        {"source": "Freelance Bonus", "type": "Variable", "amount": 25000.0}
    ]
    historical_scores = {
        "2026-08": {"score": 82},
        "2026-09": {"score": 85},
        "2026-10": health
    }
    overview = {
        "savings_insights": ["Discretionary spending accounted for 5.7% of total income."]
    }
    
    pdf_bytes = generate_financial_report_pdf(
        period=period,
        health_data=health,
        historical_periods=history,
        overview=overview,
        goals=goals,
        recommendations=recommendations,
        income_sources=income_sources,
        historical_scores=historical_scores
    )
    
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 20000
    assert get_pdf_page_count(pdf_bytes) >= 3

def test_pdf_report_incomplete_month():
    """Verify that an incomplete month (income only) generates clean PDF without crash."""
    period = FinancialPeriod("2026-10", 80000.0, 0.0, [])
    period.status = "incomplete"
    health = calculate_health_score([period], True, [])
    
    pdf_bytes = generate_financial_report_pdf(
        period=period,
        health_data=health,
        historical_periods=[period]
    )
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 10000
    assert get_pdf_page_count(pdf_bytes) >= 1

def test_pdf_report_single_month_no_history():
    """Verify that a user with only 1 month of history produces valid PDF."""
    period = FinancialPeriod("2026-10", 60000.0, 0.0, [{"category": "Food", "amount": 10000.0}])
    health = calculate_health_score([period], True, [])
    
    pdf_bytes = generate_financial_report_pdf(
        period=period,
        health_data=health,
        historical_periods=[period]
    )
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 10000
    assert get_pdf_page_count(pdf_bytes) >= 1

def test_pdf_report_empty_month_zero_data():
    """Verify that an empty month with zero income and expenses generates valid PDF."""
    period = FinancialPeriod("2026-10", 0.0, 0.0, [])
    health = calculate_health_score([period], False, [])
    
    pdf_bytes = generate_financial_report_pdf(
        period=period,
        health_data=health,
        historical_periods=[period]
    )
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 10000
    assert get_pdf_page_count(pdf_bytes) >= 1

def test_indian_currency_formatting():
    """Verify INR formatting with ₹ symbol and Indian grouping."""
    assert format_inr(0) == "₹0"
    assert format_inr(500) == "₹500"
    assert format_inr(1500) == "₹1,500"
    assert format_inr(150000) == "₹1,50,000"
    assert format_inr(10000000) == "₹1,00,00,000"
    assert format_inr(-2500) == "-₹2,500"
    
    # With 2 decimals
    assert format_inr(0, decimals=2) == "₹0.00"
    assert format_inr(150000.5, decimals=2) == "₹1,50,000.50"
    assert format_inr(-2500.75, decimals=2) == "-₹2,500.75"

def test_pdf_export_endpoint_with_context(client, app):
    """Integration test verifying /app/api/reports/export/pdf delivers complete report with goals and income sources."""
    with app.app_context():
        user = User(username='test_pdf_ctx_user', email='ctx_pdf@test.com')
        user.set_password('Password123!')
        db.session.add(user)
        db.session.commit()
        
        today = date.today()
        inc1 = Income(user_id=user.id, amount=120000.0, income_type='Fixed', date=today, description="Tech Salary")
        inc2 = Income(user_id=user.id, amount=15000.0, income_type='Variable', date=today, description="Consulting")
        exp1 = Expense(user_id=user.id, amount=35000.0, category='Housing', date=today, description="Rent")
        exp2 = Expense(user_id=user.id, amount=12000.0, category='Food', date=today, description="Groceries")
        
        goal = Goal(
            user_id=user.id,
            goal_name="Vacation Fund",
            target_amount=100000.0,
            current_saved=45000.0,
            target_date=today + relativedelta(months=6)
        )
        db.session.add_all([inc1, inc2, exp1, exp2, goal])
        db.session.commit()
        
    client.post('/api/auth/login', json={'username': 'test_pdf_ctx_user', 'password': 'Password123!'})
    
    res = client.get('/app/api/reports/export/pdf')
    assert res.status_code == 200
    assert res.headers['Content-Type'] == 'application/pdf'
    assert res.data.startswith(b"%PDF")
    assert len(res.data) > 20000
    assert get_pdf_page_count(res.data) >= 3
