"""
Module: tests/test_auth.py

Purpose:
Contains Pytest test cases ensuring application stability.

Flow:
User Request -> Route Handler -> Business Logic -> Database

"""
import pytest
from models.user import User
from extensions import db

def test_register_success(client):
    response = client.post('/api/auth/register', json={
        "username": "testuser_1",
        "email": "testuser_1@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "terms_accepted": True
    })
    assert response.status_code == 201
    assert b"User registered successfully" in response.data

    # Verify password stored as hash
    user = User.query.filter_by(username="testuser_1").first()
    assert user is not None
    assert user.password_hash != "Password123!"
    assert user.check_password("Password123!") is True
    assert user.role == "user"

def test_duplicate_registration(client):
    client.post('/api/auth/register', json={
        "username": "testuser_dup",
        "email": "testuser_dup@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "terms_accepted": True
    })
    
    # Try duplicate username
    response = client.post('/api/auth/register', json={
        "username": "testuser_dup",
        "email": "another@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "terms_accepted": True
    })
    assert response.status_code == 409
    assert b"Username already exists" in response.data

    # Try duplicate email
    response = client.post('/api/auth/register', json={
        "username": "testuser_dup2",
        "email": "testuser_dup@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "terms_accepted": True
    })
    assert response.status_code == 409
    assert b"Email already exists" in response.data

def test_invalid_registration_input(client):
    response = client.post('/api/auth/register', json={
        "username": "testuser_inv"
        # missing email and password
    })
    assert response.status_code == 400
    assert b"Missing required fields" in response.data

def test_login_success(client):
    # Register first
    client.post('/api/auth/register', json={
        "username": "testuser_log",
        "email": "testuser_log@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "terms_accepted": True
    })

    response = client.post('/api/auth/login', json={
        "username": "testuser_log",
        "password": "Password123!"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert "user" in data
    assert data["user"]["username"] == "testuser_log"

def test_wrong_password(client):
    client.post('/api/auth/register', json={
        "username": "testuser_wrong",
        "email": "testuser_wrong@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "terms_accepted": True
    })

    response = client.post('/api/auth/login', json={
        "username": "testuser_wrong",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    assert b"Invalid credentials" in response.data

def test_missing_jwt(client):
    response = client.get('/api/auth/me')
    assert response.status_code == 401 # Unauthorized because missing token

def test_valid_jwt_me(client):
    client.post('/api/auth/register', json={
        "username": "testuser_me",
        "email": "testuser_me@example.com",
        "password": "Password123!",
        "confirm_password": "Password123!",
        "terms_accepted": True
    })

    # The client automatically handles cookies returned by login
    client.post('/api/auth/login', json={
        "username": "testuser_me",
        "password": "Password123!"
    })

    response = client.get('/api/auth/me')
    assert response.status_code == 200
    data = response.get_json()
    assert data["username"] == "testuser_me"
    assert data["role"] == "user"
