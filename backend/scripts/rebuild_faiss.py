import sys
import os
import json
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.connection import SessionLocal
from app.models.food_items import FoodItem
from app.services.ml_diet_pipeline.embeddings.generator import EmbeddingGenerator
from app.services.ml_diet_pipeline.embeddings.faiss_index import FaissIndex

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def rebuild():
    db = SessionLocal()
    try:
        generator = EmbeddingGenerator()
        
        # 1. Fetch all foods
        foods = db.query(FoodItem).all()
        logger.info(f"Generating embeddings for {len(foods)} foods...")
        
        canonical_names = [food.canonical_name for food in foods]
        embedding_ids = [str(food.id) for food in foods]
        
        # Generate embeddings in batch
        embeddings = generator.generate(canonical_names)
            
        # 2. Build and save FAISS index
        logger.info("Building FAISS index...")
        index = FaissIndex(dimension=len(embeddings[0]))
        index.add(embeddings)
        
        # Standard locations expected by the service
        index_dir = "app/services/ml_diet_pipeline/canonicalization/index"
        index_path = os.path.join(index_dir, "faiss.index")
        mapping_path = os.path.join(index_dir, "faiss_mapping.json")
        
        os.makedirs(index_dir, exist_ok=True)
        
        index.save(index_path)
        with open(mapping_path, "w") as f:
            json.dump(embedding_ids, f)
            
        logger.info(f"FAISS index saved to {index_path}")
        logger.info(f"Mapping saved to {mapping_path}")
        
    finally:
        db.close()

if __name__ == "__main__":
    rebuild()
