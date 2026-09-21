from flask import render_template, request, jsonify, Response, stream_with_context
from flask_jwt_extended import jwt_required, get_jwt_identity
from routes.user import app_bp
from extensions import db, cache
from models.user import User
from models.income import Income
from models.expense import Expense, EXPENSE_CATEGORIES, normalize_category
from utils.csv_processor import process_expense_csv
from utils.finance import get_active_fixed_incomes
from datetime import datetime
from sqlalchemy import func
import csv
from io import StringIO
from utils.cache_keys import invalidate_user_financial_cache

@app_bp.route('/transactions')
@jwt_required()
def transactions():
    return render_template('app/transactions.html', expense_categories=EXPENSE_CATEGORIES, today_date=datetime.now().date().isoformat())

@app_bp.route('/expenses')
@jwt_required()
def all_expenses():
    return render_template('app/expenses.html', expense_categories=EXPENSE_CATEGORIES, today_date=datetime.now().date().isoformat())

@app_bp.route('/api/transactions/income', methods=['GET', 'POST'])
@jwt_required()
def handle_income():
    user_id = int(get_jwt_identity())
    if request.method == 'POST':
        data = request.json
        try:
            date_val = datetime.strptime(data['date'], '%Y-%m-%d').date()
            if date_val > datetime.now().date():
                return jsonify({"error": "Transaction date cannot be in the future."}), 400
            if data['income_type'] == 'Fixed':
                desc = data.get('description', '').strip()
                existing = Income.query.filter(
                    Income.user_id == user_id, 
                    Income.income_type == 'Fixed', 
                    Income.date == date_val,
                    Income.amount == float(data['amount']),
                    func.lower(Income.description) == desc.lower()
                ).first()
                if existing:
                    return jsonify({"error": "This fixed income already exists for this date, category and amount."}), 409
                
                income = Income(
                    user_id=user_id,
                    amount=float(data['amount']),
                    income_type='Fixed',
                    date=date_val,
                    description=data.get('description', '')
                )
                db.session.add(income)
            else:
                income = Income(
                    user_id=user_id,
                    amount=float(data['amount']),
                    income_type='Variable',
                    date=date_val,
                    description=data.get('description', '')
                )
                db.session.add(income)
            
            db.session.commit()
            invalidate_user_financial_cache(user_id)
            return jsonify({"message": "Income updated successfully"}), 201
        except Exception as e:
            db.session.rollback()
            import traceback
            error_details = f"{type(e).__name__}: {str(e)}"
            print(traceback.format_exc())
            return jsonify({"error": error_details}), 400
            
    # GET
    today = datetime.utcnow().date()
    
    active_fixed = get_active_fixed_incomes(user_id, today)
    
    current_fixed_data = None
    if active_fixed['active_records']:
        current_fixed_data = {
            "amount": active_fixed['total_amount'],
            "is_multiple": len(active_fixed['active_records']) > 1,
            "single_date": active_fixed['active_records'][0]['date'] if len(active_fixed['active_records']) == 1 else None
        }

    all_fixed_records = Income.query.filter_by(
        user_id=user_id,
        income_type='Fixed'
    ).order_by(Income.date.desc()).all()
    
    fixed_incomes_data = [{
        "id": r.id,
        "amount": r.amount,
        "date": r.date.isoformat(),
        "description": r.description
    } for r in all_fixed_records]

    variable_incomes = Income.query.filter_by(
        user_id=user_id, 
        income_type='Variable'
    ).order_by(Income.date.desc()).limit(50).all()
    
    variable_result = [{
        "id": i.id,
        "amount": i.amount,
        "date": i.date.isoformat(),
        "description": i.description
    } for i in variable_incomes]
    
    return jsonify({
        "current_fixed_income": current_fixed_data,
        "fixed_incomes": fixed_incomes_data,
        "variable_incomes": variable_result,
        "expense_categories": EXPENSE_CATEGORIES
    }), 200

