import pytest
from models.expense import Expense
from models.income import Income

def test_create_expense(client, user_session):
    # Missing category
    response = user_session.post('/api/transactions/expense', json={
        "amount": 500,
        "date": "2023-10-01",
        "description": "Lunch"
    })
    assert response.status_code == 400

    # Valid expense
    response = user_session.post('/api/transactions/expense', json={
        "amount": 500,
        "category": "Food & Dining",
        "date": "2023-10-01",
        "description": "Lunch"
    })
    assert response.status_code == 201

def test_create_income(client, user_session):
    response = user_session.post('/api/transactions/income', json={
        "amount": 5000,
        "income_type": "Fixed",
        "date": "2023-10-01",
        "description": "Salary"
    })
    assert response.status_code == 201
