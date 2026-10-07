"""SQLAlchemy ORM models."""

from sqlalchemy import Column, Float, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.db.base import Base


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    feature_count = Column(Integer, default=0)
    crs = Column(String, nullable=True)
    status = Column(String, default="COMPLETED")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    measurements = relationship(
        "FeatureMeasurement", back_populates="file", cascade="all, delete-orphan"
    )


class FeatureMeasurement(Base):
    __tablename__ = "feature_measurements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(String, ForeignKey("uploaded_files.id"), nullable=False)
    feature_index = Column(Integer, nullable=False)
    geometry_type = Column(String, nullable=False)
    measurement_type = Column(String, nullable=True)
    measurement_value = Column(Float, nullable=True)
    unit = Column(String, nullable=True)
    properties = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    file = relationship("UploadedFile", back_populates="measurements")
