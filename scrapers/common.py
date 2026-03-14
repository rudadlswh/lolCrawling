"""Shared helpers for champion statistics crawlers."""

from __future__ import annotations

import json
import random
import re
import time
from pathlib import Path
from typing import Any, Iterable

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 "
    "lol-stats-crawler/1.0"
)

TIMEOUT_SECONDS = 20
MAX_RETRIES = 3

ALLOWED_TARGETS = {
    "https://op.gg/ko/lol/champions",
    "https://lol.ps/statistics?lang=ko",
    "https://www.deeplol.gg/champions",
}

POSITION_MAP = {
    "TOP": "TOP",
    "탑": "TOP",
    "JUNGLE": "JUNGLE",
    "정글": "JUNGLE",
    "MID": "MID",
    "미드": "MID",
    "ADC": "ADC",
    "원딜": "ADC",
    "BOTTOM": "ADC",
    "BOT": "ADC",
    "SUPPORT": "SUPPORT",
    "서폿": "SUPPORT",
    "서포터": "SUPPORT",
}


def ensure_allowed_url(url: str) -> None:
    """Prevent unexpected outbound scraping targets (basic SSRF guard)."""
    if url not in ALLOWED_TARGETS:
        raise ValueError(f"Blocked non-whitelisted URL: {url}")


def sleep_polite(base: float = 1.0) -> None:
    """Sleep with jitter to reduce bursty traffic."""
    time.sleep(base + random.uniform(0.1, 0.5))


def safe_float_from_percent(text: str | None) -> float | None:
    if not text:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
    if not match:
        return None
    return float(match.group(1))


def normalize_tier(text: str | None) -> str | None:
    if not text:
        return None
    match = re.search(r"\b([SABCD])(?:\+|-)?\b", text.upper())
    return match.group(1) if match else None


def normalize_position(text: str | None) -> str | None:
    if not text:
        return None
    upper = text.upper()
    for key, value in POSITION_MAP.items():
        if key in upper or key in text:
            return value
    return None


def extract_patch(text: str) -> str | None:
    patterns = [
        r"(?:Patch|패치)\s*([0-9]{1,2}\.[0-9]{1,2})",
        r"([0-9]{1,2}\.[0-9]{1,2})\s*(?:Patch|패치)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def extract_updated_at_text(text: str) -> str | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines[:60]:
        if any(token in line.lower() for token in ["updated", "업데이트", "갱신"]):
            return line
    return None


def write_text(path: str | Path, content: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def save_merged_json(path: str | Path, rows: Iterable[dict[str, Any]]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(list(rows), ensure_ascii=False, indent=2), encoding="utf-8")


def build_row(
    *,
    site: str,
    source_url: str,
    champion: str,
    rank: int,
    row_text: str,
    patch: str | None = None,
    updated_at_text: str | None = None,
    tier: str | None = None,
    position: str | None = None,
    win_rate: float | None = None,
    pick_rate: float | None = None,
    ban_rate: float | None = None,
) -> dict[str, Any]:
    return {
        "site": site,
        "patch": patch,
        "updated_at_text": updated_at_text,
        "rank": rank,
        "champion": champion,
        "tier": tier,
        "position": position,
        "win_rate": win_rate,
        "pick_rate": pick_rate,
        "ban_rate": ban_rate,
        "raw": {
            "source_url": source_url,
            "raw_row_text": row_text.strip(),
        },
    }
