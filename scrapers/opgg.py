"""OP.GG champion stats scraper using requests + BeautifulSoup."""

from __future__ import annotations

import re
from typing import Any

import requests
from bs4 import BeautifulSoup

from scrapers.common import (
    MAX_RETRIES,
    TIMEOUT_SECONDS,
    USER_AGENT,
    build_row,
    ensure_allowed_url,
    extract_patch,
    extract_updated_at_text,
    normalize_position,
    normalize_tier,
    safe_float_from_percent,
    sleep_polite,
)

URL = "https://op.gg/ko/lol/champions"


def _extract_rows(soup: BeautifulSoup) -> list[tuple[str, str, str]]:
    candidates: list[tuple[str, str, str]] = []

    for anchor in soup.select('a[href*="/champions/"]'):
        champion = anchor.get_text(" ", strip=True)
        if not champion:
            continue

        row = anchor
        for _ in range(6):
            row = row.parent
            if row is None:
                break
            if row.name in {"tr", "li", "article", "section", "div"}:
                row_text = row.get_text(" ", strip=True)
                if "%" in row_text:
                    candidates.append((champion, row_text, str(row)))
                    break

    return candidates


def scrape_opgg() -> list[dict[str, Any]]:
    ensure_allowed_url(URL)

    html = None
    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(
                URL,
                headers={"User-Agent": USER_AGENT},
                timeout=TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            html = response.text
            break
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt == MAX_RETRIES:
                raise RuntimeError(f"OP.GG fetch failed after {MAX_RETRIES} attempts") from exc
            sleep_polite(base=attempt)

    assert html is not None
    soup = BeautifulSoup(html, "lxml")
    page_text = soup.get_text("\n", strip=True)
    patch = extract_patch(page_text)
    updated_at_text = extract_updated_at_text(page_text)

    rows = _extract_rows(soup)
    if not rows:
        raise RuntimeError("OP.GG selector broke: no candidate champion rows found")

    results: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()

    for idx, (champion, row_text, row_html) in enumerate(rows, start=1):
        percents = re.findall(r"\d+(?:\.\d+)?\s*%", row_text)
        win_rate = safe_float_from_percent(percents[0]) if len(percents) > 0 else None
        pick_rate = safe_float_from_percent(percents[1]) if len(percents) > 1 else None
        ban_rate = safe_float_from_percent(percents[2]) if len(percents) > 2 else None

        rank_match = re.search(r"(?:^|\s)(\d{1,3})(?:\s|$)", row_text)
        rank = int(rank_match.group(1)) if rank_match else idx

        key = (champion, rank)
        if key in seen:
            continue
        seen.add(key)

        results.append(
            build_row(
                site="opgg",
                source_url=URL,
                champion=champion,
                rank=rank,
                patch=patch,
                updated_at_text=updated_at_text,
                tier=normalize_tier(row_text),
                position=normalize_position(row_text),
                win_rate=win_rate,
                pick_rate=pick_rate,
                ban_rate=ban_rate,
                row_text=row_text if len(row_text) < 1200 else row_html[:1200],
            )
        )

    if not results:
        raise RuntimeError("OP.GG parsing failed: no normalized rows built")

    return results
