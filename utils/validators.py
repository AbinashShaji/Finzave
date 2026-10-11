"""
Module: utils/validators.py

Purpose:
Provides standardized input validation utilities across routes.
"""
import re

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+$')

def validate_email(email: str) -> bool:
    """
    Validates an email address format.
    Returns True if valid, False otherwise.
    Rejects: random_string, @, abc, test@, etc.
    Accepts: user@example.com, etc.
    """
    if not email or not isinstance(email, str):
        return False
    email_clean = email.strip()
    if len(email_clean) > 120 or len(email_clean) < 5:
        return False
    return bool(EMAIL_REGEX.match(email_clean))
