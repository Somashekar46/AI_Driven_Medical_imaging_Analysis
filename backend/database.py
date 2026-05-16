"""
Database module for storing patient records
Uses SQLite for persistent storage
"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from typing import Optional, Dict, Any

# Database configuration
DATABASE_URL = "sqlite:///./patient_records.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ─────────────────────────────────────────────────────────────
# Database Models
# ─────────────────────────────────────────────────────────────

class PatientRecordDB(Base):
    """SQLAlchemy model for patient records"""
    __tablename__ = "patient_records"
    
    id = Column(String, primary_key=True)
    patient_name = Column(String, index=True)
    gender = Column(String)
    model = Column(String)
    prediction = Column(String)
    confidence = Column(Float)
    all_probabilities = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "patientName": self.patient_name,
            "gender": self.gender,
            "model": self.model,
            "prediction": self.prediction,
            "confidence": self.confidence,
            "allProbabilities": self.all_probabilities,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


# Create tables
Base.metadata.create_all(bind=engine)


# ─────────────────────────────────────────────────────────────
# Pydantic Schemas
# ─────────────────────────────────────────────────────────────

class PatientRecordCreate(BaseModel):
    """Schema for creating a patient record"""
    patient_name: str
    gender: str
    model: str
    prediction: str
    confidence: float
    all_probabilities: Optional[Dict[str, Any]] = None


class PatientRecordResponse(BaseModel):
    """Schema for returning patient record"""
    id: str
    patientName: str
    gender: str
    model: str
    prediction: str
    confidence: float
    allProbabilities: Optional[Dict[str, Any]]
    timestamp: str


# ─────────────────────────────────────────────────────────────
# Database Functions
# ─────────────────────────────────────────────────────────────

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_patient_record(db, record_id: str, patient_name: str, gender: str, 
                         model: str, prediction: str, confidence: float, 
                         probabilities: Dict[str, Any]) -> PatientRecordDB:
    """Create a new patient record in database"""
    db_record = PatientRecordDB(
        id=record_id,
        patient_name=patient_name,
        gender=gender,
        model=model,
        prediction=prediction,
        confidence=confidence,
        all_probabilities=probabilities,
        timestamp=datetime.utcnow()
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


def get_all_patient_records(db) -> list:
    """Get all patient records from database"""
    records = db.query(PatientRecordDB).order_by(PatientRecordDB.timestamp.desc()).all()
    return [record.to_dict() for record in records]


def get_patient_records_by_name(db, patient_name: str) -> list:
    """Get patient records by name"""
    records = db.query(PatientRecordDB).filter(
        PatientRecordDB.patient_name.ilike(f"%{patient_name}%")
    ).order_by(PatientRecordDB.timestamp.desc()).all()
    return [record.to_dict() for record in records]


def get_patient_record_by_id(db, record_id: str) -> Optional[PatientRecordDB]:
    """Get a specific patient record by ID"""
    return db.query(PatientRecordDB).filter(PatientRecordDB.id == record_id).first()


def delete_patient_record(db, record_id: str) -> bool:
    """Delete a patient record by ID"""
    record = db.query(PatientRecordDB).filter(PatientRecordDB.id == record_id).first()
    if record:
        db.delete(record)
        db.commit()
        return True
    return False


def get_patient_statistics(db) -> Dict[str, Any]:
    """Get statistics about patient records"""
    records = db.query(PatientRecordDB).all()
    total = len(records)
    
    if total == 0:
        return {
            "total_records": 0,
            "by_model": {},
            "by_prediction": {},
            "average_confidence": 0
        }
    
    # Count by model
    by_model = {}
    by_prediction = {}
    total_confidence = 0
    
    for record in records:
        # Count by model
        by_model[record.model] = by_model.get(record.model, 0) + 1
        
        # Count by prediction
        by_prediction[record.prediction] = by_prediction.get(record.prediction, 0) + 1
        
        # Sum confidence for average
        total_confidence += record.confidence
    
    return {
        "total_records": total,
        "by_model": by_model,
        "by_prediction": by_prediction,
        "average_confidence": round(total_confidence / total, 3)
    }
