import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database.connection import get_session_local
from app.models.food_items import FoodItem
from app.models.food_embeddings import FoodEmbedding
from app.services.ml_diet_pipeline.embeddings.generator import EmbeddingGenerator
from app.services.ml_diet_pipeline.embeddings.faiss_index import FaissIndex
from app.services.ml_diet_pipeline.embeddings.text_normalizer import normalize_text

def build_index():
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        # Get all foods
        foods = db.query(FoodItem).filter(FoodItem.is_deprecated == False).all()
        if not foods:
            print("No foods to index.")
            return

        print(f"Found {len(foods)} foods.")

        generator = EmbeddingGenerator()
        texts = [f.canonical_name for f in foods]
        print("Generating embeddings...")
        embeddings = generator.generate(texts)

        # Clear existing embeddings for a clean wipe since it's initial load
        db.query(FoodEmbedding).delete()

        # Build DB records
        print("Saving to database...")
        for food, text, embedding in zip(foods, texts, embeddings):
            normalized = normalize_text(text)
            record = FoodEmbedding(
                food_id=food.id,
                embedding_vector=embedding,
                normalized_text_used_for_embedding=normalized,
                preprocessing_version=generator.preprocessing_version,
                embedding_model_name=generator.model_name,
                embedding_model_version=generator.model_version
            )
            db.add(record)
        
        db.commit()

        # Build FAISS
        faiss_path = os.path.join(os.path.dirname(__file__), '..', 'faiss.index')
        mapping_path = os.path.join(os.path.dirname(__file__), '..', 'faiss_mapping.json')

        print(f"Building local FAISS index at {faiss_path}...")
        index = FaissIndex(dimension=len(embeddings[0]))
        index.add(embeddings)
        index.save(faiss_path)
        
        # Save embedding map file (ingredient IDs mapping to FAISS index)
        with open(mapping_path, "w") as f:
            json.dump([str(food.id) for food in foods], f)

        print("Successfully generated embeddings and built local FAISS index!")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    build_index()
