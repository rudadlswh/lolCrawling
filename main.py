"""CLI entrypoint for champion statistics crawling."""

from __future__ import annotations

import argparse
import logging
from typing import Callable

from scrapers.common import save_merged_json
from scrapers.deeplol import scrape_deeplol
from scrapers.lolps import scrape_lolps
from scrapers.opgg import scrape_opgg

logger = logging.getLogger("champion-crawler")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crawl champion stats from OP.GG / LOL.PS / DeepLOL")
    parser.add_argument(
        "--site",
        choices=["all", "opgg", "lolps", "deeplol"],
        default="all",
        help="Target site to crawl",
    )
    parser.add_argument(
        "--output",
        default="output/champion_stats.json",
        help="Path to output merged JSON",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    jobs: dict[str, Callable[[], list[dict]]] = {
        "opgg": scrape_opgg,
        "lolps": scrape_lolps,
        "deeplol": scrape_deeplol,
    }

    selected = list(jobs.keys()) if args.site == "all" else [args.site]

    all_rows: list[dict] = []
    for site in selected:
        logger.info("Scraping %s...", site)
        rows = jobs[site]()
        logger.info("%s rows: %d", site, len(rows))
        all_rows.extend(rows)

    save_merged_json(args.output, all_rows)
    logger.info("Saved %d rows to %s", len(all_rows), args.output)


if __name__ == "__main__":
    main()
