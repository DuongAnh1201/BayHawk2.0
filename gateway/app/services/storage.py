"""Supabase Storage uploads for camera snapshot JPEGs (public bucket URLs)."""
from __future__ import annotations

import logging

from supabase import Client, create_client

from app.config import settings

logger = logging.getLogger(__name__)

_supabase: Client | None = None


def _get_supabase() -> Client | None:
    global _supabase
    if not settings.supabase_url or not settings.supabase_service_key:
        return None
    if _supabase is None:
        _supabase = create_client(settings.supabase_url, settings.supabase_service_key)
    return _supabase


def upload_snapshot(img_bytes: bytes, object_path: str) -> str:
    """Upload JPEG bytes to the configured bucket. Returns public URL, or ``""`` if skipped/failed.

    ``object_path`` is the storage key (e.g. ``cam3_20260401T120500Z.jpg``), no leading slash.
    """
    client = _get_supabase()
    if client is None:
        logger.debug("Supabase storage not configured (SUPABASE_URL / SUPABASE_SERVICE_KEY); skip upload")
        return ""
    bucket = settings.supabase_storage_bucket
    try:
        client.storage.from_(bucket).upload(
            object_path,
            img_bytes,
            file_options={"content-type": "image/jpeg", "upsert": "true"},
        )
    except Exception as exc:
        logger.warning("Supabase storage upload failed path=%s: %s", object_path, exc)
        return ""
    try:
        return client.storage.from_(bucket).get_public_url(object_path)
    except Exception as exc:
        logger.warning("Supabase get_public_url failed path=%s: %s", object_path, exc)
        return ""
