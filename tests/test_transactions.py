"""
Module: tests/test_transactions.py

Purpose:
Contains Pytest test cases ensuring application stability.

Flow:
User Request -> Route Handler -> Business Logic -> Database

"""
import pytest
from models.expense import Expense
from models.income import Income

def test_create_expense(user_session):
    # Missing category
    response = user_session.post('/app/api/transactions/expense', json={
        "amount": 500,
        "date": "2023-10-01",
        "description": "Lunch"
    })
    assert response.status_code == 400

    # Valid expense
    response = user_session.post('/app/api/transactions/expense', json={
        "amount": 500,
        "category": "Food & Dining",
        "date": "2023-10-01",
        "description": "Lunch"
    })
    assert response.status_code == 201

def test_create_income(user_session):
    response = user_session.post('/app/api/transactions/income', json={
        "amount": 5000,
        "income_type": "Fixed",
        "date": "2023-10-01",
        "description": "Salary"
    })
    assert response.status_code == 201


def test_csv_upload_and_validation(user_session):
    import io
    csv_content = b"Date,Amount,Category,Description\n2026-10-01,150.0,Food & Dining,Lunch\n2026-10-02,500.0,Shopping,Shoes\n"
    data = {'file': (io.BytesIO(csv_content), 'test.csv')}
    res = user_session.post('/app/api/transactions/upload-csv', data=data, content_type='multipart/form-data')
    assert res.status_code == 200
    payload = res.get_json()
    assert payload['success'] is True
    assert payload['valid_count'] == 2
    assert payload['invalid_count'] == 0


def test_csv_confirm(user_session):
    records = [{
        'date': '2026-10-05',
        'amount': 250.0,
        'category': 'Transportation',
        'description': 'Cab'
    }]
    res = user_session.post('/app/api/transactions/confirm-csv', json={'records': records})
    assert res.status_code == 201
    assert res.get_json()['imported'] == 1

