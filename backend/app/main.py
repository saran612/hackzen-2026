import os
import uuid
import shutil
import hashlib
import logging
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional

from .database import engine, Base, get_db
from .models import AnalysisHistory
from .cv_analysis import analyze_skin_image
from .recommendation import generate_routine

logger = logging.getLogger("uvicorn.error")


# Create DB Tables on Startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="SkinCV API", version="1.0.0")

# Setup CORS for Frontend Dev Server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this. For hackathon, allow all.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory to save uploaded files
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Serve uploaded static files
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.post("/api/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    # Verify file is an image
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.")

    # Read image bytes
    contents = await file.read()
    
    # Debug: log image details
    img_size = len(contents)
    img_hash = hashlib.sha256(contents).hexdigest()
    logger.info(f"API Received Image: filename='{file.filename}' size={img_size} bytes hash={img_hash}")
    
    # Run MediaPipe and Heuristic CV pipeline (now returns 4 values)
    scores, regions, quality, warnings = analyze_skin_image(contents)
    
    # Generate Skincare Routine
    routine = generate_routine(scores)
    
    # Save Image locally
    file_extension = os.path.splitext(file.filename)[1]
    if not file_extension:
        file_extension = ".jpg"
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    with open(file_path, "wb") as buffer:
        buffer.write(contents)
        
    db_image_path = f"/uploads/{unique_filename}"
    
    # Save to Database History
    db_record = AnalysisHistory(
        session_id=session_id or str(uuid.uuid4()),
        image_path=db_image_path,
        scores=scores,
        regions=regions,
        routine=routine,
        quality=quality,
        warnings=warnings,
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    
    return {
        "id": db_record.id,
        "session_id": db_record.session_id,
        "timestamp": db_record.timestamp,
        "image_url": db_image_path,
        "scores": scores,
        "regions": regions,
        "routine": routine,
        "quality": quality,
        "warnings": warnings,
    }

@app.get("/api/history")
def get_history(
    session_id: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    query = db.query(AnalysisHistory)
    if session_id:
        query = query.filter(AnalysisHistory.session_id == session_id)
    records = query.order_by(AnalysisHistory.timestamp.desc()).limit(limit).all()
    
    return [
        {
            "id": r.id,
            "session_id": r.session_id,
            "timestamp": r.timestamp,
            "image_url": r.image_path,
            "scores": r.scores,
            "regions": r.regions,
            "routine": r.routine,
            "quality": r.quality,
            "warnings": r.warnings,
        }
        for r in records
    ]
