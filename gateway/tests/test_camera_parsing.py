"""Camera URL extraction from alternate JSON shapes."""

from __future__ import annotations

import pytest

from app.services.ai.agents.camera import first_camera_image_url


@pytest.mark.parametrize(
    "payload,expected",
    [
        ({"cameras": [{"image_url": "https://a.com/1.jpg"}]}, "https://a.com/1.jpg"),
        ({"data": [{"imageUrl": "https://b.com/2.jpg"}]}, "https://b.com/2.jpg"),
        (
            {"results": [{"still": {"url": "https://c.com/nested.jpg"}}]},
            "https://c.com/nested.jpg",
        ),
        ({"cameras": []}, None),
    ],
)
def test_first_camera_image_url(payload, expected):
    assert first_camera_image_url(payload) == expected
