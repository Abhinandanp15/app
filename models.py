from sqlalchemy import Column, Integer, String, Float, ForeignKey
from .database import Base
from datetime import datetime
from sqlalchemy import Column, DateTime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)
    wallet = Column(String, nullable=True)


class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    total_value = Column(Float)
    total_units = Column(Integer)
    available_units = Column(Integer)


class Investment(Base):
    __tablename__ = "investments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    property_id = Column(Integer, ForeignKey("properties.id"))
    units = Column(Integer)
    amount = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)