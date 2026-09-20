from flask import render_template
from flask_jwt_extended import jwt_required
from routes.user import app_bp

@app_bp.route('/settings')
@jwt_required()
def settings():
    return render_template('app/settings.html')
