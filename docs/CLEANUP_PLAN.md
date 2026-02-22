# Project Cleanup Plan

## Overview

This document outlines what files can be safely deleted to reduce clutter.

---

## Test Files to Keep (Essential)

### Backend Core Tests (`backend/tests/`)
These are organized, proper unit tests:
- `test_auth_system.py` - Authentication tests
- `test_database.py` - Database connection tests
- `test_health_calculations.py` - BMR/TDEE calculations
- `test_security.py` - Security middleware tests
- `test_api_endpoints_unit.py` - API endpoint tests

**Action**: ✅ KEEP ALL FILES in `backend/tests/` folder

---

## Test Files to DELETE (92 files in backend root)

These are ad-hoc debug/verification scripts that served their purpose:

### Connection/Setup Tests (Delete)
- `test_connection.py`
- `test_db_connection.py`
- `test_supabase_connection.py` ⚠️ KEEP THIS ONE
- `test_config.py`
- `test_groq_api.py`
- `test_hf_simple.py`
- `test_huggingface_api_key.py`

### Debug/Troubleshooting Tests (Delete)
- `test_aggregation_debug.py`
- `test_debug_logs.py`
- `test_nutrition_aggregation_debug.py`
- `test_nutrition_lookup_debug.py`
- `test_json_repair.py`

### Feature-Specific Fix Tests (Delete)
- `test_bell_peppers_fix.py`
- `test_calorie_density_fix.py`
- `test_cucumber_fix.py`
- `test_zero_calorie_fix.py`
- `test_unit_scaling_bug.py`
- `test_preferences_keyerror_fix.py`

### Architecture/Refactoring Tests (Delete)
- `test_architecture_fixes.py`
- `test_refactored_architecture.py`
- `test_hardened_architecture.py`
- `test_hardened_proof.py`

### Pipeline Tests (Delete - Duplicates)
- `test_complete_safety_pipeline.py`
- `test_safety_pipeline_demo.py`
- `test_complete_canonical_immutability_pipeline.py`
- `test_mandatory_ingredient_pipeline.py`

### Integration Tests (Delete - Redundant)
- `test_complete_system.py`
- `test_complete_fixes.py`
- `test_final_fixes_verification.py`
- `test_final_evidence.py`
- `test_runtime_evidence.py`

### Meal/Plan Tests (Keep Only Essential)
- ✅ KEEP: `test_ml_pipeline.py` - ML pipeline tests
- DELETE: `test_real_diet_plan_generation.py`
- DELETE: `test_real_meal_structure.py`
- DELETE: `test_weekly_plan.py`
- DELETE: `test_weekly_vegetarian.py`
- DELETE: `test_meal_variety.py`

### Admin Tests (Keep Only One)
- ✅ KEEP: `test_admin_system.py`
- DELETE: `test_admin_approval_system.py`
- DELETE: `test_auth_admin_field.py`

### API Tests (Keep Only One)
- DELETE: `test_api_basic.py`
- DELETE: `test_api_endpoints.py`
- DELETE: `test_fastapi_endpoint.py`
- DELETE: `test_user_list_api.py`

### Regeneration Tests (Delete - Feature Complete)
- `test_regeneration.py`
- `test_daily_regeneration.py`
- `test_day_regeneration.py`
- `test_meal_regeneration_fixes.py`

### Validation/Contract Tests (Delete - Redundant)
- `test_contract_validation_fix.py`
- `test_input_contract_enforcement.py`
- `test_input_contract_enforcement_fixes.py`
- `test_goal_aware_validation.py`
- `test_complete_goal_aware_system.py`

### Normalization Tests (Delete - Feature Complete)
- `test_normalization_order_fix.py`
- `test_normalization_final_simple.py`
- `test_final_normalization_integration.py`

### Production/Proof Tests (Delete)
- `test_production_fix.py`
- `test_production_proof.py`
- `test_production_safety_floor.py`
- `test_final_production_safety.py`

### Misc Tests (Delete)
- `test_fixes.py`
- `test_fixes_simple.py`
- `test_business_logic.py`
- `test_dietary_compliance.py`
- `test_integrity_violations.py`
- `test_soft_acceptance.py`

---

## Files to KEEP (Essential Test Files)

1. `test_supabase_connection.py` - Connection testing utility
2. `test_ml_pipeline.py` - ML pipeline tests
3. `test_admin_system.py` - Admin functionality tests
4. All files in `backend/tests/` folder

---

## Documentation Files to DELETE

### Completion Reports (Delete - Historical)
- `ADMIN_APPROVAL_SYSTEM_COMPLETION_REPORT.md`
- `ADMIN_SYSTEM_COMPLETION_REPORT.md`
- `EXACT_FIXES_COMPLETION_REPORT.md`
- `ZERO_STATE_FIX_COMPLETION_REPORT.md`
- `ML_REGENERATION_BUTTONS_COMPLETION.md`
- All `*_COMPLETION_REPORT.md` files in backend/

