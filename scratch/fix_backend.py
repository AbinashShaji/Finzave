import re

def update_csv_processor():
    filepath = r"c:\Users\abina\OneDrive\Desktop\finzave\utils\csv_processor.py"
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Update imports
    if "from models.expense import Expense" not in content:
        content = content.replace(
            "from models.expense import EXPENSE_CATEGORIES, normalize_category",
            "from models.expense import EXPENSE_CATEGORIES, normalize_category, Expense"
        )
    
    # Update signature
    if "def process_expense_csv(file_stream: bytes, user_id: int = None) -> dict:" not in content:
        content = content.replace(
            "def process_expense_csv(file_stream: bytes) -> dict:",
            "def process_expense_csv(file_stream: bytes, user_id: int = None) -> dict:"
        )
    
    # Pre-fetch existing transactions if user_id is provided
    prefetch_logic = """
    existing_hashes = set()
    if user_id:
        try:
            existing_expenses = Expense.query.filter_by(user_id=user_id).all()
            for ex in existing_expenses:
                h = f"{ex.date.isoformat()}_{ex.amount}_{ex.category}_{ex.description}"
                existing_hashes.add(h)
        except Exception as e:
            logger.error(f"Error fetching existing expenses: {str(e)}")
    
    for index, row in df.iterrows():"""
    content = content.replace("    for index, row in df.iterrows():", prefetch_logic)
    
    # Add duplicate check after validation
    duplicate_check = """
        if record['is_valid']:
            # Check for duplicates
            row_hash = f"{record['date']}_{record['amount']}_{record['category']}_{record.get('description', '')}"
            if user_id and row_hash in existing_hashes:
                record['is_valid'] = False
                record['errors'].append("Duplicate transaction")
                
        if record['is_valid']:
            valid_records.append(record)
            existing_hashes.add(row_hash) # Prevent intra-CSV duplicates
        else:"""
    content = content.replace("""        if record['is_valid']:
            valid_records.append(record)
        else:""", duplicate_check)
        
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def update_routes():
    filepath = r"c:\Users\abina\OneDrive\Desktop\finzave\routes\transactions.py"
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Negative amount validation in POST expense
    post_expense_orig = """            expense = Expense(
                user_id=user_id,
                amount=float(data['amount']),
                category=normalized_cat,
                date=date_val,
                description=data.get('description', '')
            )"""
    post_expense_new = """            amount = float(data['amount'])
            if amount <= 0:
                return jsonify({"error": "Expense amount must be greater than zero"}), 400
                
            expense = Expense(
                user_id=user_id,
                amount=amount,
                category=normalized_cat,
                date=date_val,
                description=data.get('description', '')
            )"""
    if "amount <= 0" not in content:
        content = content.replace(post_expense_orig, post_expense_new)

    # Replace generic Exception in POST expense
    except_orig = """        except Exception as e:
            return jsonify({"error": str(e)}), 400"""
    except_new = """        except ValueError as e:
            return jsonify({"error": "Invalid data format provided."}), 400
        except Exception as e:
            import logging
            logging.error(f"Error creating expense: {str(e)}")
            return jsonify({"error": "An internal error occurred."}), 400"""
    content = content.replace(except_orig, except_new, 1)

    # Replace generic exception in DELETE expense
    except_delete_orig = """        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 400"""
    except_delete_new = """        except Exception as e:
            db.session.rollback()
            import logging
            logging.error(f"Error deleting expense: {str(e)}")
            return jsonify({"error": "An internal error occurred."}), 400"""
    content = content.replace(except_delete_orig, except_delete_new, 1)

    # 2. Put expense negative amount
    put_expense_orig = """        expense.amount = float(data['amount'])
        expense.date = date_val
        expense.description = desc"""
    put_expense_new = """        amount = float(data['amount'])
        if amount <= 0:
            return jsonify({"error": "Expense amount must be greater than zero"}), 400
        expense.amount = amount
        expense.date = date_val
        expense.description = desc"""
    if "expense amount must be greater" not in content.lower(): # Only apply if not already applied
        content = content.replace(put_expense_orig, put_expense_new)

    # 3. Pagination in GET expense
    get_expense_orig = """    limit = request.args.get('limit', default=100, type=int)
    limit = max(1, min(500, limit))
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    category = request.args.get('category')

    query = Expense.query.filter_by(user_id=user_id)"""
    get_expense_new = """    page = request.args.get('page', default=1, type=int)
    per_page = request.args.get('per_page', default=20, type=int)
    per_page = max(1, min(500, per_page))
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    category = request.args.get('category')

    query = Expense.query.filter_by(user_id=user_id)"""
    content = content.replace(get_expense_orig, get_expense_new)

    get_result_orig = """    # Sort deterministic
    query = query.order_by(Expense.date.desc(), Expense.id.desc())

    total_count = query.count()
    expenses = query.limit(limit).all()

    result = [{
        "id": e.id,
        "amount": e.amount,
        "category": e.category,
        "date": e.date.isoformat(),
        "description": e.description
    } for e in expenses]

    return jsonify({
        "data": result,
        "total_count": total_count
    }), 200"""
    
    get_result_new = """    # Sort deterministic
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
    }), 200"""
    content = content.replace(get_result_orig, get_result_new)

    # 4. CSV Process duplicates (pass user_id)
    csv_orig = "result = process_expense_csv(file_bytes)"
    csv_new = "result = process_expense_csv(file_bytes, user_id=user_id)"
    content = content.replace(csv_orig, csv_new)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == '__main__':
    update_csv_processor()
    update_routes()
    print("Backend fixes applied.")
