# ML Pipeline Implementation Checklist

## Architecture Overview
- **Goal**: Implement a new ML + Deterministic + Constrained GenAI pipeline under `ml_diet_pipeline/` without modifying the existing production GenAI-only pipeline.
- **Core Principles**:
  - Deterministic layer is the source of truth (macros, scaling, validation).
  - ML assists with matching and ranking, not calculations.
  - GenAI is constrained to naming/instructions only, with strict schema.
  - Hard rejects for unresolved ingredients (<0.80 confidence).
  - No silent macro gaps; no AI fallback after meal creation.
- **Data Sources**: Pluggable Food Registry providers (USDA primary, CSV secondary).
- **Versioning**:
  - Dataset-scoped: `dataset_name`, `dataset_version`, `import_batch_id`.
  - Global `registry_version` increments on dataset updates or overrides.
  - Embedding metadata tracked per record.

## Sprint Plan
- **Sprint 1**: Food Registry foundation + embeddings + FAISS + canonicalization.
- **Sprint 2**: ML template selection + deterministic scaling/validation integration.
- **Sprint 3**: Constrained GenAI layer + observability + feature flags + endpoints.

## Detailed Task Breakdown

### Phase 1 — Food Registry Foundation
| Task | Status | Files | Notes | Rollback | Validation |
|---|---|---|---|---|---|
| Define `food_items` schema with UUID PK, dataset fields, registry version | COMPLETE | `backend/app/models/food_items.py`, `backend/alembic/versions/*` | Include `dataset_source`, `dataset_food_id`, `registry_version`, `is_deprecated` | Revert migration | Alembic upgrade/downgrade |
| Define `food_datasets` schema (`dataset_name`, `dataset_version`, `import_batch_id`) | COMPLETE | `backend/app/models/food_datasets.py`, `backend/alembic/versions/*` | Track per-dataset versioning | Revert migration | Alembic upgrade/downgrade |
| Define `registry_versions` schema (global registry version) | COMPLETE | `backend/app/models/registry_versions.py`, `backend/alembic/versions/*` | Increment on import/override | Revert migration | Alembic upgrade/downgrade |
| Define `food_audit_log` schema (separate table) | COMPLETE | `backend/app/models/food_audit_log.py`, `backend/alembic/versions/*` | Include `changed_by`, `reason` | Revert migration | Alembic upgrade/downgrade |
| Implement FoodRegistryProvider interface | COMPLETE | `backend/app/services/ml_diet_pipeline/food_registry/providers/base.py` | `fetch_foods`, `get_by_id` only | N/A | Unit tests |
| Implement USDA provider (full load, internal batching) | COMPLETE | `backend/app/services/ml_diet_pipeline/food_registry/providers/usda.py` | Filter whole-ingredient subset | N/A | Unit tests |
| Implement CSV provider (secondary ingestion) | COMPLETE | `backend/app/services/ml_diet_pipeline/food_registry/providers/csv.py` | Pluggable ingestion | N/A | Unit tests |
| Implement registry import service (dataset + registry versioning) | COMPLETE | `backend/app/services/ml_diet_pipeline/food_registry/importer.py` | Mark old items deprecated | N/A | Integration test |

### Phase 2 — Embedding + Canonicalization
| Task | Status | Files | Notes | Rollback | Validation |
|---|---|---|---|---|---|
| Define `food_embeddings` schema | COMPLETE | `backend/app/models/food_embeddings.py`, `backend/alembic/versions/*` | Store model + preprocessing metadata | Revert migration | Alembic upgrade/downgrade |
| Implement text normalization utilities (versioned) | COMPLETE | `backend/app/services/ml_diet_pipeline/embeddings/text_normalizer.py` | Track `preprocessing_version` | N/A | Unit tests |
| Implement embedding generation service (batch) | COMPLETE | `backend/app/services/ml_diet_pipeline/embeddings/generator.py` | Model: MiniLM | N/A | Unit tests |
| Implement FAISS index builder + persistence | COMPLETE | `backend/app/services/ml_diet_pipeline/embeddings/faiss_index.py` | Persist index; load on boot | N/A | Integration test |
| Add FAISS load/rebuild logs | COMPLETE | `backend/app/services/ml_diet_pipeline/embeddings/faiss_index.py` | `[FAISS_INDEX_LOADED]`, `[FAISS_INDEX_REBUILT]` | N/A | Log check |
| Implement canonicalizer service (schema + thresholds) | COMPLETE | `backend/app/services/ml_diet_pipeline/canonicalization/service.py` | Strict output schema | N/A | Unit tests |
| Add canonicalization logs | COMPLETE | `backend/app/services/ml_diet_pipeline/canonicalization/service.py` | `[CANONICALIZATION_REJECTED]`, `[CANONICALIZATION_LOW_CONF]` | N/A | Log check |
| Enforce hard reject for <0.80 | COMPLETE | `backend/app/services/ml_diet_pipeline/canonicalization/service.py` | Block meal creation | N/A | Unit tests |

