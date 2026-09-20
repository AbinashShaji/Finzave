from flask import render_template, request, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from routes.user import app_bp
from extensions import db
from utils.finance import build_financial_periods
from utils.rule_engine import evaluate_rules
from analysis.scoring import calculate_health_score
from models.expense import Expense
import csv
import io

@app_bp.route('/reports')
@jwt_required()
def reports():
    user_id = int(get_jwt_identity())
    periods = build_financial_periods(user_id, months=6)
    
    # We need has_data for scoring calculation
    has_data = any((p.total_income > 0 or p.total_expenses > 0) for p in periods)
    
    insights = evaluate_rules(periods)
    current_period = periods[-1] if periods else None
    
    # Fix P0 Bug: Update signature to match analysis.py
    health_data = calculate_health_score(periods, has_data, insights)
    
    return render_template(
        'app/reports.html',
        has_data=has_data,
        current_period=current_period,
        health_data=health_data,
        periods=periods
    )

@app_bp.route('/api/reports/export/csv', methods=['GET'])
@jwt_required()
def export_csv():
    user_id = int(get_jwt_identity())
    
    expenses = db.session.query(Expense).filter_by(user_id=user_id).order_by(Expense.date.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Category', 'Amount', 'Description'])
    
    for ex in expenses:
        writer.writerow([ex.date.strftime('%Y-%m-%d'), ex.category, f"{ex.amount:.2f}", ex.description or ''])
        
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=transactions_export.csv"}
    )
