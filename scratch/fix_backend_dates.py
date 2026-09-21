import re

filepath = r"c:\Users\abina\OneDrive\Desktop\finzave\routes\transactions.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update GET routes to pass today_date
get_tx_old = """@app_bp.route('/transactions')
@jwt_required()
def transactions():
    return render_template('app/transactions.html', expense_categories=EXPENSE_CATEGORIES)"""
get_tx_new = """@app_bp.route('/transactions')
@jwt_required()
def transactions():
    return render_template('app/transactions.html', expense_categories=EXPENSE_CATEGORIES, today_date=datetime.now().date().isoformat())"""
content = content.replace(get_tx_old, get_tx_new)

get_ex_old = """@app_bp.route('/expenses')
@jwt_required()
def all_expenses():
    return render_template('app/expenses.html', expense_categories=EXPENSE_CATEGORIES)"""
get_ex_new = """@app_bp.route('/expenses')
@jwt_required()
def all_expenses():
    return render_template('app/expenses.html', expense_categories=EXPENSE_CATEGORIES, today_date=datetime.now().date().isoformat())"""
content = content.replace(get_ex_old, get_ex_new)

# 2. Add validation to `handle_income` POST
# Find: date_val = datetime.strptime(data['date'], '%Y-%m-%d').date()
income_post_old = """            date_val = datetime.strptime(data['date'], '%Y-%m-%d').date()
            if data['income_type'] == 'Fixed':"""
income_post_new = """            date_val = datetime.strptime(data['date'], '%Y-%m-%d').date()
            if date_val > datetime.now().date():
                return jsonify({"error": "Transaction date cannot be in the future."}), 400
            if data['income_type'] == 'Fixed':"""
content = content.replace(income_post_old, income_post_new)

# 3. Add validation to `handle_income_by_id` PUT
income_put_old = """        date_val = datetime.strptime(data['date'], '%Y-%m-%d').date()
        desc = data.get('description', '').strip()"""
income_put_new = """        date_val = datetime.strptime(data['date'], '%Y-%m-%d').date()
        if date_val > datetime.now().date():
            return jsonify({"error": "Transaction date cannot be in the future."}), 400
        desc = data.get('description', '').strip()"""
content = content.replace(income_put_old, income_put_new)

# 4. Add validation to `handle_expense` POST
expense_post_old = """            date_val = datetime.strptime(data['date'], '%Y-%m-%d').date()
            amount = float(data['amount'])"""
expense_post_new = """            date_val = datetime.strptime(data['date'], '%Y-%m-%d').date()
            if date_val > datetime.now().date():
                return jsonify({"error": "Transaction date cannot be in the future."}), 400
            amount = float(data['amount'])"""
content = content.replace(expense_post_old, expense_post_new)

# 5. Add validation to `handle_expense_by_id` PUT
expense_put_old = """        date_val = datetime.strptime(data['date'], '%Y-%m-%d').date()
        desc = data.get('description', '').strip()"""
expense_put_new = """        date_val = datetime.strptime(data['date'], '%Y-%m-%d').date()
        if date_val > datetime.now().date():
            return jsonify({"error": "Transaction date cannot be in the future."}), 400
        desc = data.get('description', '').strip()"""
content = content.replace(expense_put_old, expense_put_new)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated routes/transactions.py successfully")
