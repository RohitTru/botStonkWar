from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from database.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    balance = Column(Float, default=0.0)
    
    trades = relationship("Trade", back_populates="user")
    votes = relationship("Vote", back_populates="user")

class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    stock_symbol = Column(String, index=True)
    entry_price = Column(Float)
    exit_price = Column(Float, nullable=True)
    quantity = Column(Integer)
    entry_time = Column(DateTime, default=datetime.utcnow)
    exit_time = Column(DateTime, nullable=True)
    trade_type = Column(String)  # 'long' or 'short'
    status = Column(String)  # 'pending', 'active', 'closed'
    user_id = Column(Integer, ForeignKey("users.id"))
    
    user = relationship("User", back_populates="trades")
    votes = relationship("Vote", back_populates="trade")

class Vote(Base):
    __tablename__ = "votes"

    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(Integer, ForeignKey("trades.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    vote = Column(Boolean)  # True for yes, False for no
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="votes")
    trade = relationship("Trade", back_populates="votes") 