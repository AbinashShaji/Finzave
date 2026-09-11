from app import create_app
from extensions import db
from models import *
from sqlalchemy import text, inspect

app = create_app()

with app.app_context():
    print("Testing connection...")
    try:
        db.session.execute(text('SELECT 1'))
        print("CONNECTION: OK")
    except Exception as e:
        print("CONNECTION: FAILED", e)
        exit(1)
        
    print("Creating tables...")
    db.create_all()
    
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print("Tables found:", tables)
    expected_tables = ['users', 'incomes', 'expenses', 'goals', 'analyses', 'reviews', 'feedback', 'settings']
    missing = [t for t in expected_tables if t not in tables]
    if missing:
        print("Missing tables:", missing)
    else:
        print("All expected tables verified.")

    print("Testing /api/health...")
    client = app.test_client()
    response = client.get('/api/health')
    print("Health check status:", response.status_code)
    print("Health check response:", response.get_json())
