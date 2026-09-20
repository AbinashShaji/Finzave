import sys
import os

# Ensure we can import from finzave
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from models.user import User

app = create_app()

with app.app_context():
    app.config['JWT_TOKEN_LOCATION'] = ['headers']
    app.config["RATELIMIT_ENABLED"] = False
    
    # Create or get admin user
    from flask_jwt_extended import create_access_token
    admin_email = 'test_admin_security@example.com'
    admin_user = User.query.filter_by(email=admin_email).first()
    if not admin_user:
        admin_user = User(username='testadmin', email=admin_email, role='admin')
        admin_user.set_password('password123')
        db.session.add(admin_user)
        db.session.commit()
    
    access_token = create_access_token(identity=str(admin_user.id))
    
    client = app.test_client()
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    resp = client.get('/api/admin/reviews', headers=headers)
    print("STATUS:", resp.status_code)
    if resp.status_code != 200:
        print("ERROR:", resp.text)
    else:
        print("SUCCESS! Data:", resp.json)
