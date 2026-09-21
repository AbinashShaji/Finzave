import sys
import os
import io
import json
from datetime import datetime, timedelta

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from models.expense import Expense
from models.income import Income
from models.user import User

app = create_app()
app.config['WTF_CSRF_ENABLED'] = False
app.config['JWT_COOKIE_CSRF_PROTECT'] = False

def test_dates():
    with app.test_client() as client:
        with app.app_context():
            email = "date_validator@example.com"
            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(username="date_validator", email=email, password_hash="test")
                db.session.add(user)
                db.session.commit()
            user_id = user.id
            
            Expense.query.filter_by(user_id=user_id).delete()
            Income.query.filter_by(user_id=user_id).delete()
            db.session.commit()

            from flask_jwt_extended import create_access_token
            access_token = create_access_token(identity=str(user_id))
            client.set_cookie(key='access_token_cookie', value=access_token)
            
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            tomorrow = today + timedelta(days=1)

            print("1. Test Expense - Today (Valid)")
            res = client.post('/app/api/transactions/expense', json={
                'date': today.isoformat(),
                'amount': 100,
                'category': 'Food',
                'description': 'Lunch'
            })
            assert res.status_code in [200, 201], f"Expected success, got {res.status_code}"

            print("2. Test Expense - Yesterday (Valid)")
            res = client.post('/app/api/transactions/expense', json={
                'date': yesterday.isoformat(),
                'amount': 200,
                'category': 'Food',
                'description': 'Dinner'
            })
            assert res.status_code in [200, 201]

            print("3. Test Expense - Tomorrow (Invalid)")
            res = client.post('/app/api/transactions/expense', json={
                'date': tomorrow.isoformat(),
                'amount': 300,
                'category': 'Food',
                'description': 'Future meal'
            })
            assert res.status_code == 400
            assert "cannot be in the future" in res.get_json()['error']

            print("4. Test Income - Tomorrow (Invalid)")
            res = client.post('/app/api/transactions/income', json={
                'date': tomorrow.isoformat(),
                'income_type': 'Variable',
                'amount': 5000,
                'description': 'Future bonus'
            })
            assert res.status_code == 400
            assert "cannot be in the future" in res.get_json()['error']
            
            print("5. Test Update Expense - Tomorrow (Invalid)")
            expense = Expense.query.filter_by(user_id=user_id).first()
            res = client.put(f'/app/api/transactions/expense/{expense.id}', json={
                'date': tomorrow.isoformat(),
                'amount': 150,
                'category': 'Food',
                'description': 'Updated'
            })
            assert res.status_code == 400
            assert "cannot be in the future" in res.get_json()['error']

            print("6. Test CSV Import with Future Dates")
            csv_content = f"""Date,Amount,Category,Description
{today.isoformat()},100,Food,Today Meal
{yesterday.isoformat()},200,Transport,Gas
{tomorrow.isoformat()},300,Entertainment,Future Fun
"""
            csv_file = (io.BytesIO(csv_content.encode('utf-8')), 'dates.csv')
            res = client.post('/app/api/transactions/upload-csv', data={'file': csv_file})
            assert res.status_code == 200
            data = json.loads(res.data)
            
            assert data['valid_count'] == 2, f"Expected 2 valid, got {data['valid_count']}"
            assert data['invalid_count'] == 1, f"Expected 1 invalid, got {data['invalid_count']}"
            assert "Future transaction date is not allowed" in data['invalid_records'][0]['errors']

            print("All Date Validation Tests Passed!")

if __name__ == '__main__':
    test_dates()
