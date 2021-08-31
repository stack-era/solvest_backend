from sqlalchemy import create_engine, func
from sqlalchemy.sql import case
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, ForeignKey, Integer, String, TIMESTAMP, DECIMAL,Boolean, UniqueConstraint, DATE
from dotenv import load_dotenv
import os
from datetime import datetime
from sqlalchemy.dialects.postgresql import insert

# ENV Variables
DOTENV_PATH = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(DOTENV_PATH)
DATABASE_URI = os.environ.get("SOL_DATABASE_URI")
engine = create_engine(DATABASE_URI, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@as_declarative()
class Base:

    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()



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


class SolanaTokens(Base):
    __tablename__ = "solanaTokens"
    id = Column(Integer, primary_key=True, index=True)
    address = Column(String)
    chainId = Column(Integer)
    decimals = Column(Integer)
    logoURI = Column(String)
    name = Column(String)
    symbol = Column(String)
    priceAvailable = Column(Boolean)
    __table_args__ = (UniqueConstraint('address', 'symbol', 'chainId', 'decimals', 'logoURI', 'name', 'symbol', name='_token_name_uq'),)


class TokensPriceHistory(Base):
    __tablename__ = "tokenPriceHistory"
    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, ForeignKey(SolanaTokens.address))
    name = Column(String)
    symbol = Column(String)
    timestamp = Column(TIMESTAMP)
    price = Column(DECIMAL)


class SolvestTokens(Base):
    __tablename__ = "solvestTokens"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    symbol = Column(String, unique=True)
    underlyingTokens = Column(Integer)
    latestPrice = Column(DECIMAL)
    lastupdateTimestamp = Column(TIMESTAMP)


class UnderlyingTokens(Base):
    __tablename__ = "underlyingTokens"
    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, ForeignKey(SolanaTokens.address))
    parentToken = Column(Integer, ForeignKey(SolvestTokens.id))
    symbol = Column(String)
    name = Column(String)
    weight = Column(DECIMAL)


class UserHistoricalPortfolio(Base):
    __tablename__ = "userHistoricalPortfolio"
    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey(UsersKey.id))
    tokenAddress = Column(String, ForeignKey(SolanaTokens.address))
    timestamp = Column(TIMESTAMP)
    balance = Column(DECIMAL)


class TokensDailyData(Base):
    __tablename__ = "tokensDailyData"
    id = Column(Integer, primary_key=True, index=True)
    tokenAddress = Column(String, ForeignKey(SolanaTokens.address))
    date = Column(DATE)
    closePrice = Column(DECIMAL)


class SolvestTokensHistory(Base):
    __tablename__ = 'solvestTokensHistory'
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, ForeignKey(SolvestTokens.symbol))
    timestamp = Column(TIMESTAMP)
    price = Column(DECIMAL)


def add_update_balances(rows: list):
    try:
        db = SessionLocal()
        model = Balances
        table = model.__table__
        stmt = insert(table).values(rows)
        on_conflict = stmt.on_conflict_do_update(constraint='_token_balance_uq', set_={'userId': stmt.excluded.userId, 'tokenAccount': stmt.excluded.tokenAccount, 'tokenName': stmt.excluded.tokenName, 'tokenSymbol': stmt.excluded.tokenSymbol, 'tokenIcon': stmt.excluded.tokenIcon, 'priceUsdt': stmt.excluded.priceUsdt, 'tokenAmountUI': stmt.excluded.tokenAmountUI})
        db.execute(on_conflict)
        db.commit()
        return True
    except Exception as e:
        print(e)
        return False

def add_update_tokens(rows: list):
    try:
        db = SessionLocal()
        model = SolanaTokens
        table = model.__table__
        stmt = insert(table).values(rows)
        on_conflict = stmt.on_conflict_do_update(constraint='_token_name_uq', set_={'chainId': stmt.excluded.chainId, 'decimals': stmt.excluded.decimals, 'logoURI': stmt.excluded.logoURI, 'name': stmt.excluded.name, 'symbol': stmt.excluded.symbol, 'priceAvailable': stmt.excluded.priceAvailable})
        db.execute(on_conflict)
        db.commit()
    except Exception as e:
        print(e)
        return False

