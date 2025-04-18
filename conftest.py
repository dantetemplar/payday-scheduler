from functools import lru_cache

import pytest


@pytest.fixture(autouse=True)
def patch_streamlit_cache(monkeypatch):
    """Patch streamlit.cache_data decorator with lru_cache for testing."""
    monkeypatch.setattr("streamlit.cache_data", lru_cache())
