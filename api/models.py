from sqlalchemy import Column, String, DateTime, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from .database import Base

class Image(Base):
    __tablename__ = "images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_filename = Column(String, nullable=False)  # Original uploaded filename
    storage_filename = Column(String, nullable=False)   # UUID filename in storage
    storage_path = Column(String, nullable=False)
    embedding = Column(LargeBinary, nullable=True)  # Store CLIP embeddings as binary
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 