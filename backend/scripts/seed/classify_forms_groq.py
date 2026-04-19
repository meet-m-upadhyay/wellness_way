"""
Classify v2_ingredients form using Groq LLM.

Classifies entries with form='unspecified' into one of:
  raw, cooked, dry_ingredient, fresh, prepared, not_applicable

Usage:
    cd backend

    # Dry run (10 entries only):
    python scripts/seed/classify_forms_groq.py --dry-run

    # Full run:
    python scripts/seed/classify_forms_groq.py

Requires: GROQ_API_KEY env var
"""

import argparse
import asyncio
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy import text
from app.database.connection import get_session_local

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

GROQ_BASE_URL = "https://api.groq.com/openai/v1"
GROQ_MODEL = "llama-3.1-8b-instant"
MAX_CONCURRENT = 2       # Conservative to avoid 429s
BATCH_SIZE = 20           # Process in batches with sleep between
BATCH_SLEEP_SECS = 3.0    # Pause between batches
MAX_RETRIES = 3
VALID_FORMS = {"raw", "cooked", "dry_ingredient", "fresh", "prepared", "not_applicable"}

SYSTEM_PROMPT = """You are a food classification assistant. Given a food item name and its food group, classify its typical form into exactly one of these categories:

- raw: Unprocessed, uncooked (e.g., raw mango, raw chicken breast, raw fish fillet)
- cooked: Has been heat-treated (e.g., boiled egg, steamed rice, fried fish)
- dry_ingredient: Shelf-stable dry item typically stored in pantry (e.g., rice, flour, dal, dried spices, sugar, lentils, oats)
- fresh: Perishable but consumed without cooking (e.g., fresh fruits, fresh vegetables, salad greens, fresh herbs)
- prepared: Processed/fermented/manufactured food (e.g., cheese, yogurt, oil, ghee, butter, pickles, paneer)
- not_applicable: Doesn't fit any category (e.g., water, salt)

Respond with ONLY a JSON object: {"form": "category", "confidence": 0.0-1.0}
No explanation, no markdown, just the JSON."""


def build_user_prompt(name: str, food_group: str) -> str:
    return f'Food: "{name}"\nFood group: "{food_group}"\n\nClassify this food item.'


# ---------------------------------------------------------------------------
# Groq API call (uses httpx for async)
# ---------------------------------------------------------------------------

async def classify_one(client, name: str, food_group: str, headers):
    """Classify a single food item via Groq API with retry."""
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_prompt(name, food_group)},
        ],
        "temperature": 0.1,
        "max_tokens": 50,
        "response_format": {"type": "json_object"},
    }

    for attempt in range(MAX_RETRIES):
        try:
            resp = await client.post(
                f"{GROQ_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=15.0,
            )
            if resp.status_code == 429:
                wait = 2 ** (attempt + 1)
                await asyncio.sleep(wait)
                continue
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            result = json.loads(content)

            form = result.get("form", "").strip().lower()
            confidence = float(result.get("confidence", 0.0))

            if form not in VALID_FORMS:
                return None, 0.0, f"invalid form: {form}"

            return form, confidence, None

        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                return None, 0.0, str(e)
            await asyncio.sleep(2 ** (attempt + 1))

    return None, 0.0, "max retries exceeded"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def run(dry_run: bool):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("ERROR: GROQ_API_KEY env var not set. Skipping form classification.")
        sys.exit(1)

    SessionLocal = get_session_local()
    session = SessionLocal()

    try:
        # Get all unspecified entries not already classified
        result = session.execute(text("""
            SELECT code, name, food_group FROM v2_ingredients
            WHERE form = 'unspecified'
            AND (data_quality IS NULL OR data_quality NOT IN ('form_llm_inferred'))
            ORDER BY code
        """))
        rows = result.fetchall()
        total = len(rows)
        print(f"Found {total} entries with form='unspecified' to classify")

        if dry_run:
            rows = rows[:10]
            print(f"DRY RUN: processing only {len(rows)} entries")

        if not rows:
            print("Nothing to classify.")
            return

        # Classify in batches with rate-limit-friendly pacing
        import httpx

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        results = []

        async with httpx.AsyncClient() as client:
            for batch_start in range(0, len(rows), BATCH_SIZE):
                batch = rows[batch_start:batch_start + BATCH_SIZE]

                # Run batch with limited concurrency
                semaphore = asyncio.Semaphore(MAX_CONCURRENT)

                async def process(code, name, food_group):
                    async with semaphore:
                        return code, name, *(await classify_one(client, name, food_group, headers))

                batch_tasks = [process(code, name, fg) for code, name, fg in batch]
                batch_results = await asyncio.gather(*batch_tasks)
                results.extend(batch_results)

                done = batch_start + len(batch)
                print(f"  Progress: {done}/{len(rows)}", flush=True)

                # Sleep between batches to respect rate limits
                if done < len(rows):
                    await asyncio.sleep(BATCH_SLEEP_SECS)

        # Apply results to DB — fresh session to avoid stale connection after long API phase
        try:
            session.close()
        except Exception:
            pass  # old connection may already be dead
        session = SessionLocal()

        classified = 0
        errors = 0
        low_confidence = 0
        form_counts = {}

        print()  # newline after progress
        for code, name, form, confidence, error in results:
            if error:
                print(f"  ERROR {code} ({name}): {error}", flush=True)
                errors += 1
                continue

            form_counts[form] = form_counts.get(form, 0) + 1
            if confidence < 0.7:
                low_confidence += 1

            try:
                session.execute(text("""
                    UPDATE v2_ingredients
                    SET form = :form,
                        llm_confidence = :confidence,
                        data_quality = CASE
                            WHEN data_quality IS NULL THEN 'form_llm_inferred'
                            ELSE data_quality
                        END
                    WHERE code = :code
                """), {"form": form, "confidence": confidence, "code": code})
                classified += 1

                if classified % 20 == 0:
                    session.commit()
            except Exception as e:
                print(f"  DB ERROR {code}: {e}", flush=True)
                session.rollback()
                session.close()
                session = SessionLocal()

        session.commit()

        # Summary
        print(f"\n=== FORM CLASSIFICATION SUMMARY ===")
        print(f"Total processed: {len(results)}")
        print(f"Successfully classified: {classified}")
        print(f"Errors: {errors}")
        print(f"Low confidence (<0.7): {low_confidence}")
        print(f"\n--- Form Breakdown ---")
        for form, count in sorted(form_counts.items(), key=lambda x: -x[1]):
            print(f"  {form}: {count}")
        if total > len(rows):
            print(f"\nRemaining unclassified: {total - classified}")

    except Exception as e:
        session.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        session.close()


def main():
    parser = argparse.ArgumentParser(description="Classify v2_ingredients form via Groq LLM")
    parser.add_argument("--dry-run", action="store_true", help="Process only 10 entries")
    args = parser.parse_args()

    asyncio.run(run(args.dry_run))


if __name__ == "__main__":
    main()
