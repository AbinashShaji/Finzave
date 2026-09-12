import sys
import os
from app import create_app
from extensions import db
from models.user import User

app = create_app()

def test_admin_routes():
    with app.app_context():
        # Setup test users
        admin_user = User.query.filter_by(username='test_admin').first()
        if not admin_user:
            admin_user = User(username='test_admin', email='admin@test.com', role='admin')
            admin_user.set_password('pass123')
            db.session.add(admin_user)
            db.session.commit()
            
        normal_user = User.query.filter_by(username='test_normal').first()
        if not normal_user:
            normal_user = User(username='test_normal', email='normal@test.com', role='user')
            normal_user.set_password('pass123')
            db.session.add(normal_user)
            db.session.commit()
            
        normal_user_id = normal_user.id
        admin_user_id = admin_user.id
            
    # Use test client
    with app.test_client() as client:
        # 1. Unauthenticated -> Should redirect to login for UI, 401 for API
        r = client.get('/admin')
        assert r.status_code == 302, f"Expected 302, got {r.status_code}"
        
        r = client.get('/api/admin/stats')
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"
        
        # 2. Authenticated Normal User -> Should return 403
        from flask_jwt_extended import create_access_token
        with app.app_context():
            normal_token = create_access_token(identity=str(normal_user_id))
            admin_token = create_access_token(identity=str(admin_user_id))
            
        client.set_cookie('access_token_cookie', normal_token)
        r = client.get('/admin')
        assert r.status_code == 403, f"Expected 403 for normal user UI, got {r.status_code}"
        
        r = client.get('/api/admin/stats')
        assert r.status_code == 403, f"Expected 403 for normal user API, got {r.status_code}"
        
        # 3. Authenticated Admin -> Should return 200
        client.set_cookie('access_token_cookie', admin_token)
        
        ui_routes = ['/admin', '/admin/users', '/admin/reviews', '/admin/feedback', '/admin/settings']
        for route in ui_routes:
            r = client.get(route)
            assert r.status_code == 200, f"Expected 200 for {route}, got {r.status_code}"
            
        api_routes = ['/api/admin/stats', '/api/admin/users', '/api/admin/reviews', '/api/admin/feedback']
        for route in api_routes:
            r = client.get(route)
            assert r.status_code == 200, f"Expected 200 for {route}, got {r.status_code}"
            
        print("ALL TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    test_admin_routes()
