from typing import List, Optional, TYPE_CHECKING
from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, DateTime
from extensions import db

if TYPE_CHECKING:
    from models.income import Income
    from models.expense import Expense
    from models.goal import Goal
    from models.analysis import Analysis
    from models.review import Review
    from models.feedback import Feedback
    from models.setting import Setting
    from models.activity import UserActivity

class User(db.Model):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(256))
    role: Mapped[str] = mapped_column(String(20), default='user')
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, server_default='false')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    incomes: Mapped[List["Income"]] = relationship("Income", back_populates="user", cascade="all, delete-orphan")
    expenses: Mapped[List["Expense"]] = relationship("Expense", back_populates="user", cascade="all, delete-orphan")
    goals: Mapped[List["Goal"]] = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    analyses: Mapped[List["Analysis"]] = relationship("Analysis", back_populates="user", cascade="all, delete-orphan")
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    feedbacks: Mapped[List["Feedback"]] = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")
    setting: Mapped[Optional["Setting"]] = relationship("Setting", back_populates="user", uselist=False, cascade="all, delete-orphan")
    activities: Mapped[List["UserActivity"]] = relationship("UserActivity", back_populates="user", cascade="all, delete-orphan")

    @property
    def is_online(self) -> bool:
        """Returns True if the user has activity within the last 15 minutes."""
        if not self.activities:
            return False
        # Activities are not necessarily loaded or ordered in memory, 
        # so we rely on a DB query for this or sort them if loaded.
        # But in a property, sorting loaded ones is easiest if they are eager loaded.
        # However, for performance, we should ideally query this directly when needed, 
        # but for simple template rendering:
        latest = max((a.created_at for a in self.activities), default=None)
        if not latest:
            return False
        
        # Ensure latest is aware before comparing
        if latest.tzinfo is None:
            latest = latest.replace(tzinfo=timezone.utc)
            
        now = datetime.now(timezone.utc)
        return (now - latest).total_seconds() < 900 # 15 mins
        
    @property
    def last_active(self) -> Optional[datetime]:
        """Returns the most recent activity timestamp."""
        return max((a.created_at for a in self.activities), default=None)

    def set_password(self, password: str):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)
