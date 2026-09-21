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

CATEGORY_ALIASES = {
    "food": "Food & Dining",
    "groceries": "Food & Dining",
    "transport": "Transportation",
    "electricity": "Utilities",
    "internet": "Utilities",
    "medical": "Healthcare",
    "mobile recharge": "Utilities",
    "miscellaneous": "Other",
    "rent": "Rent & Housing"
}

def normalize_category(category_name: str) -> str:
    """
    Normalizes a category string.
    Checks exact matches against EXPENSE_CATEGORIES first (case-insensitive).
    Then checks against CATEGORY_ALIASES.
    Returns the canonical category name, or None if invalid.
    """
    if not category_name:
        return None
        
    cat_lower = category_name.strip().lower()
    
    # 1. Check exact match
    for canonical in EXPENSE_CATEGORIES:
        if canonical.lower() == cat_lower:
            return canonical
            
    # 2. Check aliases
    if cat_lower in CATEGORY_ALIASES:
        return CATEGORY_ALIASES[cat_lower]
        
    return None

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
