"""
Module: tests/test_reports.py

Purpose:
Contains Pytest test cases ensuring application stability.

Flow:
User Request -> Route Handler -> Business Logic -> Database

"""
import pytest
from datetime import date
from dateutil.relativedelta import relativedelta
from models.user import User
from models.income import Income
from models.expense import Expense
from extensions import db

def test_reports_default_current_month(client, app):
    with app.app_context():
        user = User(username='testuser_reports', email='reports@test.com')
        user.set_password('Password123!')
        db.session.add(user)
        db.session.commit()
        
        # Add income for current month
        today = date.today()
        income = Income(user_id=user.id, amount=5000, income_type='Variable', date=today)
        db.session.add(income)
        db.session.commit()
        
    client.post('/api/auth/login', json={'username': 'testuser_reports', 'password': 'Password123!'})
    
    res = client.get('/app/reports')
    assert res.status_code == 200
    assert b"5,000.00" in res.data

def test_reports_previous_month(client, app):
    with app.app_context():
        user = User(username='testuser_reports2', email='reports2@test.com')
        user.set_password('Password123!')
        db.session.add(user)
        db.session.commit()
        
        today = date.today()
        prev_month = today - relativedelta(months=1)
        prev_period_str = f"{prev_month.year}-{prev_month.month:02d}"
        
        # Add income for prev month
        income = Income(user_id=user.id, amount=8000, income_type='Variable', date=prev_month)
        db.session.add(income)
        db.session.commit()
        
    client.post('/api/auth/login', json={'username': 'testuser_reports2', 'password': 'Password123!'})
    
    res = client.get(f'/app/reports?period={prev_period_str}')
    assert res.status_code == 200
    assert b"8,000.00" in res.data

def test_reports_empty_period(client, app):
    with app.app_context():
        user = User(username='testuser_reports3', email='reports3@test.com')
        user.set_password('Password123!')
        db.session.add(user)
        db.session.commit()
        
        today = date.today()
        prev_month = today - relativedelta(months=1)
        prev_period_str = f"{prev_month.year}-{prev_month.month:02d}"
        
        # Add income for current month so global has_data is true
        income = Income(user_id=user.id, amount=5000, income_type='Variable', date=today)
        db.session.add(income)
        db.session.commit()
        
    client.post('/api/auth/login', json={'username': 'testuser_reports3', 'password': 'Password123!'})
    
    res = client.get(f'/app/reports?period={prev_period_str}')
    assert res.status_code == 200
    assert b"No financial activity recorded for this period." in res.data

def test_reports_invalid_period(client, app):
    with app.app_context():
        user = User(username='testuser_reports4', email='reports4@test.com')
        user.set_password('Password123!')
        db.session.add(user)
        db.session.commit()
        
    client.post('/api/auth/login', json={'username': 'testuser_reports4', 'password': 'Password123!'})
    
    res = client.get('/app/reports?period=2026-15')
    assert res.status_code == 400
    assert b"Invalid period selected" in res.data
