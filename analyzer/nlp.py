"""Shared spaCy pipeline (loading the model is slow, so do it once)."""
from functools import lru_cache

import spacy


@lru_cache(maxsize=1)
def get_nlp():
    try:
        return spacy.load("en_core_web_sm")
    except OSError as e:  # pragma: no cover
        raise RuntimeError("Run: python -m spacy download en_core_web_sm") from e
