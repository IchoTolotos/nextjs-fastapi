from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import os
from pathlib import Path
import shutil
import uuid
from typing import List
from . import models
from .database import engine, get_db
from .clip_service import clip_service

app = FastAPI()

# Create uploads directory if it doesn't exist
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Mount the uploads directory
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.post("/api/images/upload")
async def upload_image(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload an image and generate its embedding."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Generate unique filename for storage
    file_extension = Path(file.filename).suffix
    storage_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = UPLOAD_DIR / storage_filename
    
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
async def search_images(query: str, db: Session = Depends(get_db)):
    """Search images using text query."""
    try:
        # Generate text embedding
        text_embedding = clip_service.get_text_embedding(query)
        
        # Get all images
        images = db.query(models.Image).all()
        
        # Calculate similarities
        results = []
        for image in images:
            similarity = clip_service.compare_embeddings(text_embedding, image.embedding)
            results.append({
                "id": str(image.id),
                "filename": image.storage_filename,  # Use storage filename
                "similarity": similarity
            })
        
        # Sort by similarity
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results
    except Exception as e:
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