import json
import io
import sys
import os

sys.path.append(os.getcwd())

from app import create_app
from extensions import db
from models.user import User
from models.expense import Expense

def run_tests():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False
    
    with app.app_context():
        db.create_all()
        
        import uuid
        test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        user = User(email=test_email, username=f"testuser_{uuid.uuid4().hex[:8]}")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        
        client = app.test_client()
        from flask_jwt_extended import create_access_token
        access_token = create_access_token(identity=str(user.id))
        client.set_cookie('access_token_cookie', access_token)
        headers = {}
        
        print("Testing Negative Amount Rejection...")
        resp = client.post('/app/api/transactions/expense', json={
            "amount": -500,
            "date": "2026-09-20",
            "category": "Food"
        }, headers=headers)
        print(f"Status: {resp.status_code}, Data: {resp.data}")
        assert resp.status_code == 400
        data = json.loads(resp.data)
        assert "greater than zero" in data['error'].lower()
        
        print("Testing XSS Payload Storage...")
        resp = client.post('/app/api/transactions/expense', json={
            "amount": 100,
            "date": "2026-09-20",
            "category": "Food",
            "description": "<script>alert(1)</script>"
        }, headers=headers)
        assert resp.status_code == 201
        
        print("Testing Duplicate CSV Upload Prevention...")
        csv_content = "Date,Amount,Category,Description\n2026-09-01,150.00,Food,Lunch"
        
        # Upload 1
        resp = client.post('/app/api/transactions/confirm-csv', data={
            'file': (io.BytesIO(csv_content.encode('utf-8')), 'test.csv')
        }, content_type='multipart/form-data', headers=headers)
        assert resp.status_code == 201
        
        # Upload 2
        resp2 = client.post('/app/api/transactions/confirm-csv', data={
            'file': (io.BytesIO(csv_content.encode('utf-8')), 'test2.csv')
        }, content_type='multipart/form-data', headers=headers)
        
        # Duplicate should be filtered out. Total valid = 0 -> 400 error.
        assert resp2.status_code == 400
        assert b"No valid records to import" in resp2.data
        
        print("Testing Pagination...")
        for i in range(40):
            ex = Expense(user_id=user.id, amount=10, category="Shopping", date="2026-09-20")
            db.session.add(ex)
        db.session.commit()
        
        resp = client.get('/app/api/transactions/expense?page=1&per_page=20')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert len(data['transactions']) == 20
        assert data['page'] == 1
        assert data['total_pages'] > 1
        
        resp = client.get('/app/api/transactions/expense?page=2&per_page=20')
        data2 = json.loads(resp.data)
        assert data2['page'] == 2
        assert len(data2['transactions']) == 20
        
        print("All tests passed!")

if __name__ == '__main__':
    run_tests()
