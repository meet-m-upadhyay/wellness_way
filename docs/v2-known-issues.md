# V2 Meal Engine — Known Issues

Last updated: 2026-04-19

## Blockers (blocks feature/cuisine expansion)

### USDA Provider Returns Wrong Food Forms
**Severity:** Blocker for Mediterranean/Italian cuisines
**Impact:** USDA FDC search returns first result without form validation. "avocado" returns avocado oil (884 cal/100g, 100g fat), "cherry tomato" returns sun-dried tomato (302 cal), "red onion" returns dehydrated onion (186 cal).
**Workaround:** V2 is gated to Indian cuisine only via `V2_SUPPORTED_CUISINES` feature flag.
**Fix scope:** Medium — need a USDA response validator that prefers fresh/raw entries, filters by description keywords, and rejects implausible per-100g values (>900 cal, >100g fat).

## Minor (doesn't block shipping, monitor in production)

### LLM Undershoots Portions by 20-40%
**Severity:** Minor
**Impact:** Daily totals come in 20-40% under calorie target. Meals are nutritionally sound but portions are conservative.
**Evidence:** Indian daily plan averaged 1430 cal vs 2259 target (37% under).
**Fix scope:** Small — prompt tuning to emphasize hitting calorie target, possibly add portion guidance ("100g rice, not 50g").

### Scoring Threshold in Debug Mode
**Severity:** Minor (production flag needed before launch)
**Impact:** `ScoreBreakdown.compute_total()` uses threshold=40 for "review" band (normally 70). `MAX_RETRIES=1` (normally 3). Both marked with `SCORING_DEBUG_MODE` TODO.
**Fix scope:** Trivial — change constants after confirming production score distribution clusters above 70.

### curry powder Occasionally Slips Through Prompt Rules
**Severity:** Cosmetic
**Impact:** LLM sometimes outputs "curry powder" as a single ingredient despite the composite blend rule. Frequency: ~1 in 10 meals.
**Fix scope:** Minimal — monitor frequency at Checkpoint D. If >10%, tighten prompt.

### Protein Diversity — Chicken Dominates
**Severity:** Minor
**Impact:** LLM defaults to chicken breast for 2/3 meals despite exclude_ingredients passing used proteins. Shrimp appeared once in testing.
**Fix scope:** Small — stronger prompt diversity guidance or protein rotation config.

### Coriander Leaves Role Correction
**Severity:** Cosmetic
**Impact:** IFCT classifies coriander leaves under "Condiments and Spices" but LLM assigns "leafy_green" role. Auto-corrected to "spice" by role validation, which is technically correct per IFCT but feels wrong culinarily. Low macro impact.
**Fix scope:** Consider adding "leafy_green" as valid role for Condiments and Spices entries that are actually leaves (coriander, curry leaves, mint).
