"""Unit tests for name normalization."""

from __future__ import annotations

import pytest

from src.utils.normalization import normalize_name


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("  Hello   World ", "hello world"),
        ("MACHOTE", "machote"),
        ("Café", "cafe"),
        ("a\tb\nc", "a b c"),
    ],
)
def test_normalize_name(raw: str, expected: str) -> None:
    assert normalize_name(raw) == expected
