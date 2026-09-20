from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey
from extensions import db
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.user import User

class Feedback(db.Model):
    __tablename__ = 'feedback'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    feedback_type: Mapped[str] = mapped_column(String(50), nullable=False) # App Review / Bug Report / Suggestions
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default='pending', index=True) # pending, in_progress, resolved
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User", back_populates="feedbacks")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.user.username if self.user else "Unknown",
            "type": self.feedback_type,
            "content": self.content,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
