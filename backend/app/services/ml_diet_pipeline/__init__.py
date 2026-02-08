"""
ML Diet Pipeline - New ML + constrained GenAI architecture

This module implements the ML-based diet plan generation pipeline
that lives side-by-side with the existing GenAI-only pipeline.

ARCHITECTURE:
- ML for ingredient canonicalization (sentence transformers)
- ML for meal template selection (heuristic → LightGBM)
- Deterministic nutrition calculation (reuse existing)
- Constrained GenAI for text generation ONLY

CRITICAL RULES:
- NO GenAI for numeric decisions
- NO AI retries after meal creation
- Failures must be graceful with structured logs
"""

__version__ = "0.1.0"
