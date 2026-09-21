import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from models.user import User
from models.setting import Setting

class ProfileModuleTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['JWT_SECRET_KEY'] = 'test-secret'
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        db.create_all()
        
        # Create test user
        self.test_user = User(username='testprofile', email='test@profile.com', full_name='Test Profile')
        self.test_user.set_password('Password123!')
        db.session.add(self.test_user)
        db.session.commit()
        
        self.user_id = self.test_user.id
        
        # Create second user for conflict testing
        self.user2 = User(username='test2', email='test2@profile.com')
        self.user2.set_password('Password123!')
        db.session.add(self.user2)
        db.session.commit()
        
        # Login to get JWT
        response = self.client.post('/api/auth/login', json={
            'username': 'testprofile',
            'password': 'Password123!'
        })
        self.access_token = None
        for cookie in response.headers.getlist('Set-Cookie'):
            if 'access_token_cookie' in cookie:
                self.access_token = cookie.split(';')[0].split('=')[1]
                
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
    def get_headers(self):
        # Disable CSRF for tests by omitting it, but the app configuration needs to allow it.
        # Since we use cookies, JWT expects CSRF if enabled.
        # We disabled CSRF globally in setUp via 'WTF_CSRF_ENABLED' = False, 
        # but flask_jwt_extended might still check JWT_COOKIE_CSRF_PROTECT.
        self.app.config['JWT_COOKIE_CSRF_PROTECT'] = False
        return {
            'Cookie': f'access_token_cookie={self.access_token}'
        }

    def test_get_profile(self):
        self.app.config['JWT_COOKIE_CSRF_PROTECT'] = False
        res = self.client.get('/app/api/profile', headers=self.get_headers())
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['username'], 'testprofile')
        self.assertEqual(data['full_name'], 'Test Profile')
        
    def test_update_profile(self):
        self.app.config['JWT_COOKIE_CSRF_PROTECT'] = False
        res = self.client.put('/app/api/profile', json={
            'email': 'newtest@profile.com',
            'full_name': 'New Profile Name'
        }, headers=self.get_headers())
        self.assertEqual(res.status_code, 200)
        
        user = db.session.get(User, self.user_id)
        self.assertEqual(user.email, 'newtest@profile.com')
        self.assertEqual(user.full_name, 'New Profile Name')
        
    def test_update_profile_duplicate_email(self):
        self.app.config['JWT_COOKIE_CSRF_PROTECT'] = False
        res = self.client.put('/app/api/profile', json={
            'email': 'test2@profile.com'
        }, headers=self.get_headers())
        self.assertEqual(res.status_code, 409)

    def test_update_password_success(self):
        self.app.config['JWT_COOKIE_CSRF_PROTECT'] = False
        res = self.client.post('/app/api/profile/password', json={
            'current_password': 'Password123!',
            'new_password': 'NewPassword123!',
            'confirm_password': 'NewPassword123!'
        }, headers=self.get_headers())
        self.assertEqual(res.status_code, 200)
        
        user = db.session.get(User, self.user_id)
        self.assertTrue(user.check_password('NewPassword123!'))

    def test_update_password_fail_wrong_current(self):
        self.app.config['JWT_COOKIE_CSRF_PROTECT'] = False
        res = self.client.post('/app/api/profile/password', json={
            'current_password': 'WrongPassword123!',
            'new_password': 'NewPassword123!',
            'confirm_password': 'NewPassword123!'
        }, headers=self.get_headers())
        self.assertEqual(res.status_code, 401)
        
    def test_update_password_fail_mismatch(self):
        self.app.config['JWT_COOKIE_CSRF_PROTECT'] = False
        res = self.client.post('/app/api/profile/password', json={
            'current_password': 'Password123!',
            'new_password': 'NewPassword123!',
            'confirm_password': 'DifferentPassword123!'
        }, headers=self.get_headers())
        self.assertEqual(res.status_code, 400)

    def test_update_preferences(self):
        self.app.config['JWT_COOKIE_CSRF_PROTECT'] = False
        res = self.client.put('/app/api/profile/preferences', json={
            'currency': 'INR',
            'email_notifications': False
        }, headers=self.get_headers())
        self.assertEqual(res.status_code, 200)
        
        user = db.session.get(User, self.user_id)
        self.assertIsNotNone(user.setting)
        self.assertEqual(user.setting.currency, 'INR')
        self.assertFalse(user.setting.email_notifications)

if __name__ == '__main__':
    unittest.main()
