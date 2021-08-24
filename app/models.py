from sqlalchemy import Boolean, Column, ForeignKey, UniqueConstraint, Integer, String, TIMESTAMP, DECIMAL

from database import Base


class UsersKey(Base):
    __tablename__ = "usersKey"
    id = Column(Integer, primary_key=True, index=True)
    publicKey = Column(String, unique=True)


class Balances(Base):
    __tablename__ = "balances"
    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey(UsersKey.id))
    tokenAccount = Column(String)
    tokenName = Column(String)
    tokenSymbol = Column(String)
    tokenIcon = Column(String)
    priceUsdt = Column(DECIMAL)
    tokenAmountUI = Column(DECIMAL)
    __table_args__ = (UniqueConstraint('userId', 'tokenSymbol', 'tokenAccount', name='_token_balance_uq'),)

