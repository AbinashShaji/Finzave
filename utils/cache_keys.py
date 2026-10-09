"""
Module: utils/cache_keys.py

Purpose:
Provides reusable helper functions and core business logic.

Flow:
User Request -> Route Handler -> Business Logic -> Database

"""
from extensions import cache

def user_dashboard_key(user_id):
    return f"user_dashboard_{user_id}"

def user_transaction_key(user_id):
    return f"user_transaction_{user_id}"

def user_analysis_key(user_id):
    return f"user_analysis_{user_id}"

def user_analysis_monthly_key(user_id):
    return f"user_analysis_monthly_{user_id}"

def user_analysis_yearly_key(user_id):
    return f"user_analysis_yearly_{user_id}"

def invalidate_user_financial_cache(user_id):
    """
    Clears all financial-related cache keys for a specific user.
    To be used when a transaction is added, updated, or deleted.
    """
    cache.delete(user_dashboard_key(user_id))
    cache.delete(user_transaction_key(user_id))
    cache.delete(user_analysis_key(user_id))
    cache.delete(user_analysis_monthly_key(user_id))
    cache.delete(user_analysis_yearly_key(user_id))