### Fix Reports (Delete - Historical)
- `COMPLETE_FIX_SUMMARY.md`
- `FINAL_INFINITE_LOOP_FIXES.md`
- `FINAL_NAVIGATION_AND_ADMIN_FIXES.md`
- `INFINITE_LOOP_FIX_REPORT.md`
- `NAVIGATION_FIXES_SUMMARY.md`
- `REGENERATE_DAY_FIX.md`
- `REGENERATE_MEAL_FIX.md`
- `ZERO_STATE_BUG_FIX_SUMMARY.md`

### ChatGPT Prompts (Delete - No Longer Needed)
- `CHATGPT_FILES_TO_SHARE.md`
- `CHATGPT_ZERO_STATE_FIX_PROMPT.md`
- All `CHATGPT_*.md` files in backend/

### Duplicate/Redundant Docs (Delete)
- `COMPLETE_BUG_ANALYSIS.md`
- `CURRENT_STATUS_AND_SOLUTIONS.md`
- `FILES_CREATED_SUMMARY.md`
- `AI_BUTTONS_DISABLED.md`
- `DISABLE_USER_FLOW_TEST_PLAN.md`
- `USER_DISABLE_FLOW_EXPLANATION.md`

### Migration Docs (Consolidate)
- Keep: `SUPABASE_MIGRATION_SUCCESS.md`
- Delete: `EASY_MIGRATION_GUIDE.md`
- Delete: `MIGRATE_DATA_TO_SUPABASE.md`
- Delete: `SUPABASE_CONNECTION_SETUP.md`
- Delete: `SUPABASE_MIGRATION_IMPLEMENTATION.md`
- Delete: `SUPABASE_TEAM_MIGRATION_CHECKLIST.md`

### ML Docs (Consolidate)
- Keep: `ML_MODELS_USED.md`
- Delete: `ML_PIPELINE_COMPLETE.md`
- Delete: `ML_PIPELINE_COMPLETE_EXPLANATION.md`
- Delete: `ML_PIPELINE_UI_GUIDE.md`
- Delete: `ML_REGENERATION_UI_GUIDE.md`

### Quick Start Docs (Consolidate)
- Keep: `QUICK_START.md`
- Delete: `QUICK_START_ML_PIPELINE.md`
- Delete: `QUICK_START_SUPABASE.md`
- Delete: `QUICK_TEST_ML_REGENERATION.md`

---

## Documentation to KEEP

### Essential Docs (Root)
- `README.md` - Main project readme
- `spec.md` - Project specification
- `QUICK_START.md` - Quick start guide
- `SECURITY_REMINDER.md` - Security best practices
- `GIT_PUSH_SUCCESS.md` - Recent success (can delete after reading)
- `ML_MODELS_USED.md` - ML documentation
- `SUPABASE_MIGRATION_SUCCESS.md` - Migration guide
- `GOOGLE_OAUTH_SETUP.md` - OAuth setup
- `NOTIFICATION_SYSTEM_ARCHITECTURE.md` - System architecture
- `database_management_commands.md` - DB commands

### Essential Docs (docs/)
- `docs/PROJECT_DOCUMENTATION.md` - Consolidated documentation
- `docs/CI_CD_SETUP.md` - Deployment guide
- `docs/ENVIRONMENT_SETUP.md` - Environment setup
- `docs/SUPABASE_MIGRATION.md` - Migration guide

### Essential Docs (backend/)
- `backend/ALEMBIC_MIGRATION_SYSTEM.md` - Migration system
- `backend/DATABASE_SETUP.md` - Database setup

---

## Utility Scripts to KEEP

### Backend Scripts
- `backend/start_backend.py` - Start server
- `backend/run_migrations.py` - Run migrations
- `backend/test_supabase_connection.py` - Test connection
- `backend/migrate_to_supabase.py` - Migration utility
- `backend/scripts/seed_database.py` - Seed data
- `backend/scripts/validate_config.py` - Config validation

### Backend Scripts to DELETE
- `backend/check_hcd_content.py`
- `backend/create_all_tables.py`
- `backend/create_tables_directly.py`
- `backend/debug_*.py` (all debug scripts)
- `backend/delete_user.py`
- `backend/demo_hcd_generation.py`
- `backend/setup_supabase.py`
- `backend/show_db_contents.py`
- `backend/simple_test.py`

---

## Summary

### Files to Delete
- **Test files**: ~85 files in `backend/` root
- **Documentation**: ~35 markdown files
- **Debug scripts**: ~15 Python scripts

### Files to Keep
- **Test files**: All in `backend/tests/` + 3 essential root tests
- **Documentation**: ~15 essential markdown files
- **Scripts**: ~7 utility scripts

### Space Saved
- Estimated: 2-3 MB
- Reduced clutter: 130+ files removed
- Easier navigation and maintenance

---

## Execution

Run the cleanup script:
```bash
python cleanup_project.py
```

Or manually delete files listed above.

---

**Generated**: February 22, 2026
