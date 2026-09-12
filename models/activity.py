from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, ForeignKey, Index
from extensions import db

class UserActivity(db.Model):
    __tablename__ = 'user_activities'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    user: Mapped["User"] = relationship("User", back_populates="activities")

    __table_args__ = (
        Index('idx_user_activity_recent', 'user_id', 'created_at'),
    )
