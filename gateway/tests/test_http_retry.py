"""Tests for HTTP retry helper."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.services.ai.agents.http_retry import httpx_get_json


@pytest.mark.asyncio
async def test_get_json_retries_on_503_then_ok():
    """Second attempt returns 200 with JSON body."""
    url = "https://example.com/x"
    req = httpx.Request("GET", url)
    responses = [
        httpx.Response(503, json={}, request=req),
        httpx.Response(200, json={"ok": True}, request=req),
    ]
    # Each retry builds a new AsyncClient; share index across instances.
    state = {"i": 0}

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return None

        async def get(self, *a, **k):
            r = responses[state["i"]]
            state["i"] += 1
            return r

    with patch("app.services.ai.agents.http_retry.httpx.AsyncClient", FakeClient):
        with patch("app.services.ai.agents.http_retry.asyncio.sleep", new_callable=AsyncMock):
            data = await httpx_get_json("https://example.com/x", label="t", max_attempts=3)

    assert data == {"ok": True}


@pytest.mark.asyncio
async def test_get_json_no_retry_on_401():
    url = "https://example.com/x"
    req = httpx.Request("GET", url)

    class FakeClient:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return None

        async def get(self, *a, **k):
            return httpx.Response(401, json={"message": "unauthorized"}, request=req)

    with patch("app.services.ai.agents.http_retry.httpx.AsyncClient", FakeClient):
        with pytest.raises(httpx.HTTPStatusError):
            await httpx_get_json("https://example.com/x", label="t", max_attempts=3)
