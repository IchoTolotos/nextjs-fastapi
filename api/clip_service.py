import torch
import clip
from PIL import Image
import numpy as np
from pathlib import Path
import ssl
import os

# Disable SSL verification for CLIP model download
ssl._create_default_https_context = ssl._create_unverified_context

class CLIPService:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model, self.preprocess = clip.load("ViT-B/32", device=self.device)
        
    def get_image_embedding(self, image_path: str) -> bytes:
        """Generate CLIP embedding for an image."""
        image = Image.open(image_path)
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
        """Compare text embedding with image embedding."""
        image_embedding = np.frombuffer(image_embedding_bytes, dtype=np.float32)
        image_embedding = image_embedding.reshape(1, -1)
        
        # Calculate cosine similarity
        similarity = np.dot(text_embedding, image_embedding.T)[0][0]
        return float(similarity)

# Create a singleton instance
clip_service = CLIPService() 