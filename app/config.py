"""
app/config.py
=============
Centralised, immutable configuration for SkillSync.

All thresholds, model names, and runtime constants live here.
Import CONFIG from this module — never hardcode values in other modules.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NlpConfig:
    """NLP model identifiers and cosine-similarity classification thresholds."""
    spacy_model: str = "en_core_web_sm"
    sentence_transformer_model: str = "all-MiniLM-L6-v2"
    similarity_threshold_strong: float = 0.75
    similarity_threshold_partial: float = 0.55


@dataclass(frozen=True)
class AppConfig:
    """Top-level application config. Compose sub-configs here as needed."""
    nlp: NlpConfig = NlpConfig()


CONFIG = AppConfig()

