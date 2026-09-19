from datetime import date, datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Float, Date, DateTime, ForeignKey, Index
from extensions import db

if TYPE_CHECKING:
    from models.user import User

EXPENSE_CATEGORIES = [
    "Food & Dining",
    "Transportation",
    "Shopping",
    "Rent & Housing",
    "Utilities",
    "Healthcare",
    "Education",
    "Entertainment",
    "Bills & Subscriptions",
    "Travel",
    "Personal Care",
    "Investments",
    "Insurance",
    "Family",
    "EMI",
    "Other"
]

class Expense(db.Model):
    __tablename__ = 'expenses'
    __table_args__ = (Index('ix_expense_user_date', 'user_id', 'date'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship("User", back_populates="expenses")
