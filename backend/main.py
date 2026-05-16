"""
Medical AI Detection API
FastAPI backend for CMVD and Nutritional Rickets detection
"""

import os
import io
import time
import uuid
import logging
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import torch

from models.cmvd_model import CMVDDetector
from models.rickets_model import RicketsDetector
from utils.report import generate_ai_report
from utils.preprocess import validate_image, validate_medical_image, get_image_metadata
from database import (
    get_db, create_patient_record, get_all_patient_records, 
    delete_patient_record, get_patient_statistics, get_patient_record_by_id,
    SessionLocal
)

# ─────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# Global Model Registry
# ─────────────────────────────────────────────────────────────
detectors = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load models on startup"""
    logger.info("Loading AI detection models...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Using device: {device}")

    detectors["cmvd"] = CMVDDetector(
        model_path="checkpoints/cmvd_best.pth",
        device=device
    )
    detectors["rickets"] = RicketsDetector(
        model_path="checkpoints/rickets_best.pth",
        device=device
    )
    logger.info("Models loaded successfully!")
    yield
    logger.info("Shutting down...")


# ─────────────────────────────────────────────────────────────
# App Setup
# ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="Medical AI Detection API",
    description="Real-time AI detection for CMVD (ECG) and Nutritional Rickets (X-ray)",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────
class DetectionResponse(BaseModel):
    request_id: str
    model: str
    processing_time_ms: float
    image_metadata: dict
    result: dict
    ai_report: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    models_loaded: list
    device: str
    version: str


# ─────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────

@app.get("/", tags=["Info"])
async def root():
    return {
        "name": "Medical AI Detection API",
        "version": "1.0.0",
        "endpoints": ["/detect/cmvd", "/detect/rickets", "/health"],
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    return HealthResponse(
        status="healthy",
        models_loaded=list(detectors.keys()),
        device=device,
        version="1.0.0",
    )


@app.post("/detect/cmvd", response_model=DetectionResponse, tags=["Detection"])
async def detect_cmvd(
    file: UploadFile = File(..., description="ECG image (PNG, JPEG, TIFF)"),
    generate_report: bool = True,
):
    """
    Detect Coronary Microvascular Dysfunction (CMVD) from an ECG image.
    Only accepts grayscale/near-grayscale medical ECG images.
    Rejects natural photos, selfies, animal images etc.
    """
    return await _run_detection("cmvd", file, generate_report, image_type="ecg")


@app.post("/detect/rickets", response_model=DetectionResponse, tags=["Detection"])
async def detect_rickets(
    file: UploadFile = File(..., description="X-ray image (PNG, JPEG, TIFF)"),
    generate_report: bool = True,
):
    """
    Detect Nutritional Rickets from a pediatric X-ray image.
    Only accepts grayscale/near-grayscale medical X-ray images.
    Rejects natural photos, selfies, animal images etc.
    """
    return await _run_detection("rickets", file, generate_report, image_type="xray")


@app.post("/detect/batch", tags=["Detection"])
async def detect_batch(
    ecg_file: Optional[UploadFile] = File(None),
    xray_file: Optional[UploadFile] = File(None),
    generate_report: bool = True,
):
    """Run both CMVD and Rickets detection in a single request"""
    results = {}

    if ecg_file:
        results["cmvd"] = await _run_detection("cmvd", ecg_file, generate_report, image_type="ecg")

    if xray_file:
        results["rickets"] = await _run_detection("rickets", xray_file, generate_report, image_type="xray")

    if not results:
        raise HTTPException(status_code=400, detail="Please provide at least one image file")

    return results


# ─────────────────────────────────────────────────────────────
# Core Detection Logic
# ─────────────────────────────────────────────────────────────

async def _run_detection(
    model_type: str,
    file: UploadFile,
    generate_report: bool,
    image_type: str = "ecg"
) -> DetectionResponse:

    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    # 1. Validate file type
    allowed_types = {"image/png", "image/jpeg", "image/tiff", "image/jpg"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Allowed: PNG, JPEG, TIFF"
        )

    # 2. Read image bytes
    image_bytes = await file.read()
    if len(image_bytes) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Max size: 50MB")

    # 3. Validate it's a readable image
    is_valid, error_msg = validate_image(image_bytes)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {error_msg}")

    # 4. ← NEW: Validate it's a medical image (ECG or X-ray)
    is_medical, medical_error = validate_medical_image(image_bytes, image_type=image_type)
    if not is_medical:
        raise HTTPException(
            status_code=422,
            detail=medical_error
        )

    # 5. Get image metadata
    metadata = get_image_metadata(image_bytes)

    # 6. Run model inference
    try:
        detector = detectors[model_type]
        result = detector.predict(image_bytes)
    except Exception as e:
        logger.error(f"Inference error [{request_id}]: {e}")
        raise HTTPException(status_code=500, detail=f"Model inference failed: {str(e)}")

    # 7. Optional: Generate AI clinical report
    ai_report = None
    if generate_report:
        try:
            ai_report = await generate_ai_report(model_type, result)
        except Exception as e:
            logger.warning(f"Report generation failed [{request_id}]: {e}")

    processing_time = (time.time() - start_time) * 1000

    logger.info(
        f"[{request_id}] {model_type.upper()} | "
        f"Result: {result.get('prediction', 'N/A')} | "
        f"Time: {processing_time:.1f}ms"
    )

    return DetectionResponse(
        request_id=request_id,
        model=model_type,
        processing_time_ms=round(processing_time, 2),
        image_metadata=metadata,
        result=result,
        ai_report=ai_report,
    )


# ─────────────────────────────────────────────────────────────
# Patient Records Endpoints
# ─────────────────────────────────────────────────────────────

class SaveRecordRequest(BaseModel):
    """Schema for saving patient record"""
    patient_name: str
    gender: str
    model: str
    prediction: str
    confidence: float
    probabilities: Optional[dict] = None


@app.post("/records/save", tags=["Patient Records"])
async def save_patient_record(record_data: SaveRecordRequest):
    """Save a patient analysis record to database"""
    try:
        db = SessionLocal()
        record_id = str(uuid.uuid4())[:12]
        
        record = create_patient_record(
            db,
            record_id=record_id,
            patient_name=record_data.patient_name,
            gender=record_data.gender,
            model=record_data.model,
            prediction=record_data.prediction,
            confidence=record_data.confidence,
            probabilities=record_data.probabilities or {}
        )
        
        logger.info(f"✅ Patient record saved: {record_id}")
        
        return {
            "success": True,
            "message": "Record saved successfully",
            "record_id": record_id,
            "record": record.to_dict()
        }
    except Exception as e:
        logger.error(f"❌ Error saving record: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save record: {str(e)}")
    finally:
        db.close()


@app.get("/records/all", tags=["Patient Records"])
async def get_records():
    """Get all patient records from database"""
    try:
        db = SessionLocal()
        records = get_all_patient_records(db)
        logger.info(f"📊 Retrieved {len(records)} patient records")
        
        return {
            "success": True,
            "total": len(records),
            "records": records
        }
    except Exception as e:
        logger.error(f"❌ Error retrieving records: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve records: {str(e)}")
    finally:
        db.close()


@app.delete("/records/{record_id}", tags=["Patient Records"])
async def delete_record(record_id: str):
    """Delete a patient record by ID"""
    try:
        db = SessionLocal()
        success = delete_patient_record(db, record_id)
        
        if success:
            logger.info(f"🗑️ Patient record deleted: {record_id}")
            return {
                "success": True,
                "message": f"Record {record_id} deleted successfully"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Record {record_id} not found")
    except Exception as e:
        logger.error(f"❌ Error deleting record: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete record: {str(e)}")
    finally:
        db.close()


@app.get("/records/stats", tags=["Patient Records"])
async def get_stats():
    """Get patient records statistics"""
    try:
        db = SessionLocal()
        stats = get_patient_statistics(db)
        
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"❌ Error retrieving statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve stats: {str(e)}")
    finally:
        db.close()


# ─────────────────────────────────────────────────────────────
# Error Handlers
# ─────────────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again."}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )