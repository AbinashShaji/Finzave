import sys
import os
from app import create_app
from extensions import db
from models.user import User
from models.review import Review
from models.feedback import Feedback

def run_tests():
    app = create_app()
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False

    with app.app_context():
        # Setup test users
        admin = User.query.filter_by(username='admin_feedback').first()
        if not admin:
            admin = User(username='admin_feedback', email='admin_feedback@test.com', role='admin')
            admin.set_password('pass123')
            db.session.add(admin)
            
        user1 = User.query.filter_by(username='user1_feedback').first()
        if not user1:
            user1 = User(username='user1_feedback', email='user1_feedback@test.com', role='user')
            user1.set_password('pass123')
            db.session.add(user1)

        user2 = User.query.filter_by(username='user2_feedback').first()
        if not user2:
            user2 = User(username='user2_feedback', email='user2_feedback@test.com', role='user')
            user2.set_password('pass123')
            db.session.add(user2)
            
        db.session.commit()
        
        user1_id = user1.id
        user2_id = user2.id
        admin_id = admin.id
        
        # Clear existing test data
        Review.query.filter(Review.user_id.in_([user1_id, user2_id])).delete()
        Feedback.query.filter(Feedback.user_id.in_([user1_id, user2_id])).delete()
        db.session.commit()

        from flask_jwt_extended import create_access_token
        user1_token = create_access_token(identity=str(user1_id))
        user2_token = create_access_token(identity=str(user2_id))
        admin_token = create_access_token(identity=str(admin_id))

    print("Starting tests...")
    
    with app.test_client() as client:
        # TEST 1: User1 Review Submission
        client.set_cookie('access_token_cookie', user1_token)
        res = client.post('/app/api/reviews', json={
            "rating": 5,
            "content": "This app is amazing!"
        })
        assert res.status_code == 201, f"Expected 201 for review submission, got {res.status_code}. Response: {res.get_data(as_text=True)}"
        print("[PASS] User 1 Review Submission Successful")

        # TEST 2: User1 Feedback Submission
        res = client.post('/app/api/feedback', json={
            "category": "Bug Report",
            "message": "Found a typo on the dashboard."
        })
        assert res.status_code == 201, f"Expected 201 for feedback submission, got {res.status_code}"
        print("[PASS] User 1 Feedback Submission Successful")

        # TEST 3: User2 should NOT see User1's reviews/feedback
        client.set_cookie('access_token_cookie', user2_token)
        res = client.get('/app/feedback')
        assert res.status_code == 200
        html = res.get_data(as_text=True)
        assert "This app is amazing!" not in html, "User2 can see User1's review!"
        assert "Found a typo on the dashboard." not in html, "User2 can see User1's feedback!"
        print("[PASS] User Data Isolation Verified")

        # TEST 4: Admin Access to Reviews & Feedback
        client.set_cookie('access_token_cookie', admin_token)
        res_reviews = client.get('/api/admin/reviews')
        assert res_reviews.status_code == 200, "Admin cannot fetch reviews"
        assert "This app is amazing!" in res_reviews.get_data(as_text=True), "Admin did not receive the new review"
        print("[PASS] Admin Review Integration Verified")
        
        res_feedback = client.get('/api/admin/feedback')
        assert res_feedback.status_code == 200, "Admin cannot fetch feedback"
        assert "Found a typo on the dashboard." in res_feedback.get_data(as_text=True), "Admin did not receive the new feedback"
        print("[PASS] Admin Feedback Integration Verified")

        print("\nALL INTEGRATION TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    run_tests()
