# Financial Market Intelligence Pipeline

A Python-based proof-of-concept pipeline that automates monitoring of financial news and surfaces relevant insights for relationship managers.

## Features

- **Ingest** financial news from multiple RSS feeds (Yahoo Finance, MarketWatch, CNBC, SEC EDGAR)
- **Extract & Enrich** articles with:
  - Company/ticker identification (spaCy NER + regex)
  - Sentiment analysis (Ollama LLM)
  - Topic classification (earnings, M&A, regulatory, macro)
  - Price impact likelihood scoring
- **Store** processed data in SQLite for fast querying
- **Generate** daily digests with top articles per sector and AI-generated reasoning

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│   RSS Feeds     │────▶│  Enrichment      │────▶│   SQLite    │
│   SEC EDGAR     │     │  (spaCy + Ollama)│     │   Database  │
└─────────────────┘     └──────────────────┘     └─────────────┘
                                                        │
                                                        ▼
                              ┌──────────────────────────────────┐
                              │         CLI Interface            │
                              │  ingest │ digest │ query │ stats │
                              └──────────────────────────────────┘
```

## Prerequisites

1. **Python 3.11+**

2. **Ollama** (for LLM-powered analysis):
   ```bash
   # macOS
   brew install ollama
   
   # Linux
   curl -fsSL https://ollama.com/install.sh | sh
   ```

3. **Pull a model** (Llama 3.1 8B recommended):
   ```bash
   ollama pull llama3.1:8b
   ```

## Installation

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd H-poc
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Download spaCy model:
   ```bash
   python -m spacy download en_core_web_sm
   ```

## Usage

### Ingest Articles

Fetch and process financial news from RSS feeds:

```bash
python run_pipeline.py ingest
```

Options:
- `--max-articles N` - Limit number of articles to fetch (default: 200)
- `--fallback` - Use keyword-based analysis instead of Ollama (faster, offline)

### Generate Daily Digest

Create a summary report of top articles per sector:

```bash
python run_pipeline.py digest
```

Options:
- `--days N` - Include articles from last N days (default: 1)
- `--top-n N` - Number of articles per topic (default: 5)

Output saved to `output/digest_YYYY-MM-DD.md`

### Query Articles

Search and filter stored articles:

```bash
# By topic
python run_pipeline.py query --topic earnings --days 7

# By company ticker
python run_pipeline.py query --ticker AAPL

# By sentiment
python run_pipeline.py query --sentiment positive

# Combined filters
python run_pipeline.py query --topic ma --sentiment positive --limit 10
```

### View Statistics

```bash
python run_pipeline.py stats
```

## Sample Output

### Ingest Run

```
Financial Market Intelligence Pipeline
==================================================
✓ Fetched 127 articles from RSS feeds
✓ 89 new articles to process (38 already in database)

Enriching articles with Ollama...
✓ Enriched 89 articles
✓ Saved 89 articles to database (skipped 0)

Summary:
┌──────────────────────┬───────┐
│ Metric               │ Value │
├──────────────────────┼───────┤
│ Topic: earnings      │    23 │
│ Topic: macro         │    31 │
│ Topic: other         │    28 │
│ Topic: regulatory    │     7 │
│────────────────────────────────│
│ 📈 Positive          │    34 │
│ ➡️ Neutral           │    41 │
│ 📉 Negative          │    14 │
└──────────────────────┴───────┘
```

### Query Results

```
Found 15 articles:
┌──────────────────────────────────────────┬───────────────┬──────────┬───────────┬────────┬───────┐
│ Title                                    │ Sentiment     │ Topic    │ Companies │ Impact │ Date  │
├──────────────────────────────────────────┼───────────────┼──────────┼───────────┼────────┼───────┤
│ Apple Q4 Earnings Beat Expectations...   │ + positive    │ earnings │ AAPL      │ 75%    │ 01/22 │
│ Tesla Misses Delivery Targets Amid...    │ - negative    │ earnings │ TSLA      │ 80%    │ 01/21 │
│ Fed Signals Potential Rate Cut in...     │ ~ neutral     │ macro    │ —         │ 65%    │ 01/21 │
└──────────────────────────────────────────┴───────────────┴──────────┴───────────┴────────┴───────┘
```

### Daily Digest (Markdown)

```markdown
# Daily Market Intelligence Digest
**Date:** 2026-01-22
**Generated:** 2026-01-22 12:30:00 UTC
**Articles Analyzed:** 25

---

## Earnings & Financial Results

### 1. Apple Q4 Beats Wall Street Expectations
**Source:** Yahoo Finance | **Sentiment:** + Positive | **Companies:** AAPL
**Price Impact Likelihood:** 75%

> Strong iPhone sales and services revenue drove beat; guidance raised for Q1.

**Why It Matters:** Positive earnings surprise signals strong consumer demand; 
relationship managers should proactively reach out to clients with AAPL exposure.

[Read Full Article](https://example.com/article)

---
```

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_MODEL` | `llama3.1:8b` | Ollama model for analysis |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama API endpoint |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Scheduling (Cron)

Run the pipeline daily at 8am:

```bash
# Edit crontab
crontab -e

# Add line:
0 8 * * * cd /path/to/H-poc && /path/to/venv/bin/python run_pipeline.py ingest && /path/to/venv/bin/python run_pipeline.py digest
```

## Project Structure

```
H-poc/
├── src/
│   ├── __init__.py
│   ├── config.py           # Configuration settings
│   ├── models.py           # Data models
│   ├── cli.py              # CLI commands
│   ├── ingestion/
│   │   ├── rss_fetcher.py  # RSS feed fetching
│   │   └── sources.py      # Feed URLs
│   ├── enrichment/
│   │   ├── ner.py          # Company extraction
│   │   └── enricher.py     # Ollama analysis
│   ├── storage/
│   │   └── database.py     # SQLite operations
│   └── digest/
│       └── generator.py    # Digest generation
├── data/                   # SQLite database
├── output/                 # Generated digests
├── tests/
├── requirements.txt
├── run_pipeline.py         # Entry point
└── README.md
```

## Trade-offs & Decisions

| Decision | Rationale |
|----------|-----------|
| SQLite over PostgreSQL | Zero config, portable, sufficient for POC scale |
| Ollama over cloud LLM | Free, privacy-preserving, no API keys needed |
| Single LLM call per article | Reduces latency vs. separate sentiment/topic calls |
| spaCy for NER | Faster than LLM for entity extraction, good accuracy |
| RSS over web scraping | Simpler, legal, structured data |

## Future Improvements

- [ ] Add semantic search with embeddings (sentence-transformers)
- [ ] Web UI dashboard
- [ ] Real-time streaming with WebSockets
- [ ] Historical trend analysis
- [ ] Email/Slack digest delivery

## License

MIT
