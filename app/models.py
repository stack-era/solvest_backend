from sqlalchemy import Boolean, Column, ForeignKey, UniqueConstraint, Integer, String, TIMESTAMP, DECIMAL

from .database import Base


class UsersKey(Base):
    __tablename__ = "usersKey"
    id = Column(Integer, primary_key=True, index=True)
    publicKey = Column(String, unique=True)