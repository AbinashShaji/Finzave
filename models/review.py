from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey, Boolean
from extensions import db

if TYPE_CHECKING:
    from models.user import User

class Review(db.Model):
    __tablename__ = 'reviews'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True, nullable=True) # Optional for anonymous reviews if applicable
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='pending', index=True) # pending, accepted, live
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User", back_populates="reviews")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.user.username if self.user else "Anonymous",
            "rating": self.rating,
            "content": self.content,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
