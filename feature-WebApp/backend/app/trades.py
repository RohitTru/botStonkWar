from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from database.database import get_db
from models.models import Trade, Vote, User
from datetime import datetime

router = APIRouter()

class TradeCreate(BaseModel):
    stock_symbol: str
    entry_price: float
    quantity: int
    trade_type: str  # 'long' or 'short'

class TradeResponse(BaseModel):
    id: int
    stock_symbol: str
    entry_price: float
    exit_price: float | None
    quantity: int
    entry_time: datetime
    exit_time: datetime | None
    trade_type: str
    status: str
    user_id: int

    class Config:
        from_attributes = True

class VoteCreate(BaseModel):
    trade_id: int
    vote: bool  # True for yes, False for no

@router.post("/trades/", response_model=TradeResponse)
def create_trade(trade: TradeCreate, user_id: int, db: Session = Depends(get_db)):
    db_trade = Trade(
        stock_symbol=trade.stock_symbol,
        entry_price=trade.entry_price,
        quantity=trade.quantity,
        trade_type=trade.trade_type,
        status="pending",
        user_id=user_id
    )
    db.add(db_trade)
    db.commit()
    db.refresh(db_trade)
    return db_trade

@router.get("/trades/", response_model=List[TradeResponse])
def read_trades(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    trades = db.query(Trade).offset(skip).limit(limit).all()
    return trades

@router.get("/trades/{trade_id}", response_model=TradeResponse)
def read_trade(trade_id: int, db: Session = Depends(get_db)):
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if trade is None:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade

@router.post("/votes/")
def create_vote(vote: VoteCreate, user_id: int, db: Session = Depends(get_db)):
    # Check if user has already voted
    existing_vote = db.query(Vote).filter(
        Vote.trade_id == vote.trade_id,
        Vote.user_id == user_id
    ).first()
    
    if existing_vote:
        raise HTTPException(
            status_code=400,
            detail="User has already voted on this trade"
        )
    
    db_vote = Vote(
        trade_id=vote.trade_id,
        user_id=user_id,
        vote=vote.vote
    )
    db.add(db_vote)
    db.commit()
    db.refresh(db_vote)
    return db_vote

@router.get("/trades/{trade_id}/votes")
def get_trade_votes(trade_id: int, db: Session = Depends(get_db)):
    votes = db.query(Vote).filter(Vote.trade_id == trade_id).all()
    yes_votes = sum(1 for vote in votes if vote.vote)
    no_votes = len(votes) - yes_votes
    return {
        "total_votes": len(votes),
        "yes_votes": yes_votes,
        "no_votes": no_votes
    } 