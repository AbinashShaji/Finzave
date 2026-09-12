from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from extensions import db
from models.activity import UserActivity
import logging

logger = logging.getLogger(__name__)

def log_activity(action: str, user_id: int = None):
    """
    Logs a non-financial user activity.
    If user_id is not provided, it attempts to fetch it from the current JWT identity.
    """
    if user_id is None:
        try:
            verify_jwt_in_request(optional=True)
            identity = get_jwt_identity()
            if identity:
                user_id = int(identity)
        except Exception:
            pass

    if user_id:
        try:
            activity = UserActivity(user_id=user_id, action=action)
            db.session.add(activity)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to log activity '{action}' for user {user_id}: {e}")
