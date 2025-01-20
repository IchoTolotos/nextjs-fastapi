from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
from pathlib import Path
import shutil
import uuid
from typing import List
from . import models
from .database import engine, get_db
from .clip_service import clip_service
from . import config
import logging

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the uploads directory
app.mount("/uploads", StaticFiles(directory=str(config.UPLOAD_DIR)), name="uploads")

logger = logging.getLogger(__name__)

@app.post("/api/images/upload")
async def upload_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload an image and generate its embedding."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Generate unique filename for storage
    file_extension = Path(file.filename).suffix
    storage_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = config.UPLOAD_DIR / storage_filename
    
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    try:
        # Generate embedding
        embedding = clip_service.get_image_embedding(str(file_path))
        
        # Save to database
        db_image = models.Image(
            original_filename=file.filename,
            storage_filename=storage_filename,
            storage_path=str(file_path),
            embedding=embedding
        )
        db.add(db_image)
        db.commit()
        db.refresh(db_image)
        
        return {
            "id": str(db_image.id),
            "filename": db_image.storage_filename  # Return the storage filename for frontend
        }
    except Exception as e:
        # Clean up file if something goes wrong
        os.unlink(file_path)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/images/search")
async def search_images(
    query: str, 
    db: Session = Depends(get_db)
):
    """Search images using text query."""
    try:
        # Generate text embedding
        text_embedding = clip_service.get_text_embedding(query)
        
        # Get all images
        images = db.query(models.Image).all()
        logger.info(f"Found {len(images)} images to search through")
        
        # Calculate similarities for all images
        all_results = []
        for image in images:
            try:
                similarity = clip_service.compare_embeddings(text_embedding, image.embedding)
                all_results.append({
                    "id": str(image.id),
                    "filename": image.storage_filename,
                    "similarity": similarity
                })
            except Exception as e:
                logger.error(f"Error processing image {image.id}: {str(e)}")
                continue
        
        # Sort all results by similarity
        all_results.sort(key=lambda x: x["similarity"], reverse=True)
        
        return all_results
            
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        logger.exception("Full traceback:")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/images/{image_id}")
async def delete_image(image_id: str, db: Session = Depends(get_db)):
    """Delete an image."""
    try:
        image = db.query(models.Image).filter(models.Image.id == image_id).first()
        if not image:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Delete file
        if os.path.exists(image.storage_path):
            os.unlink(image.storage_path)
        
        # Delete from database
        db.delete(image)
        db.commit()
        
        return {"status": "success", "message": "Image deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/images")
async def list_images(db: Session = Depends(get_db)):
    """List all images."""
    images = db.query(models.Image).all()
    return [{
        "id": str(image.id),
        "filename": image.storage_filename  # Use storage filename
    } for image in images]