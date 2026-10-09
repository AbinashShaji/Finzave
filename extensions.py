"""
Module: extensions.py

Purpose:
Core application logic and configurations.

Flow:
User Request -> Route Handler -> Business Logic -> Database

"""
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate

db = SQLAlchemy()
jwt = JWTManager()
cache = Cache()
limiter = Limiter(key_func=get_remote_address, storage_uri="memory://")
migrate = Migrate()
