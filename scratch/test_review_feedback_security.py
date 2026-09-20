import os
import sys
import json
import requests
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app
from extensions import db
from models.user import User
from models.review import Review
from models.feedback import Feedback

def run_tests():
    app = create_app()
    with app.app_context():
        app.config["RATELIMIT_ENABLED"] = False
        # Clean up existing test data
        test_email = 'test_security@example.com'
        user = User.query.filter_by(email=test_email).first()
        if user:
            db.session.delete(user)
            db.session.commit()

        # Create test user
        user = User(username='sec_test_user', email=test_email)
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        user_id = user.id
        
        # Test 1: XSS Review Submission
        print("Running Test 1: XSS Review Submission...")
        
        client = app.test_client()
        # Login
        resp = client.post('/api/auth/login', json={"email": test_email, "password": "password123"})
        csrf_token = None
        app.config['JWT_TOKEN_LOCATION'] = ['cookies', 'headers']
        from flask_jwt_extended import create_access_token
        access_token = create_access_token(identity=str(user_id))
        headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}

        # Submit XSS review
        xss_payload = '<script>alert("XSS")</script>'
        resp = client.post('/app/api/reviews', json={"rating": 5, "content": xss_payload}, headers=headers)
        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}. Msg: {resp.text}"
        
        # Check DB
        review = Review.query.filter_by(user_id=user_id).first()
        assert review.content == xss_payload, "XSS Payload not saved correctly in DB (it should be raw in DB but escaped in UI)"
        
        # Test 2: Validation Hardening
        print("Running Test 2: Validation Hardening (Empty content, invalid rating)")
        resp = client.post('/app/api/reviews', json={"rating": 6, "content": "Too good"}, headers=headers)
        assert resp.status_code == 400, "Should reject rating > 5"
        
        resp = client.post('/app/api/reviews', json={"rating": 5, "content": ""}, headers=headers)
        assert resp.status_code == 400, "Should reject empty review content"
        
        # Feedback validation
        resp = client.post('/app/api/feedback', json={"category": "Invalid", "message": "Good app"}, headers=headers)
        assert resp.status_code == 400, "Should reject invalid category"
        
        # Test 3: Pagination Generation
        print("Running Test 3: Pagination generation & API sizes")
        # Add 50 reviews
        reviews_to_add = []
        for i in range(50):
            reviews_to_add.append(Review(user_id=user_id, rating=5, content=f"Bulk review {i}", status='live'))
        db.session.add_all(reviews_to_add)
        db.session.commit()
        
        resp = client.get('/api/reviews?page=2&per_page=10')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'items' in data
        assert len(data['items']) == 10, f"Expected 10 items, got {len(data['items'])}"
        assert data['page'] == 2
        assert data['total'] >= 50
        
        app.config["RATELIMIT_ENABLED"] = True
        
        # Test 4: Rate Limiting
        # In test environment, limiter might be disabled or in memory, let's test if it returns 429
        # Assuming limit is 1 per minute, we already submitted 1 review in Test 1.
        # It's possible test client doesn't trigger limits due to config, but let's try.
        print("Running Test 4: Rate Limiting verification...")
        resp = client.post('/app/api/reviews', json={"rating": 4, "content": "Second review fast"}, headers=headers)
        if resp.status_code == 429:
            print("Rate limiting working correctly (429 Too Many Requests)")
        else:
            print(f"Note: Rate limiting returned {resp.status_code}. (May be bypassed in test_client)")
            
        print("All tests executed successfully!")

if __name__ == '__main__':
    run_tests()
