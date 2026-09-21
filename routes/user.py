from flask import Blueprint, redirect, url_for, request, jsonify
from flask_jwt_extended import verify_jwt_in_request, current_user

app_bp = Blueprint('app', __name__, url_prefix='/app')

@app_bp.before_request
def restrict_admin_access():
    try:
        verify_jwt_in_request(optional=True)
        if current_user and current_user.role == 'admin':
            if request.path.startswith('/app/api/'):
                return jsonify({"msg": "Admins cannot access user API endpoints."}), 403
            return redirect(url_for('admin.dashboard'))
    except Exception:
        pass

# Import modules to register routes to app_bp
from routes import dashboard, transactions, goals, analysis, planning, feedback, profile, reports
