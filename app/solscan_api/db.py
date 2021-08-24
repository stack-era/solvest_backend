from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, ForeignKey, Integer, String, TIMESTAMP, DECIMAL,Boolean, UniqueConstraint
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