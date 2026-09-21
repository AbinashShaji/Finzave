from flask import render_template, request, jsonify, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from routes.user import app_bp
from extensions import db
from models.user import User
from models.setting import Setting

@app_bp.route('/settings')
@jwt_required()
def settings():
    return redirect(url_for('app.profile'))

@app_bp.route('/profile')
@jwt_required()
def profile():
    return render_template('app/profile.html')

@app_bp.route('/api/profile', methods=['GET', 'PUT'])
@jwt_required()
def api_profile():
    current_user_id = get_jwt_identity()
    user = db.session.get(User, int(current_user_id))
    
    if not user:
        return jsonify({"message": "User not found"}), 404
        
    if request.method == 'GET':
        setting = user.setting
        setting_data = {
            "currency": setting.currency if setting else "USD",
            "email_notifications": setting.email_notifications if setting else True
        }
        return jsonify({
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "settings": setting_data
        }), 200
        
    if request.method == 'PUT':
        data = request.get_json()
        if not data:
            return jsonify({"message": "Missing data"}), 400
            
        email = data.get('email')
        full_name = data.get('full_name')
        
        if email:
            # Check for duplicate email
            existing_user = User.query.filter_by(email=email).first()
            if existing_user and existing_user.id != user.id:
                return jsonify({"message": "Email is already in use by another account"}), 409
            user.email = email
            
        if full_name is not None:
            user.full_name = full_name
            
        db.session.commit()
        return jsonify({"message": "Profile updated successfully"}), 200

@app_bp.route('/api/profile/password', methods=['POST'])
@jwt_required()
def update_password():
    current_user_id = get_jwt_identity()
    user = db.session.get(User, int(current_user_id))
    
    if not user:
        return jsonify({"message": "User not found"}), 404
        
    data = request.get_json()
    if not data:
        return jsonify({"message": "Missing data"}), 400
        
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')
    
    if not current_password or not new_password or not confirm_password:
        return jsonify({"message": "All password fields are required"}), 400
        
    if not user.check_password(current_password):
        return jsonify({"message": "Incorrect current password"}), 401
        
    if new_password != confirm_password:
        return jsonify({"message": "New passwords do not match"}), 400
        
    import re
    if len(new_password) < 6:
        return jsonify({"message": "Password must be at least 6 characters"}), 400
    if not re.search(r'[A-Z]', new_password):
        return jsonify({"message": "Password must contain at least 1 uppercase letter"}), 400
    if not re.search(r'[a-z]', new_password):
        return jsonify({"message": "Password must contain at least 1 lowercase letter"}), 400
    if not re.search(r'[^a-zA-Z0-9]', new_password):
        return jsonify({"message": "Password must contain at least 1 special character"}), 400
        
    user.set_password(new_password)
    db.session.commit()
    
    return jsonify({"message": "Password updated successfully"}), 200

@app_bp.route('/api/profile/preferences', methods=['PUT'])
@jwt_required()
def update_preferences():
    current_user_id = get_jwt_identity()
    user = db.session.get(User, int(current_user_id))
    
    if not user:
        return jsonify({"message": "User not found"}), 404
        
    data = request.get_json()
    if not data:
        return jsonify({"message": "Missing data"}), 400
        
    setting = user.setting
    if not setting:
        setting = Setting(user_id=user.id)
        db.session.add(setting)
        
    currency = data.get('currency')
    email_notifications = data.get('email_notifications')
    
    if currency:
        setting.currency = currency
    if email_notifications is not None:
        setting.email_notifications = bool(email_notifications)
        
    db.session.commit()
    return jsonify({"message": "Preferences updated successfully"}), 200
