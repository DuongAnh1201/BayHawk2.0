"""Test harness: stub heavy imports before gateway app modules load."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

# Camera agent imports ultralytics at module load time; avoid requiring PyTorch in CI.
sys.modules.setdefault("ultralytics", MagicMock())

import pytest

from app.services.ai.agents.collection_cache import clear_all_collection_caches


@pytest.fixture(autouse=True)
def _isolate_collection_caches() -> None:
    clear_all_collection_caches()
    yield
    clear_all_collection_caches()