def get_solvest_tokens():
    try:
        db = SessionLocal()
        t = db.query(func.max(TokensPriceHistory.timestamp)).scalar_subquery()
        print(t)
        res = db.query(SolvestTokens).with_entities(SolvestTokens.symbol.label('solvest_symbol'), UnderlyingTokens.symbol, UnderlyingTokens.weight, TokensPriceHistory.price)\
                        .join(UnderlyingTokens, UnderlyingTokens.parentToken == SolvestTokens.id).join(TokensPriceHistory, TokensPriceHistory.address == UnderlyingTokens.address)\
                        .filter(TokensPriceHistory.timestamp == t).all()
        db.close()
        return res
    except Exception as e:
        print(e)
        return False

def get_underlying_tokens():
    try:
        db = SessionLocal()
        res = db.query(SolanaTokens).with_entities(SolanaTokens.symbol, SolanaTokens.address, SolanaTokens.name).join(UnderlyingTokens, UnderlyingTokens.address == SolanaTokens.address)\
            .group_by(UnderlyingTokens.symbol, SolanaTokens.symbol, SolanaTokens.address, SolanaTokens.name).all()
        db.close()
        return res
    except Exception as e:
        print(e)
        return False

def save_tokens_price(rows: list):
    try:
        db = SessionLocal()
        time = datetime.utcnow()
        insertRows = [TokensPriceHistory(address=row['address'], name=row['name'], symbol=row['symbol'], price=row['price'], timestamp=time) for row in rows]
        db.add_all(insertRows)
        db.commit()
        db.close()
        return True
    except Exception as e:
        print(e)
        return False

def update_solvest_tokens_price(symbols: list):
    try:
        db = SessionLocal()
        timenow = datetime.utcnow()
        insertRow = list()
        for symbol in symbols:
            insertRow.append(SolvestTokensHistory(symbol=symbol, timestamp=timenow, price=symbols[symbol]))
            updated_data = {'latestPrice': symbols[symbol], 'lastupdateTimestamp': timenow}
            db.query(SolvestTokens).filter(SolvestTokens.symbol == symbol).update(updated_data, synchronize_session=False)
        db.add_all(insertRow)
        db.commit()
        db.close()
        return True
    except Exception as e:
        print(e)
        return False

def save_user_historical_portfolio(rows: list):
    try:
        db = SessionLocal()
        insertRows = [UserHistoricalPortfolio(userId=row["userId"], tokenAddress=row["tokenAddress"], timestamp=row["balanceTimestamp"], balance=row["balance"]) for row in rows]
        db.add_all(insertRows)
        db.commit()
        return True
    except Exception as e:
        print(e)
        return False

def get_last_portfolio_update(userId):
    try:
        db = SessionLocal()
        res = db.query(UserHistoricalPortfolio).with_entities(func.max(UserHistoricalPortfolio.timestamp).label('timestamp')).filter(UserHistoricalPortfolio.userId == userId).first()
        if res:
            return int(res.timestamp.timestamp())
        else:
            return None
    except Exception as e:
        print(e)
        return False

def get_tokens_for_candle_prices():
    try:
        db = SessionLocal()
        res = db.query(SolanaTokens).with_entities(SolanaTokens.symbol, SolanaTokens.address).filter(SolanaTokens.priceAvailable).all()
        return res
    except Exception as e:
        print(e)
        return False

def add_token_daily_data(rows):
    try:
        db = SessionLocal()
        insertRows = [TokensDailyData(tokenAddress=row['address'], date=row['date'], closePrice=row['closePrice']) for row in rows]
        db.add_all(insertRows)
        db.commit()
        return True
    except Exception as e:
        print(e)
        return False