"""SQLAlchemy models for the lottery bot."""
from datetime import datetime
from sqlalchemy import BigInteger, String, DateTime, Integer, ARRAY, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import List


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class User(Base):
    """User model storing Telegram ID to phone number mapping."""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationship
    tickets: Mapped[List["Ticket"]] = relationship("Ticket", back_populates="user")
    
    def __repr__(self) -> str:
        return f"<User(telegram_id={self.telegram_id}, phone={self.phone})>"


class Ticket(Base):
    """Ticket model for lottery tickets."""
    
    __tablename__ = "tickets"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    draw_id: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    numbers: Mapped[List[int]] = mapped_column(ARRAY(Integer), nullable=True)  # NULL = auto-generate
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, active, won, lost
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="tickets")
    
    def __repr__(self) -> str:
        return f"<Ticket(id={self.id}, draw_id={self.draw_id}, numbers={self.numbers})>"
