import torch
import clip
from PIL import Image
import numpy as np
from pathlib import Path
import ssl
import os
from sklearn.metrics.pairwise import cosine_similarity
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Disable SSL verification for CLIP model download
ssl._create_default_https_context = ssl._create_unverified_context

# Create models directory if it doesn't exist
MODELS_DIR = Path(__file__).parent.parent / "models"
logger.info(f"Using models directory: {MODELS_DIR}")
MODELS_DIR.mkdir(exist_ok=True)

class CLIPService:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # Use the more powerful CLIP model for better embeddings
        model_name = "ViT-L/14"
        logger.info(f"Loading CLIP model {model_name} on {self.device}")
        try:
            self.model, self.preprocess = clip.load(model_name, device=self.device, download_root=str(MODELS_DIR))
            logger.info("CLIP model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading CLIP model: {str(e)}")
            raise
        
    def get_image_embedding(self, image_path: str) -> bytes:
        """Generate CLIP embedding for an image."""
        image = Image.open(image_path).convert("RGB")  # Ensure RGB format
        image_input = self.preprocess(image).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            image_features = self.model.encode_image(image_input)
            # Normalize the features
            image_features /= image_features.norm(dim=-1, keepdim=True)
            
        # Convert to numpy and then to bytes
        numpy_array = image_features.cpu().numpy()
        return numpy_array.tobytes()
    
    def get_text_embedding(self, text: str) -> np.ndarray:
        """Generate CLIP embedding for text query."""
        text_input = clip.tokenize([text]).to(self.device)
        
        with torch.no_grad():
            text_features = self.model.encode_text(text_input)
            # Normalize the features
            text_features /= text_features.norm(dim=-1, keepdim=True)
            
        return text_features.cpu().numpy()
    
    def compare_embeddings(self, text_embedding: np.ndarray, image_embedding_bytes: bytes) -> float:
        """Compare text embedding with image embedding using sklearn's cosine_similarity."""
        image_embedding = np.frombuffer(image_embedding_bytes, dtype=np.float32)
        image_embedding = image_embedding.reshape(1, -1)
        
        # Calculate cosine similarity using sklearn
        similarity = cosine_similarity(text_embedding, image_embedding)[0][0]
        
        # Log raw similarity for analysis
        logger.info(f"Raw cosine similarity: {similarity:.4f}")
        
        # Apply non-linear scaling to increase separation
        # Shift from [-1,1] to [0,1] and then apply power scaling
        similarity = ((similarity + 1) / 2) ** 0.5  # Square root to spread out higher values
        
        # Convert to percentage (0-100 range)
        similarity_percentage = similarity * 100
        
        logger.info(f"After scaling: {similarity_percentage:.1f}%")
        
        return round(float(similarity_percentage), 1)  # Round to 1 decimal place

# Create a singleton instance
clip_service = CLIPService() 