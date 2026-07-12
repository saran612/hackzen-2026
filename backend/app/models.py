import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON
from .database import Base

class AnalysisHistory(Base):
    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    image_path = Column(String, nullable=True)
    scores = Column(JSON, nullable=False)
    regions = Column(JSON, nullable=False)
    routine = Column(JSON, nullable=False)
    quality = Column(JSON, nullable=True)
    warnings = Column(JSON, nullable=True)