@app_bp.route('/api/transactions/income/<int:income_id>', methods=['PUT', 'DELETE'])
@jwt_required()
def handle_income_by_id(income_id):
    user_id = int(get_jwt_identity())
    
    if request.method == 'DELETE':
        try:
            income = Income.query.filter_by(id=income_id, user_id=user_id).first()
            if not income:
                return jsonify({"error": "Income record not found or unauthorized"}), 404
                
            db.session.delete(income)
            db.session.commit()
            invalidate_user_financial_cache(user_id)
            return jsonify({"message": "Income record deleted successfully"}), 200
        except Exception as e:
            db.session.rollback()
            import logging
            logging.error(f"Error deleting expense: {str(e)}")
            return jsonify({"error": "An internal error occurred."}), 400

    # PUT
    data = request.json
    try:
        income = Income.query.filter_by(id=income_id, user_id=user_id).first()
        if not income:
            return jsonify({"error": "Income record not found or unauthorized"}), 404
            
        date_val = datetime.strptime(data['date'], '%Y-%m-%d').date()
        if date_val > datetime.now().date():
            return jsonify({"error": "Transaction date cannot be in the future."}), 400
        desc = data.get('description', '').strip()
        
        if income.income_type == 'Fixed':
            # Duplicate check excluding current record
            existing = Income.query.filter(
                Income.id != income_id,
                Income.user_id == user_id,
                Income.income_type == 'Fixed',
                Income.date == date_val,
                Income.amount == float(data['amount']),
                func.lower(Income.description) == desc.lower()
            ).first()
            
            if existing:
                return jsonify({"error": "This fixed income already exists for this date, category and amount."}), 409
                
        income.amount = float(data['amount'])
        income.date = date_val
        income.description = desc
        
        db.session.commit()
        invalidate_user_financial_cache(user_id)
        return jsonify({"message": "Income updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@app_bp.route('/api/transactions/expense', methods=['GET', 'POST'])
@jwt_required()
def handle_expense():
    user_id = int(get_jwt_identity())
    if request.method == 'POST':
        data = request.json
        try:
            if 'category' not in data:
                return jsonify({"error": "Missing category"}), 400
            
            normalized_cat = normalize_category(data['category'])
            if not normalized_cat:
                return jsonify({"error": "Invalid category"}), 400
                
            date_val = datetime.strptime(data['date'], '%Y-%m-%d').date()
            if date_val > datetime.now().date():
                return jsonify({"error": "Transaction date cannot be in the future."}), 400
            amount = float(data['amount'])
            if amount <= 0:
                return jsonify({"error": "Expense amount must be greater than zero"}), 400
                
            expense = Expense(
                user_id=user_id,
                amount=amount,
                category=normalized_cat,
                date=date_val,
                description=data.get('description', '')
            )
            db.session.add(expense)
            db.session.commit()
            invalidate_user_financial_cache(user_id)
            return jsonify({"message": "Expense added successfully"}), 201
        except ValueError as e:
            return jsonify({"error": "Invalid data format provided."}), 400
        except Exception as e:
            import logging
            logging.error(f"Error creating expense: {str(e)}")
            return jsonify({"error": "An internal error occurred."}), 400
            
    # GET with filters
    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=20, type=int)
    per_page = max(1, min(500, per_page))
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    category = request.args.get('category')

    query = Expense.query.filter_by(user_id=user_id)

    if start_date:
        try:
            sd = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Expense.date >= sd)
        except ValueError:
            pass
            
    if end_date:
        try:
            ed = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Expense.date <= ed)
        except ValueError:
            pass

    if category:
        normalized_cat = normalize_category(category)
        if normalized_cat:
            query = query.filter(Expense.category == normalized_cat)

    # Sort deterministic
    query = query.order_by(Expense.date.desc(), Expense.id.desc())

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    expenses = paginated.items

    result = [{
        "id": e.id,
        "amount": e.amount,
        "category": e.category,
        "date": e.date.isoformat(),
        "description": e.description
    } for e in expenses]

    return jsonify({
        "transactions": result,
        "page": paginated.page,
        "total_pages": paginated.pages,
        "total_items": paginated.total
    }), 200

