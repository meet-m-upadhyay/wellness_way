"""
Generate embeddings for v2_ingredients using sentence-transformers.

Model: all-MiniLM-L6-v2 (384-dim, normalized)
Storage: v2_ingredient_embeddings table via pgvector

Usage:
    cd backend
    python scripts/seed/generate_embeddings.py

Idempotent: skips ingredients that already have embeddings.
"""

import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy import text
from app.database.connection import get_session_local


def build_text_for_embedding(name, scientific_name, food_group, search_aliases):
    """Concatenate name + scientific_name + food_group + top 3 aliases."""
    parts = [name]
    if scientific_name:
        parts.append(scientific_name)
    parts.append(food_group)
    if search_aliases:
        # Take top 3 aliases that differ from the name
        added = 0
        for alias in search_aliases:
            if alias.lower() != name.lower() and added < 3:
                parts.append(alias)
                added += 1
    return " ".join(parts)


def main():
    print("Loading sentence-transformers model (all-MiniLM-L6-v2)...")
    from sentence_transformers import SentenceTransformer
    import numpy as np

    model = SentenceTransformer("all-MiniLM-L6-v2")

    SessionLocal = get_session_local()
    session = SessionLocal()

    try:
        # Get ingredients without embeddings
        rows = session.execute(text("""
            SELECT vi.id, vi.name, vi.scientific_name, vi.food_group, vi.search_aliases
            FROM v2_ingredients vi
            LEFT JOIN v2_ingredient_embeddings vie ON vie.ingredient_id = vi.id
            WHERE vie.id IS NULL
            ORDER BY vi.code
        """)).fetchall()

        total = len(rows)
        print(f"Found {total} ingredients without embeddings")

        if total == 0:
            print("Nothing to do.")
            return

        # Build texts
        texts = []
        ids = []
        for row in rows:
            t = build_text_for_embedding(row.name, row.scientific_name, row.food_group, row.search_aliases)
            texts.append(t)
            ids.append(row.id)

        # Encode in batches
        print("Encoding embeddings...")
        embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True, batch_size=64)

        # Insert into DB
        print("Inserting into v2_ingredient_embeddings...")
        for i, (ingredient_id, embedding) in enumerate(zip(ids, embeddings)):
            vec_str = "[" + ",".join(str(float(x)) for x in embedding) + "]"
            session.execute(
                text("""
                    INSERT INTO v2_ingredient_embeddings (id, ingredient_id, embedding, text_used, model_name)
                    VALUES (:id, :ingredient_id, CAST(:embedding AS vector), :text_used, 'all-MiniLM-L6-v2')
                    ON CONFLICT (ingredient_id) DO UPDATE SET
                        embedding = CAST(:embedding AS vector),
                        text_used = :text_used
                """),
                {
                    "id": str(uuid.uuid4()),
                    "ingredient_id": str(ingredient_id),
                    "embedding": vec_str,
                    "text_used": texts[i][:500],
                },
            )

            if (i + 1) % 50 == 0:
                session.commit()
                print(f"  Committed {i + 1}/{total}")

        session.commit()
        print(f"\nDone! Generated {total} embeddings.")

        # Verify
        count = session.execute(text("SELECT COUNT(*) FROM v2_ingredient_embeddings")).scalar()
        print(f"Total embeddings in DB: {count}")

    except Exception as e:
        session.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
