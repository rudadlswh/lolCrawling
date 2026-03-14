"""DeepLOL scraper using Playwright-rendered HTML."""

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

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
    write_text,
)

URL = "https://www.deeplol.gg/champions"


def _fetch_rendered() -> tuple[str, str]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=USER_AGENT)
        page.goto(URL, wait_until="domcontentloaded", timeout=TIMEOUT_SECONDS * 1000)
        page.wait_for_timeout(2500)
        page.wait_for_load_state("networkidle", timeout=TIMEOUT_SECONDS * 1000)
        html = page.content()
        text = page.locator("body").inner_text()
        browser.close()
        return html, text


def scrape_deeplol() -> list[dict[str, Any]]:
    ensure_allowed_url(URL)

    html = text = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            html, text = _fetch_rendered()
            break
        except PlaywrightTimeoutError as exc:
            if attempt == MAX_RETRIES:
                raise RuntimeError("DeepLOL timed out after retries") from exc
            sleep_polite(base=attempt)

    assert html is not None and text is not None

    write_text("debug/raw_html/deeplol.html", html)
    write_text("debug/raw_text/deeplol.txt", text)

    soup = BeautifulSoup(html, "lxml")
    patch = extract_patch(text)
    updated_at_text = extract_updated_at_text(text)

    candidates: list[tuple[str, str]] = []

    for a in soup.select('a[href*="champ" i], a[href*="/champions" i], a[href*="/champion" i]'):
        champion = a.get_text(" ", strip=True)
        if not champion:
            continue
        node = a.parent
        for _ in range(8):
            if node is None:
                break
            row_text = node.get_text(" ", strip=True)
            if node.name in {"tr", "li", "div", "article"} and "%" in row_text:
                candidates.append((champion, row_text))
                break
            node = node.parent

    if not candidates:
        for line in text.splitlines():
            line = line.strip()
            if not line or "%" not in line:
                continue
            if re.search(r"\d+(?:\.\d+)?%", line):
                parts = re.split(r"\s+", line)
                champion = parts[1] if parts and parts[0].isdigit() and len(parts) > 1 else parts[0]
                candidates.append((champion, line))

    if not candidates:
        raise RuntimeError("DeepLOL selector broke: no candidate rows found")

    results: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()

    for idx, (champion, row_text) in enumerate(candidates, start=1):
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
                site="deeplol",
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
                row_text=row_text,
            )
        )

    return results