### Phase 3 — ML Template Selection
| Task | Status | Files | Notes | Rollback | Validation |
|---|---|---|---|---|---|
| Implement ML template selector scaffold | COMPLETE | `backend/app/services/ml_diet_pipeline/template_selection/selector.py` | Heuristic baseline | N/A | Unit tests |
| Add instrumentation for template selection | COMPLETE | `backend/app/services/ml_diet_pipeline/template_selection/selector.py` | `[TEMPLATE_SELECTED]`, `[TEMPLATE_REJECTED]` | N/A | Log check |
| Wire selector to registry filters (diet/allergen) | COMPLETE | `backend/app/services/ml_diet_pipeline/template_selection/selector.py` | Use authoritative metadata | N/A | Unit tests |

### Phase 4 — Deterministic Scaling + Validation Integration
| Task | Status | Files | Notes | Rollback | Validation |
|---|---|---|---|---|---|
| Integrate registry nutrition into deterministic engine | COMPLETE | `backend/app/services/ml_diet_pipeline/nutrition/engine.py` | No macro inference | N/A | Unit tests |
| Ensure scaling unchanged (deterministic math) | COMPLETE | `backend/app/services/ml_diet_pipeline/scaling/engine.py` | Preserve existing logic | N/A | Unit tests |
| Validation engine integration with registry flags | COMPLETE | `backend/app/services/ml_diet_pipeline/validation/engine.py` | Enforce allergens/diet flags | N/A | Unit tests |
| Add scaling logs | COMPLETE | `backend/app/services/ml_diet_pipeline/scaling/engine.py` | `[SCALING_APPLIED]` | N/A | Log check |

### Phase 5 — Constrained GenAI Layer
| Task | Status | Files | Notes | Rollback | Validation |
|---|---|---|---|---|---|
| Define GenAI schema contract | COMPLETE | `backend/app/services/ml_diet_pipeline/genai/schema.py` | Strict JSON schema | N/A | Unit tests |
| Implement GenAI service wrapper (read-only) | COMPLETE | `backend/app/services/ml_diet_pipeline/genai/service.py` | No ingredient/macro edits | N/A | Unit tests |
| Add GenAI schema validation + fallback | COMPLETE | `backend/app/services/ml_diet_pipeline/genai/service.py` | `[GENAI_SCHEMA_VALID]`, `[GENAI_SCHEMA_INVALID_FALLBACK]` | N/A | Unit tests |

### Phase 6 — Observability + Instrumentation
| Task | Status | Files | Notes | Rollback | Validation |
|---|---|---|---|---|---|
| Add pipeline-level structured logging | COMPLETE | `backend/app/services/ml_diet_pipeline/logging.py` | Correlation IDs | N/A | Log check |
| Add user regeneration logs | COMPLETE | `backend/app/api/endpoints/diet_plans_ml.py` | `[USER_REGENERATE]` | N/A | Log check |
| Add validation failure logs | COMPLETE | `backend/app/services/ml_diet_pipeline/validation/engine.py` | Include reason | N/A | Log check |

### Phase 7 — ML Endpoints + Feature Flag
| Task | Status | Files | Notes | Rollback | Validation |
|---|---|---|---|---|---|
| Add new ML endpoints (feature-flagged) | COMPLETE | `backend/app/api/endpoints/diet_plans_ml.py`, `backend/app/core/config.py` | No changes to existing GenAI pipeline | N/A | API test |
| Add feature flag gating | COMPLETE | `backend/app/core/config.py` | `ENABLE_ML_PIPELINE` | N/A | Unit tests |
| Add ML pipeline orchestrator wiring | COMPLETE | `backend/app/services/ml_diet_pipeline/orchestrator.py` | Keep new module isolated | N/A | Integration test |

## Risks
- Dataset ingestion scale may exceed memory in future datasets.
- Embedding model/version changes can cause canonicalization drift.
- FAISS index persistence and rebuild timing may become inconsistent if not properly versioned.
- Logging volume could become high without sampling/levels.
- Manual overrides require strong audit discipline to avoid silent macro changes.

## Open Questions
- None pending. (Add here when new ambiguity arises.)

## Change Log
- 2026-02-23: Added CSV provider and registry import service.
- 2026-02-23: Added food embeddings model/migration and embedding utilities.
- 2026-02-23: Added FAISS index wrapper and canonicalization service.
- 2026-02-23: Added template selector scaffold with logging.
- 2026-02-23: Added nutrition, scaling, and validation engines.
- 2026-02-23: Added constrained GenAI schema and service wrapper.
- 2026-02-23: Added ML pipeline logging helpers and regeneration logs.
- 2026-02-23: Added ML pipeline feature flag and endpoint gating.
- 2026-02-23: Added ML pipeline component wiring helper.
- 2026-02-23: Added USDA registry provider (`food_registry/providers/usda.py`).
- 2026-02-23: Added FoodRegistryProvider interface (`food_registry/providers/base.py`).
- 2026-02-23: Added `food_audit_log` model and migration (`add_food_audit_log_table`).
- 2026-02-23: Added `registry_versions` model and migration (`add_registry_versions_table`).
- 2026-02-23: Added `food_datasets` model and migration (`add_food_datasets_table`).
- 2026-02-23: Added `food_items` model and migration (`add_food_items_table`).
- 2026-02-23: Initial checklist created with all tasks marked TODO.
