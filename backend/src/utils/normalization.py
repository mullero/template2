"""Text normalization helpers used for entity deduplication.

Referenceable entities store a ``normalized_name`` computed by
:func:`normalize_name` so lookups/dedup are case- and whitespace-insensitive.
"""

from __future__ import annotations

import re
import unicodedata

_WHITESPACE_RE = re.compile(r"\s+")


def normalize_name(value: str) -> str:
    """Return a normalized form of ``value`` for dedup and lookup.

    - Unicode NFKD fold + strip combining marks
    - lowercase
    - collapse internal whitespace to single spaces
    - trim
    """
    decomposed = unicodedata.normalize("NFKD", value)
    without_marks = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    lowered = without_marks.casefold()
    collapsed = _WHITESPACE_RE.sub(" ", lowered)
    return collapsed.strip()
