import sys
import os
from app import create_app
from extensions import db
from models.user import User

app = create_app()

def update_admin():
    with app.app_context():
        # Look for existing admin user
        admin_user = User.query.filter_by(role='admin').first()
        
        if admin_user:
            admin_user.username = 'admin'
            admin_user.email = 'admin@admin.com'
            admin_user.set_password('admin@000')
            db.session.commit()
            print(f"Updated existing admin to username '{admin_user.username}'.")
        else:
            # Create new admin if none exists
            admin_user = User(username='admin', email='admin@admin.com', role='admin')
            admin_user.set_password('admin@000')
            db.session.add(admin_user)
            db.session.commit()
            print(f"Created new admin with username '{admin_user.username}'.")

if __name__ == '__main__':
    update_admin()
