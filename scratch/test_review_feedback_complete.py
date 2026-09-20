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
    app.config['JWT_COOKIE_CSRF_PROTECT'] = True # Ensure CSRF is on for JWT

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

        from flask_jwt_extended import create_access_token, get_csrf_token
        user1_token = create_access_token(identity=str(user1_id))
        user1_csrf = get_csrf_token(user1_token)
        
        user2_token = create_access_token(identity=str(user2_id))
        user2_csrf = get_csrf_token(user2_token)
        
        admin_token = create_access_token(identity=str(admin_id))
        admin_csrf = get_csrf_token(admin_token)

    print("Starting tests...")
    
    with app.test_client() as client:
        # TEST: Normal user cannot access admin APIs
        client.set_cookie('access_token_cookie', user1_token)
        client.set_cookie('csrf_access_token', user1_csrf)
        res = client.get('/api/admin/reviews')
        assert res.status_code == 403, "Normal user accessed admin reviews!"
        print("[PASS] User Role Enforcement")

        # TEST: User1 Review Submission
        res = client.post('/app/api/reviews', json={
            "rating": 5,
            "content": "This app is amazing!"
        }, headers={"X-CSRF-TOKEN": user1_csrf})
        assert res.status_code == 201, f"Expected 201 for review submission, got {res.status_code}."
        print("[PASS] User 1 Review Submission Successful")

        # TEST: User1 Feedback Submission
        res = client.post('/app/api/feedback', json={
            "category": "Bug Report",
            "message": "Found a typo on the dashboard."
        }, headers={"X-CSRF-TOKEN": user1_csrf})
        assert res.status_code == 201, f"Expected 201 for feedback submission, got {res.status_code}"
        print("[PASS] User 1 Feedback Submission Successful")

        # TEST: Missing CSRF fails
        res = client.post('/app/api/feedback', json={
            "category": "Other",
            "message": "Missing CSRF test"
        })
        assert res.status_code == 401, f"Expected 401 for missing CSRF, got {res.status_code}"
        print("[PASS] Missing CSRF Token Rejected")

        # TEST: User Data Isolation
        client.set_cookie('access_token_cookie', user2_token)
        client.set_cookie('csrf_access_token', user2_csrf)
        res = client.get('/app/feedback')
        assert res.status_code == 200
        html = res.get_data(as_text=True)
        assert "This app is amazing!" not in html, "User2 can see User1's review!"
        assert "Found a typo on the dashboard." not in html, "User2 can see User1's feedback!"
        print("[PASS] User Data Isolation Verified")

        # TEST: Admin Access to Reviews & Feedback
        client.set_cookie('access_token_cookie', admin_token)
        client.set_cookie('csrf_access_token', admin_csrf)
        
        res_reviews = client.get('/api/admin/reviews')
        assert res_reviews.status_code == 200, "Admin cannot fetch reviews"
        data_reviews = res_reviews.get_json()
        assert len(data_reviews) > 0, "No reviews found for admin"
        review_id = data_reviews[0]['id']
        print("[PASS] Admin Review Retrieval Verified")
        
        res_feedback = client.get('/api/admin/feedback')
        assert res_feedback.status_code == 200, "Admin cannot fetch feedback"
        data_feedbacks = res_feedback.get_json()
        assert len(data_feedbacks) > 0, "No feedback found for admin"
        feedback_id = data_feedbacks[0]['id']
        assert data_feedbacks[0]['status'] == 'pending', f"Feedback status is {data_feedbacks[0]['status']}, expected pending"
        print("[PASS] Admin Feedback Retrieval Verified")

        # TEST: Admin Review Accept (PATCH with CSRF)
        res_patch_rev = client.patch(f'/api/admin/reviews/{review_id}/status', json={"status": "accepted"}, headers={"X-CSRF-TOKEN": admin_csrf})
        assert res_patch_rev.status_code == 200, f"Failed to patch review: {res_patch_rev.status_code}"
        
        # Verify status changed
        res_reviews_verify = client.get('/api/admin/reviews')
        data_reviews_verify = res_reviews_verify.get_json()
        assert data_reviews_verify[0]['status'] == 'accepted', "Review status was not updated in database"
        print("[PASS] Admin Review Update Verified")

        # TEST: Admin Feedback Status Update (PATCH with CSRF)
        res_patch_fb = client.patch(f'/api/admin/feedback/{feedback_id}/status', json={"status": "in_progress"}, headers={"X-CSRF-TOKEN": admin_csrf})
        assert res_patch_fb.status_code == 200, f"Failed to patch feedback: {res_patch_fb.status_code}"
        
        # Verify status changed
        res_feedback_verify = client.get('/api/admin/feedback')
        data_feedbacks_verify = res_feedback_verify.get_json()
        assert data_feedbacks_verify[0]['status'] == 'in_progress', "Feedback status was not updated in database"
        print("[PASS] Admin Feedback Update Verified")

        # TEST: Admin Delete Review & Feedback
        res_del_rev = client.delete(f'/api/admin/reviews/{review_id}', headers={"X-CSRF-TOKEN": admin_csrf})
        assert res_del_rev.status_code == 200
        
        res_del_fb = client.delete(f'/api/admin/feedback/{feedback_id}', headers={"X-CSRF-TOKEN": admin_csrf})
        assert res_del_fb.status_code == 200
        print("[PASS] Admin Delete verified")

        print("\nALL INTEGRATION TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    run_tests()
