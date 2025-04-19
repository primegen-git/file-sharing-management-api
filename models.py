from datetime import datetime, timezone
from typing import List
from sqlalchemy import Column, ForeignKey, Integer, String, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
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

    files: Mapped[List["File"]] = relationship(
        "File", back_populates="owner", cascade="all, delete-orphan"
    )


class File(Base):
    __tablename__ = "file"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    filename: Mapped[str] = mapped_column(String, index=True)
    uploaded_at: Mapped[datetime] = mapped_column(
        default=datetime.now(timezone.utc), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
        index=True,
    )
    storage_path: Mapped[str] = mapped_column(String, unique=True)
    size: Mapped[int] = mapped_column(BigInteger)
    s3_url: Mapped[str] = mapped_column(String, unique=True, index=True)
    content_type: Mapped[str] = mapped_column(String, index=True)

    owner_id: Mapped["User"] = mapped_column(ForeignKey("user.id"), nullable=False)

    # NOTE: this is just used for the back_populate. main thing is the ForeignKey attribute
    owner: Mapped["User"] = relationship("User", back_populates="files")
