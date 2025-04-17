from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base
import uuid

Base = declarative_base()


class Dummy(Base):
    __tablename__ = "dummy"

    name = Column(String)
    id = Column(Integer, primary_key=True, autoincrement=True)


class User(Base):
    __tablename__ = "user"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, index=True, unique=True)
    hashed_password = Column(String)
    email = Column(String, unique=True, index=True)
