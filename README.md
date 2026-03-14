# LoL Champion Stats Crawler

Production-oriented crawler for champion statistics from:

- OP.GG: `https://op.gg/ko/lol/champions`
- LOL.PS: `https://lol.ps/statistics?lang=ko`
- DeepLOL: `https://www.deeplol.gg/champions`

It merges normalized data into `output/champion_stats.json`.

## Why this architecture

- **OP.GG**: first attempted as lightweight `requests + BeautifulSoup` parser.
- **LOL.PS / DeepLOL**: rendered with Playwright, then parsed with BeautifulSoup.
- Defensive parsing with retries, timeouts, and graceful handling of missing fields.
- Debug artifacts for browser-rendered sources:
  - `debug/raw_html/lolps.html`
  - `debug/raw_html/deeplol.html`
  - `debug/raw_text/lolps.txt`
  - `debug/raw_text/deeplol.txt`

## Install

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

## Run

```bash
python main.py --site all
python main.py --site opgg
python main.py --site lolps
python main.py --site deeplol
```

Optional custom output path:

```bash
python main.py --site all --output output/champion_stats.json
```

## Output schema

Each row is normalized as:

```json
{
  "site": "opgg|lolps|deeplol",
  "patch": "string or null",
  "updated_at_text": "string or null",
  "rank": 1,
  "champion": "Ahri",
  "tier": "S|A|B|C|D|null",
  "position": "TOP|JUNGLE|MID|ADC|SUPPORT|null",
  "win_rate": 52.36,
  "pick_rate": 14.85,
  "ban_rate": 8.89,
  "raw": {
    "source_url": "original url",
    "raw_row_text": "original parsed text for debugging"
  }
}
```

## Selector strategy (summary)

### OP.GG (`scrapers/opgg.py`)
- Fetch HTML with requests.
- Find anchors containing `/champions/`.
- Walk upward to nearest row-like container (`tr/li/div/article/section`) containing `%`.
- Extract rank/champion/percent fields and optional tier/position from row text.

### LOL.PS (`scrapers/lolps.py`)
- Render with Playwright (`domcontentloaded + networkidle + short wait`).
- Save rendered HTML/text debug artifacts.
- Parse champion links and enclosing row-like blocks with `%` values.
- Fallback to text-line parsing when links/selectors drift.

### DeepLOL (`scrapers/deeplol.py`)
- Render with Playwright and dump debug artifacts.
- Parse champion links plus closest row-like container containing `%` stats.
- Fallback to text-line parsing if DOM selectors fail.

## Reliability and safety notes

- Retries are bounded (`MAX_RETRIES=3`) with small jittered delays.
- Requests and page loads use timeouts.
- URL target whitelist prevents accidental crawling of arbitrary URLs (basic SSRF guard).
- No Riot API usage.
- No anti-bot bypassing, login-wall bypassing, or high-frequency requests.
- Clear custom User-Agent is configured.

## Known limitations

- These target sites may change markup frequently; if selectors break, the crawler raises explicit errors.
- This environment may block outbound access to target domains; run in a network environment that can reach the sites.
- Position/tier extraction is heuristic and depends on source text availability.
