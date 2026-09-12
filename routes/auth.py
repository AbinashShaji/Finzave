from flask import Blueprint, request, jsonify
from extensions import db
from models.user import User
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity,
    set_access_cookies, unset_jwt_cookies
)
from extensions import limiter

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

import re

@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
def register():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Missing JSON in request"}), 400

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    confirm_password = data.get('confirm_password')
    terms_accepted = data.get('terms_accepted')

    if not username or not email or not password or not confirm_password:
        return jsonify({"message": "Missing required fields"}), 400
        
    if password != confirm_password:
        return jsonify({"message": "Passwords do not match"}), 400
        
    if not terms_accepted:
        return jsonify({"message": "You must accept the Terms & Conditions"}), 400

    # Password Validation
    if len(password) < 6:
        return jsonify({"message": "Password must be at least 6 characters"}), 400
    if not re.search(r'[A-Z]', password):
        return jsonify({"message": "Password must contain at least 1 uppercase letter"}), 400
    if not re.search(r'[a-z]', password):
        return jsonify({"message": "Password must contain at least 1 lowercase letter"}), 400
    if not re.search(r'[^a-zA-Z0-9]', password):
        return jsonify({"message": "Password must contain at least 1 special character"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"message": "Username already exists"}), 409
    
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already exists"}), 409

    # Add user
    new_user = User(username=username, email=email)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Missing JSON in request"}), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"message": "Missing required fields"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"message": "Invalid credentials"}), 401

    access_token = create_access_token(identity=str(user.id))
    response = jsonify({
        "message": "Login successful",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
    })
    set_access_cookies(response, access_token)
    return response, 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    response = jsonify({"message": "Logout successful"})
    unset_jwt_cookies(response)
    return response, 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    current_user_id = get_jwt_identity()
    user = db.session.get(User, int(current_user_id))
    
    if not user:
        return jsonify({"message": "User not found"}), 404

    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "created_at": user.created_at.isoformat()
    }), 200
