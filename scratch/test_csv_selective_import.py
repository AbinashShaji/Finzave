import sys
import os
import io
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from models.expense import Expense
from models.user import User

app = create_app()

def test_selective_csv_import():
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False
    with app.test_client() as client:
        with app.app_context():
            email = "csv_selective_tester@example.com"
            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(username="csv_select_test", email=email, password_hash="test")
                db.session.add(user)
                db.session.commit()
            user_id = user.id
            
            Expense.query.filter_by(user_id=user_id).delete()
            db.session.commit()

            from flask_jwt_extended import create_access_token
            access_token = create_access_token(identity=str(user_id))
            client.set_cookie(key='access_token_cookie', value=access_token)
            
            csv_content = """Date,Amount,Category,Description
2026-09-02,15000,Rent,Rent September
2026-09-03,3500,Food,Groceries
2026-09-05,1200,Food,Restaurant
2026-09-07,2000,Transport,Gas
2026-09-09,-100,Invalid,Negative Amount
"""
            csv_file = (io.BytesIO(csv_content.encode('utf-8')), 'test_expenses.csv')
            
            print("Testing CSV upload (preview)...")
            res1 = client.post('/app/api/transactions/upload-csv', 
                               data={'file': csv_file})
            assert res1.status_code == 200, f"Upload failed: {res1.data}"
            preview_data = json.loads(res1.data)
            assert preview_data['valid_count'] == 4
            assert preview_data['invalid_count'] == 1
            print("Preview successful.")
            
            print("Testing selective import (all valid rows)...")
            csv_file2 = (io.BytesIO(csv_content.encode('utf-8')), 'test_expenses.csv')
            res2 = client.post('/app/api/transactions/confirm-csv',
                               data={
                                   'file': csv_file2,
                                   'selected_rows': json.dumps([2, 3, 4, 5])
                               })
            assert res2.status_code == 201, f"Confirm failed: {res2.data}"
            expenses = Expense.query.filter_by(user_id=user_id).all()
            assert len(expenses) == 4
            print("Imported all valid rows successfully.")
            
            Expense.query.filter_by(user_id=user_id).delete()
            db.session.commit()
            
            print("Testing selective import (subset of rows)...")
            csv_file3 = (io.BytesIO(csv_content.encode('utf-8')), 'test_expenses.csv')
            res3 = client.post('/app/api/transactions/confirm-csv',
                               data={
                                   'file': csv_file3,
                                   'selected_rows': json.dumps([2, 5])
                               })
            assert res3.status_code == 201
            expenses = Expense.query.filter_by(user_id=user_id).all()
            assert len(expenses) == 2
            amounts = sorted([e.amount for e in expenses])
            assert amounts == [2000.0, 15000.0]
            print("Imported subset of rows successfully.")

            print("Testing selective import (empty selection)...")
            csv_file4 = (io.BytesIO(csv_content.encode('utf-8')), 'test_expenses.csv')
            res4 = client.post('/app/api/transactions/confirm-csv',
                               data={
                                   'file': csv_file4,
                                   'selected_rows': json.dumps([])
                               })
            assert res4.status_code == 400
            err_data = json.loads(res4.data)
            assert "No selected valid rows" in err_data['error']
            print("Empty selection properly rejected.")

            print("Testing selective import (invalid row numbers)...")
            csv_file5 = (io.BytesIO(csv_content.encode('utf-8')), 'test_expenses.csv')
            res5 = client.post('/app/api/transactions/confirm-csv',
                               data={
                                   'file': csv_file5,
                                   'selected_rows': json.dumps([99, 100, "abc"])
                               })
            assert res5.status_code == 400
            print("Invalid row selection properly rejected.")
            
            print("All CSV Selective Import tests passed successfully!")

if __name__ == '__main__':
    app.config['WTF_CSRF_ENABLED'] = False
    test_selective_csv_import()
