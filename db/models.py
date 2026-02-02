"""SQLAlchemy models for the lottery bot."""
from datetime import datetime, date
from sqlalchemy import BigInteger, String, DateTime, Integer, ARRAY, ForeignKey, Numeric, Date, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import List, Optional
import json


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class User(Base):
    """User model storing Telegram ID to phone number mapping and customer data."""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    
    # Additional fields from API
    external_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    balance: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True, default=0.0)
    birthday: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    sex: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 0=female, 1=male, null=unknown
    available_tickets: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    additional_fields: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow, nullable=True)
    
    # Relationship
    tickets: Mapped[List["Ticket"]] = relationship("Ticket", back_populates="user")
    
    def __repr__(self) -> str:
        return f"<User(telegram_id={self.telegram_id}, phone={self.phone}, name={self.name})>"
    
    @property
    def additional_fields_dict(self) -> dict:
        """Parse additional_fields JSON string to dict."""
        if not self.additional_fields:
            return {}
        try:
            return json.loads(self.additional_fields)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    @additional_fields_dict.setter
    def additional_fields_dict(self, value: dict):
        """Set additional_fields from dict."""
        self.additional_fields = json.dumps(value) if value else None


class Ticket(Base):
    """Ticket model for lottery tickets."""
    
    __tablename__ = "tickets"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    external_id: Mapped[Optional[int]] = mapped_column(Integer, unique=True, nullable=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    customer_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # API customer ID
    draw_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # API draw ID
    numbers: Mapped[Optional[List[int]]] = mapped_column(ARRAY(Integer), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, active, won, lost
    is_winner: Mapped[Optional[bool]] = mapped_column(nullable=True, default=False)
    matched_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    prize_amount: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True, default=0.0)
    filled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    filled_by: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow, nullable=True)
    
    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="tickets")
    
    def __repr__(self) -> str:
        return f"<Ticket(id={self.id}, draw_id={self.draw_id}, numbers={self.numbers}, is_winner={self.is_winner})>"


class Draw(Base):
    """Draw model for lottery draws/tirazhes."""
    
    __tablename__ = "draws"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    external_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # pending, active, completed, cancelled
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    prize_pool: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    draw_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    periodicity: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    numbers_to_pick: Mapped[int] = mapped_column(Integer, nullable=False, default=6)
    numbers_total: Mapped[int] = mapped_column(Integer, nullable=False, default=45)
    prize_grid: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    winning_numbers: Mapped[Optional[List[int]]] = mapped_column(ARRAY(Integer), nullable=True)
    statistics: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow, nullable=True)
    
    def __repr__(self) -> str:
        return f"<Draw(id={self.id}, external_id={self.external_id}, name={self.name}, status={self.status})>"
    
    @property
    def prize_grid_dict(self) -> dict:
        """Parse prize_grid JSON string to dict."""
        if not self.prize_grid:
            return {}
        try:
            return json.loads(self.prize_grid)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    @property
    def statistics_dict(self) -> dict:
        """Parse statistics JSON string to dict."""
        if not self.statistics:
            return {}
        try:
            return json.loads(self.statistics)
        except (json.JSONDecodeError, TypeError):
            return {}
