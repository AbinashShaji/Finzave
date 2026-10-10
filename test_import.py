import requests
from app import create_app
from extensions import db
from models.user import User
from flask_jwt_extended import create_access_token
import io
import urllib3

app = create_app()

with app.app_context():
    user = User.query.first()
    if not user:
        user = User(username='testuser', email='test@test.com')
        user.set_password('test')
        db.session.add(user)
        db.session.commit()
    
    user_id = user.id
    token = create_access_token(identity=str(user_id))

# Using a session to keep cookies
session = requests.Session()
# Manually set the cookie
session.cookies.set('access_token_cookie', token, domain='127.0.0.1')
session.cookies.set('csrf_access_token', token, domain='127.0.0.1') # It's not exactly the same but let's just bypass CSRF or provide it in header

headers = {'X-CSRF-TOKEN': token}

csv_data = """Date,Category,Amount,Description
2026-10-09,Food & Dining,50.0,Lunch
2026-10-09,Salary,1000.0,Invalid Category
2026-10-09,Food & Dining,50.0,Lunch
"""

# Upload CSV
files = {'file': ('test.csv', io.BytesIO(csv_data.encode('utf-8')), 'text/csv')}
response = session.post('http://127.0.0.1:5000/app/api/transactions/upload-csv', files=files, headers=headers)
print("Upload Response:", response.json())

data = response.json()
all_records = data.get('valid_records', []) + data.get('invalid_records', [])

confirm_payload = {'records': all_records}
confirm_response = session.post('http://127.0.0.1:5000/app/api/transactions/confirm-csv', json=confirm_payload, headers=headers)
print("Confirm Response status:", confirm_response.status_code)
print("Confirm Response text:", confirm_response.text)
