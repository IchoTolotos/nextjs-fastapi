from .database import SessionLocal
from .models import Image
from .clip_service import clip_service
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_embeddings():
    """Regenerate embeddings for all images using the new CLIP model."""
    db = SessionLocal()
    try:
        # Get all images
        images = db.query(Image).all()
        logger.info(f"Found {len(images)} images to process")
        
        # Process each image
        for i, image in enumerate(images, 1):
            try:
                logger.info(f"Processing image {i}/{len(images)}: {image.original_filename}")
                
                # Generate new embedding
                new_embedding = clip_service.get_image_embedding(image.storage_path)
                
                # Update the embedding in the database
                image.embedding = new_embedding
                db.add(image)
                
                # Commit every 10 images
                if i % 10 == 0:
                    db.commit()
                    logger.info(f"Committed batch of 10 images")
                
            except Exception as e:
                logger.error(f"Error processing image {image.id}: {str(e)}")
                continue
        
        # Final commit for any remaining images
        db.commit()
        logger.info("Migration completed successfully")
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Starting embedding migration...")
    migrate_embeddings() 