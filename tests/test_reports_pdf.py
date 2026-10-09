"""
Module: tests/test_reports_pdf.py

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

def test_pdf_export_authenticated(client, app):
    with app.app_context():
        user = User(username='testuser_pdf', email='pdf@test.com')
        user.set_password('Password123!')
        db.session.add(user)
        db.session.commit()
        
        # Add income for current month
        today = date.today()
        income = Income(user_id=user.id, amount=5000, income_type='Variable', date=today)
        db.session.add(income)
        db.session.commit()
        
    client.post('/api/auth/login', json={'username': 'testuser_pdf', 'password': 'Password123!'})
    
    res = client.get('/app/api/reports/export/pdf')
    assert res.status_code == 200
    assert res.headers['Content-Type'] == 'application/pdf'
    assert b"%PDF" in res.data  # Valid PDF signature

def test_pdf_export_selected_period(client, app):
    with app.app_context():
        user = User(username='testuser_pdf2', email='pdf2@test.com')
        user.set_password('Password123!')
        db.session.add(user)
        db.session.commit()
        
        today = date.today()
        prev_month = today - relativedelta(months=1)
        prev_period_str = f"{prev_month.year}-{prev_month.month:02d}"
        
        income = Income(user_id=user.id, amount=8000, income_type='Variable', date=prev_month)
        db.session.add(income)
        db.session.commit()
        
    client.post('/api/auth/login', json={'username': 'testuser_pdf2', 'password': 'Password123!'})
    
    res = client.get(f'/app/api/reports/export/pdf?period={prev_period_str}')
    assert res.status_code == 200
    assert res.headers['Content-Type'] == 'application/pdf'
    assert b"%PDF" in res.data
    # In a real scenario we'd use PyPDF2 to read the text inside, but for now checking it generates is fine.

def test_pdf_export_different_periods_different_reports(client, app):
    with app.app_context():
        user = User(username='testuser_pdf3', email='pdf3@test.com')
        user.set_password('Password123!')
        db.session.add(user)
        db.session.commit()
        
        today = date.today()
        prev_month = today - relativedelta(months=1)
        
        income1 = Income(user_id=user.id, amount=5000, income_type='Variable', date=today)
        income2 = Income(user_id=user.id, amount=8000, income_type='Variable', date=prev_month)
        db.session.add_all([income1, income2])
        db.session.commit()
        
        period1 = f"{today.year}-{today.month:02d}"
        period2 = f"{prev_month.year}-{prev_month.month:02d}"
        
    client.post('/api/auth/login', json={'username': 'testuser_pdf3', 'password': 'Password123!'})
    
    res1 = client.get(f'/app/api/reports/export/pdf?period={period1}')
    res2 = client.get(f'/app/api/reports/export/pdf?period={period2}')
    
    assert res1.status_code == 200
    assert res2.status_code == 200
    assert res1.data != res2.data

def test_pdf_export_unauthorized(client):
    res = client.get('/app/api/reports/export/pdf')
    assert res.status_code == 401

def test_pdf_export_empty_period(client, app):
    with app.app_context():
        user = User(username='testuser_pdf4', email='pdf4@test.com')
        user.set_password('Password123!')
        db.session.add(user)
        db.session.commit()
        
        today = date.today()
        prev_month = today - relativedelta(months=1)
        prev_period_str = f"{prev_month.year}-{prev_month.month:02d}"
        
        # Add income for current month only
        income = Income(user_id=user.id, amount=5000, income_type='Variable', date=today)
        db.session.add(income)
        db.session.commit()
        
    client.post('/api/auth/login', json={'username': 'testuser_pdf4', 'password': 'Password123!'})
    
    res = client.get(f'/app/api/reports/export/pdf?period={prev_period_str}')
    assert res.status_code == 200
    assert res.headers['Content-Type'] == 'application/pdf'
    assert b"%PDF" in res.data
