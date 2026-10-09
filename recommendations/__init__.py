"""
Module: recommendations/__init__.py

Purpose:
Core application logic and configurations.

Flow:
User Request -> Route Handler -> Business Logic -> Database

"""
from .engine import generate_recommendations

__all__ = ['generate_recommendations']
