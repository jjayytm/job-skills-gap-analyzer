from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NlpConfig:
    spacy_model: str = "en_core_web_sm"
    sentence_transformer_model: str = "all-MiniLM-L6-v2"
    similarity_threshold_strong: float = 0.75
    similarity_threshold_partial: float = 0.55


@dataclass(frozen=True)
class AppConfig:
    nlp: NlpConfig = NlpConfig()


CONFIG = AppConfig()