@app_bp.route('/api/transactions/expense/<int:expense_id>', methods=['PUT', 'DELETE'])
@jwt_required()
def handle_expense_by_id(expense_id):
    user_id = int(get_jwt_identity())
    
    if request.method == 'DELETE':
        try:
            expense = Expense.query.filter_by(id=expense_id, user_id=user_id).first()
            if not expense:
                return jsonify({"error": "Expense record not found or unauthorized"}), 404
                
            db.session.delete(expense)
            db.session.commit()
            invalidate_user_financial_cache(user_id)
            return jsonify({"message": "Expense record deleted successfully"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 400

    # PUT
    data = request.json
    try:
        expense = Expense.query.filter_by(id=expense_id, user_id=user_id).first()
        if not expense:
            return jsonify({"error": "Expense record not found or unauthorized"}), 404
            
        if 'category' in data:
            normalized_cat = normalize_category(data['category'])
            if not normalized_cat:
                return jsonify({"error": "Invalid category"}), 400
            expense.category = normalized_cat
            
        date_val = datetime.strptime(data['date'], '%Y-%m-%d').date()
        if date_val > datetime.now().date():
            return jsonify({"error": "Transaction date cannot be in the future."}), 400
        desc = data.get('description', '').strip()
        
        expense.amount = float(data['amount'])
        expense.date = date_val
        expense.description = desc
        
        db.session.commit()
        invalidate_user_financial_cache(user_id)
        return jsonify({"message": "Expense updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400

@app_bp.route('/api/transactions/expense/export', methods=['GET'])
@jwt_required()
def export_expenses_csv():
    user_id = int(get_jwt_identity())
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    category = request.args.get('category')

    query = Expense.query.filter_by(user_id=user_id)

    if start_date:
        try:
            sd = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(Expense.date >= sd)
        except ValueError:
            pass
            
    if end_date:
        try:
            ed = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(Expense.date <= ed)
        except ValueError:
            pass

    if category:
        normalized_cat = normalize_category(category)
        if normalized_cat:
            query = query.filter(Expense.category == normalized_cat)

    query = query.order_by(Expense.date.desc(), Expense.id.desc())

    def generate():
        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(['Date', 'Category', 'Description', 'Amount'])
        yield si.getvalue()
        si.seek(0)
        si.truncate(0)
        
        for e in query.yield_per(100):
            cw.writerow([e.date.isoformat(), e.category, e.description, f"{e.amount:.2f}"])
            yield si.getvalue()
            si.seek(0)
            si.truncate(0)

    return Response(
        stream_with_context(generate()),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=expenses_export.csv"}
    )

@app_bp.route('/api/transactions/upload-csv', methods=['POST'])
@jwt_required()
def upload_csv():
    user_id = int(get_jwt_identity())
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
        
    file = request.files['file']
    if file.filename == '' or not file.filename.lower().endswith('.csv'):
        return jsonify({"error": "No selected file or invalid extension. Must be a .csv file."}), 400
        
    file_bytes = file.read(2 * 1024 * 1024) # Read up to 2MB
    if len(file.read(1)) > 0:
        return jsonify({"error": "File exceeds maximum allowed size of 2MB."}), 400
        
    result = process_expense_csv(file_bytes, user_id=user_id)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 400
        
    # We can either return preview or save directly.
    # The requirement says "Preview records -> Show invalid rows -> Confirm import".
    # So this endpoint will just return the processed result for preview.
    # The frontend will then call another endpoint to confirm.
    return jsonify(result), 200

@app_bp.route('/api/transactions/confirm-csv', methods=['POST'])
@jwt_required()
def confirm_csv():
    user_id = int(get_jwt_identity())
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
        
    file = request.files['file']
    if file.filename == '' or not file.filename.lower().endswith('.csv'):
        return jsonify({"error": "No selected file or invalid extension. Must be a .csv file."}), 400
        
    file_bytes = file.read(2 * 1024 * 1024) # Read up to 2MB
    if len(file.read(1)) > 0:
        return jsonify({"error": "File exceeds maximum allowed size of 2MB."}), 400
        
    result = process_expense_csv(file_bytes, user_id=user_id)
    
    if not result['success']:
        return jsonify({"error": result['error']}), 400
        
    records = result.get('valid_records', [])
    if not records:
        return jsonify({"error": "No valid records to import"}), 400
        
    selected_rows_str = request.form.get('selected_rows')
    if selected_rows_str:
        import json
        try:
            selected_rows = json.loads(selected_rows_str)
            if not isinstance(selected_rows, list):
                return jsonify({"error": "Invalid format for selected rows"}), 400
            selected_rows = [int(r) for r in selected_rows]
            records = [r for r in records if r['row_number'] in selected_rows]
            if not records:
                return jsonify({"error": "No selected valid rows to import"}), 400
        except (ValueError, json.JSONDecodeError):
            return jsonify({"error": "Invalid selected rows provided"}), 400
        
    try:
        for r in records:
            expense = Expense(
                user_id=user_id,
                amount=r['amount'],
                category=r['category'],
                date=datetime.strptime(r['date'], '%Y-%m-%d').date(),
                description=r.get('description', '')
            )
            db.session.add(expense)
        db.session.commit()
        invalidate_user_financial_cache(user_id)
        return jsonify({"message": f"{len(records)} expenses imported successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
