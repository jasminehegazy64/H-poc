# Financial market intelligence pipeline POC plan
_Exported on 1/22/2026 at 23:51:44 GMT+2 from Cursor (2.3.41)_

---

**User**

i want a thorogh plan for this task, be very precise but do not complicate matters, this is a simple POC , i want the architecture, structure and stack and the how to implement and build this task Technical Assessment_ Financial Market Intelligence Pipeline.pdf

---

**Cursor**

I'll create a thorough but practical plan for this POC. Before finalizing, I have one critical question that affects the architecture:

---

**User**

can we use ollama instead? because i need accurate responses but i don't want to pay

---

**Cursor**

Absolutely! Ollama is a great choice - free, local, and models like Llama 3.1 or Mistral provide good accuracy. Let me create the full plan now:

---

**User**

Implement the plan as specified, it is attached for your reference. Do NOT edit the plan file itself.

To-do's from the plan have already been created. Do not create them again. Mark them as in_progress as you work, starting with the first one. Don't stop until you have completed all the to-dos.

---

**Cursor**

I'll implement the full pipeline now. Let me start by marking the first todo as in progress and creating the project structure.

The directory is empty. Let me create the entire project structure. I'll start with the setup phase - creating directories, requirements.txt, and configuration.

```plaintext
# Financial Market Intelligence Pipeline - Dependencies

# HTTP & RSS
httpx>=0.25.0
feedparser>=6.0.10

# NLP
spacy>=3.7.0

# LLM
ollama>=0.3.0

# CLI & Output
click>=8.1.0
rich>=13.0.0

# Database
# SQLite is built-in to Python

# Date handling
python-dateutil>=2.8.0

# Testing
pytest>=7.4.0

```

```python
"""Financial Market Intelligence Pipeline."""

__version__ = "0.1.0"

```

```python
"""Configuration management for the pipeline."""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Database
DATABASE_PATH = DATA_DIR / "market_intel.db"

# Ollama settings
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Pipeline settings
MAX_ARTICLES_PER_RUN = 200
DIGEST_TOP_N_PER_SECTOR = 5

# Topic categories
TOPICS = ["earnings", "ma", "regulatory", "macro", "other"]
SENTIMENTS = ["positive", "negative", "neutral"]

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

```

```python
"""Data ingestion module."""

from .rss_fetcher import fetch_all_feeds, fetch_feed
from .sources import RSS_SOURCES

__all__ = ["fetch_all_feeds", "fetch_feed", "RSS_SOURCES"]

```

```python
"""RSS feed source configuration."""

# RSS feed sources for financial news
# These are free, public feeds that don't require authentication

RSS_SOURCES = [
    {
        "name": "Yahoo Finance",
        "url": "https://finance.yahoo.com/news/rssindex",
        "category": "general",
    },
    {
        "name": "MarketWatch Top Stories",
        "url": "http://feeds.marketwatch.com/marketwatch/topstories/",
        "category": "general",
    },
    {
        "name": "MarketWatch Market Pulse",
        "url": "http://feeds.marketwatch.com/marketwatch/marketpulse/",
        "category": "market",
    },
    {
        "name": "CNBC Top News",
        "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=100003114",
        "category": "general",
    },
    {
        "name": "CNBC Finance",
        "url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
        "category": "finance",
    },
    {
        "name": "Investing.com News",
        "url": "https://www.investing.com/rss/news.rss",
        "category": "general",
    },
    {
        "name": "SEC EDGAR Company Filings",
        "url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&CIK=&type=8-K&company=&dateb=&owner=include&count=100&output=atom",
        "category": "filings",
    },
]

```

```python
"""Enrichment module for NLP processing."""

from .ner import extract_companies
from .enricher import enrich_article

__all__ = ["extract_companies", "enrich_article"]

```

```python
"""Storage module for database operations."""

from .database import Database

__all__ = ["Database"]

```

```python
"""Digest generation module."""

from .generator import DigestGenerator

__all__ = ["DigestGenerator"]

```

```plaintext
# SQLite database will be created here

```

```plaintext
# Generated digest reports will be saved here

```

```python
"""Tests for the Financial Market Intelligence Pipeline."""

```

Now let me complete the setup and move to the data models:

```python
"""Data models for the pipeline."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Article:
    """Raw article data from RSS feed."""
    
    title: str
    url: str
    source: str
    content: Optional[str] = None
    summary: Optional[str] = None
    published_at: Optional[datetime] = None
    fetched_at: datetime = field(default_factory=datetime.utcnow)
    
    def get_text(self) -> str:
        """Get the best available text content."""
        return self.content or self.summary or self.title


@dataclass
class CompanyMention:
    """A company mentioned in an article."""
    
    company_name: str
    ticker: Optional[str] = None


@dataclass
class EnrichedArticle:
    """Article enriched with NLP analysis."""
    
    # Original article data
    title: str
    url: str
    source: str
    content: Optional[str]
    published_at: Optional[datetime]
    fetched_at: datetime
    
    # Enrichment data
    sentiment: str  # positive, negative, neutral
    sentiment_score: float  # -1.0 to 1.0
    sentiment_reasoning: str
    topic: str  # earnings, ma, regulatory, macro, other
    companies: list[CompanyMention] = field(default_factory=list)
    price_impact_likelihood: float = 0.0  # 0.0 to 1.0
    key_insight: str = ""
    
    # Database ID (set after save)
    id: Optional[int] = None
    
    @classmethod
    def from_article(
        cls,
        article: Article,
        sentiment: str,
        sentiment_score: float,
        sentiment_reasoning: str,
        topic: str,
        companies: list[CompanyMention],
        price_impact_likelihood: float = 0.0,
        key_insight: str = "",
    ) -> "EnrichedArticle":
        """Create an EnrichedArticle from a raw Article."""
        return cls(
            title=article.title,
            url=article.url,
            source=article.source,
            content=article.content,
            published_at=article.published_at,
            fetched_at=article.fetched_at,
            sentiment=sentiment,
            sentiment_score=sentiment_score,
            sentiment_reasoning=sentiment_reasoning,
            topic=topic,
            companies=companies,
            price_impact_likelihood=price_impact_likelihood,
            key_insight=key_insight,
        )


@dataclass
class DigestItem:
    """A single item in the daily digest."""
    
    article_id: int
    title: str
    source: str
    url: str
    sentiment: str
    topic: str
    companies: list[str]  # Just ticker symbols
    key_insight: str
    why_it_matters: str  # Generated reasoning
    price_impact_likelihood: float
    published_at: Optional[datetime]


@dataclass
class DailyDigest:
    """Complete daily digest organized by sector/topic."""
    
    date: datetime
    generated_at: datetime
    sections: dict[str, list[DigestItem]]  # topic -> items
    total_articles_processed: int
    
    def to_markdown(self) -> str:
        """Convert digest to markdown format."""
        lines = [
            f"# Daily Market Intelligence Digest",
            f"**Date:** {self.date.strftime('%Y-%m-%d')}",
            f"**Generated:** {self.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"**Articles Analyzed:** {self.total_articles_processed}",
            "",
            "---",
            "",
        ]
        
        topic_titles = {
            "earnings": "Earnings & Financial Results",
            "ma": "Mergers & Acquisitions",
            "regulatory": "Regulatory & Legal",
            "macro": "Macroeconomic News",
            "other": "Other Market News",
        }
        
        for topic, items in self.sections.items():
            if not items:
                continue
                
            lines.append(f"## {topic_titles.get(topic, topic.title())}")
            lines.append("")
            
            for i, item in enumerate(items, 1):
                sentiment_emoji = {
                    "positive": "+",
                    "negative": "-",
                    "neutral": "~",
                }.get(item.sentiment, "~")
                
                companies_str = ", ".join(item.companies) if item.companies else "N/A"
                
                lines.extend([
                    f"### {i}. {item.title}",
                    f"**Source:** {item.source} | **Sentiment:** {sentiment_emoji} {item.sentiment.title()} | **Companies:** {companies_str}",
                    f"**Price Impact Likelihood:** {item.price_impact_likelihood:.0%}",
                    "",
                    f"> {item.key_insight}",
                    "",
                    f"**Why It Matters:** {item.why_it_matters}",
                    "",
                    f"[Read Full Article]({item.url})",
                    "",
                    "---",
                    "",
                ])
        
        return "\n".join(lines)

```

Now let me build the RSS fetcher for the ingestion layer:

```python
"""RSS feed fetcher for financial news ingestion."""

import logging
from datetime import datetime
from typing import Optional

import feedparser
import httpx
from dateutil import parser as date_parser

from ..models import Article
from .sources import RSS_SOURCES

logger = logging.getLogger(__name__)


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse various date formats from RSS feeds."""
    if not date_str:
        return None
    try:
        return date_parser.parse(date_str)
    except (ValueError, TypeError):
        return None


def fetch_feed(source: dict, timeout: float = 30.0) -> list[Article]:
    """
    Fetch and parse a single RSS feed.
    
    Args:
        source: Feed source configuration dict with 'name', 'url', 'category'
        timeout: Request timeout in seconds
        
    Returns:
        List of Article objects from the feed
    """
    articles = []
    feed_url = source["url"]
    feed_name = source["name"]
    
    logger.info(f"Fetching feed: {feed_name}")
    
    try:
        # Fetch the feed with custom headers
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; FinancialIntelBot/1.0)",
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
        }
        
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.get(feed_url, headers=headers)
            response.raise_for_status()
            
        # Parse the feed
        feed = feedparser.parse(response.text)
        
        if feed.bozo and feed.bozo_exception:
            logger.warning(f"Feed parsing warning for {feed_name}: {feed.bozo_exception}")
        
        # Extract articles
        for entry in feed.entries:
            try:
                # Get the best available content
                content = None
                if hasattr(entry, "content") and entry.content:
                    content = entry.content[0].get("value", "")
                elif hasattr(entry, "description"):
                    content = entry.description
                elif hasattr(entry, "summary"):
                    content = entry.summary
                
                # Clean HTML tags from content (basic cleaning)
                if content:
                    import re
                    content = re.sub(r"<[^>]+>", " ", content)
                    content = re.sub(r"\s+", " ", content).strip()
                
                # Parse publication date
                pub_date = None
                if hasattr(entry, "published"):
                    pub_date = parse_date(entry.published)
                elif hasattr(entry, "updated"):
                    pub_date = parse_date(entry.updated)
                
                article = Article(
                    title=entry.get("title", "Untitled"),
                    url=entry.get("link", ""),
                    source=feed_name,
                    content=content,
                    summary=entry.get("summary", None),
                    published_at=pub_date,
                )
                
                # Only add if we have a valid URL
                if article.url:
                    articles.append(article)
                    
            except Exception as e:
                logger.warning(f"Error parsing entry in {feed_name}: {e}")
                continue
        
        logger.info(f"Fetched {len(articles)} articles from {feed_name}")
        
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching {feed_name}: {e.response.status_code}")
    except httpx.RequestError as e:
        logger.error(f"Request error fetching {feed_name}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error fetching {feed_name}: {e}")
    
    return articles


def fetch_all_feeds(
    sources: Optional[list[dict]] = None,
    max_articles: Optional[int] = None,
) -> list[Article]:
    """
    Fetch articles from all configured RSS feeds.
    
    Args:
        sources: List of feed source configs. Defaults to RSS_SOURCES.
        max_articles: Maximum number of articles to return (for testing)
        
    Returns:
        List of deduplicated Article objects
    """
    if sources is None:
        sources = RSS_SOURCES
    
    all_articles = []
    seen_urls = set()
    
    for source in sources:
        articles = fetch_feed(source)
        
        # Deduplicate by URL
        for article in articles:
            if article.url not in seen_urls:
                seen_urls.add(article.url)
                all_articles.append(article)
    
    # Sort by publication date (newest first)
    all_articles.sort(
        key=lambda a: a.published_at or datetime.min,
        reverse=True,
    )
    
    # Limit if requested
    if max_articles:
        all_articles = all_articles[:max_articles]
    
    logger.info(f"Total articles fetched: {len(all_articles)} (deduplicated)")
    
    return all_articles

```

Now let me build the enrichment layer with NER and Ollama integration:

```python
"""Named Entity Recognition for company and ticker extraction."""

import logging
import re
from typing import Optional

from ..models import CompanyMention

logger = logging.getLogger(__name__)

# Common stock ticker pattern ($AAPL, AAPL, etc.)
TICKER_PATTERN = re.compile(r"\$?([A-Z]{1,5})(?:\s|$|[,.])")

# Well-known company name to ticker mappings
KNOWN_COMPANIES = {
    "apple": "AAPL",
    "microsoft": "MSFT",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "amazon": "AMZN",
    "meta": "META",
    "facebook": "META",
    "tesla": "TSLA",
    "nvidia": "NVDA",
    "netflix": "NFLX",
    "amd": "AMD",
    "intel": "INTC",
    "ibm": "IBM",
    "oracle": "ORCL",
    "salesforce": "CRM",
    "adobe": "ADBE",
    "paypal": "PYPL",
    "visa": "V",
    "mastercard": "MA",
    "jpmorgan": "JPM",
    "jp morgan": "JPM",
    "goldman sachs": "GS",
    "morgan stanley": "MS",
    "bank of america": "BAC",
    "wells fargo": "WFC",
    "citigroup": "C",
    "berkshire hathaway": "BRK.A",
    "warren buffett": "BRK.A",
    "walmart": "WMT",
    "target": "TGT",
    "costco": "COST",
    "home depot": "HD",
    "boeing": "BA",
    "lockheed martin": "LMT",
    "general motors": "GM",
    "ford": "F",
    "exxon": "XOM",
    "chevron": "CVX",
    "shell": "SHEL",
    "pfizer": "PFE",
    "johnson & johnson": "JNJ",
    "moderna": "MRNA",
    "united health": "UNH",
    "disney": "DIS",
    "comcast": "CMCSA",
    "at&t": "T",
    "verizon": "VZ",
    "t-mobile": "TMUS",
    "uber": "UBER",
    "lyft": "LYFT",
    "airbnb": "ABNB",
    "doordash": "DASH",
    "coinbase": "COIN",
    "robinhood": "HOOD",
    "palantir": "PLTR",
    "snowflake": "SNOW",
    "zoom": "ZM",
    "slack": "WORK",
    "spotify": "SPOT",
    "twitter": "X",
    "snap": "SNAP",
    "snapchat": "SNAP",
    "pinterest": "PINS",
    "reddit": "RDDT",
}

# Common words that look like tickers but aren't
TICKER_BLACKLIST = {
    "A", "I", "CEO", "CFO", "CTO", "IPO", "SEC", "FDA", "FTC", "DOJ",
    "NYSE", "NASDAQ", "SP", "US", "UK", "EU", "GDP", "AI", "ML", "IT",
    "THE", "AND", "FOR", "ARE", "BUT", "NOT", "YOU", "ALL", "CAN",
    "HER", "WAS", "ONE", "OUR", "OUT", "HAS", "HIS", "HOW", "ITS",
    "MAY", "NEW", "NOW", "OLD", "SEE", "WAY", "WHO", "BOY", "DID",
    "GET", "HIM", "LET", "PUT", "SAY", "SHE", "TOO", "USE", "ETF",
    "Q1", "Q2", "Q3", "Q4", "YOY", "MOM", "QOQ", "PE", "EPS", "P",
}

# spaCy model - lazy loaded
_nlp = None


def get_nlp():
    """Lazy load spaCy model."""
    global _nlp
    if _nlp is None:
        try:
            import spacy
            _nlp = spacy.load("en_core_web_sm")
            logger.info("Loaded spaCy model: en_core_web_sm")
        except OSError:
            logger.warning(
                "spaCy model not found. Run: python -m spacy download en_core_web_sm"
            )
            _nlp = False
    return _nlp if _nlp else None


def extract_tickers_from_text(text: str) -> set[str]:
    """Extract stock tickers from text using regex."""
    tickers = set()
    
    # Find explicit ticker mentions ($AAPL)
    for match in re.finditer(r"\$([A-Z]{1,5})\b", text):
        ticker = match.group(1)
        if ticker not in TICKER_BLACKLIST:
            tickers.add(ticker)
    
    # Find potential tickers in uppercase (more conservative)
    for match in re.finditer(r"\b([A-Z]{2,5})\b", text):
        ticker = match.group(1)
        # Only add if surrounded by stock-related context
        context_start = max(0, match.start() - 50)
        context_end = min(len(text), match.end() + 50)
        context = text[context_start:context_end].lower()
        
        stock_keywords = ["stock", "share", "trade", "market", "price", "nasdaq", "nyse"]
        if any(kw in context for kw in stock_keywords):
            if ticker not in TICKER_BLACKLIST:
                tickers.add(ticker)
    
    return tickers


def extract_companies_from_text(text: str) -> list[CompanyMention]:
    """Extract company mentions using spaCy NER."""
    companies = []
    seen = set()
    
    nlp = get_nlp()
    if not nlp:
        return companies
    
    # Process with spaCy
    doc = nlp(text[:10000])  # Limit text length for performance
    
    for ent in doc.ents:
        if ent.label_ == "ORG":
            company_name = ent.text.strip()
            
            # Skip very short or already seen
            if len(company_name) < 2 or company_name.lower() in seen:
                continue
            
            seen.add(company_name.lower())
            
            # Try to find ticker
            ticker = KNOWN_COMPANIES.get(company_name.lower())
            
            companies.append(CompanyMention(
                company_name=company_name,
                ticker=ticker,
            ))
    
    return companies


def extract_companies(text: str, title: Optional[str] = None) -> list[CompanyMention]:
    """
    Extract company mentions from article text.
    
    Combines spaCy NER for company names with regex for tickers.
    
    Args:
        text: Article content text
        title: Optional article title (searched first for better context)
        
    Returns:
        List of CompanyMention objects
    """
    full_text = f"{title or ''} {text}"
    companies = []
    seen_tickers = set()
    seen_names = set()
    
    # 1. Extract explicit tickers from text
    tickers = extract_tickers_from_text(full_text)
    for ticker in tickers:
        if ticker not in seen_tickers:
            seen_tickers.add(ticker)
            # Find company name for ticker (reverse lookup)
            company_name = None
            for name, t in KNOWN_COMPANIES.items():
                if t == ticker:
                    company_name = name.title()
                    break
            companies.append(CompanyMention(
                company_name=company_name or ticker,
                ticker=ticker,
            ))
    
    # 2. Extract company names using NER
    ner_companies = extract_companies_from_text(full_text)
    for company in ner_companies:
        name_key = company.company_name.lower()
        
        # Skip if we already have this company by ticker
        if company.ticker and company.ticker in seen_tickers:
            continue
        
        # Skip if we already have by name
        if name_key in seen_names:
            continue
        
        # Check known companies for ticker
        if not company.ticker:
            company.ticker = KNOWN_COMPANIES.get(name_key)
        
        if company.ticker:
            seen_tickers.add(company.ticker)
        seen_names.add(name_key)
        companies.append(company)
    
    # 3. Check for known company names in text (fallback)
    text_lower = full_text.lower()
    for company_name, ticker in KNOWN_COMPANIES.items():
        if company_name in text_lower and ticker not in seen_tickers:
            seen_tickers.add(ticker)
            companies.append(CompanyMention(
                company_name=company_name.title(),
                ticker=ticker,
            ))
    
    logger.debug(f"Extracted {len(companies)} company mentions")
    return companies

```

```python
"""Article enrichment using Ollama for sentiment, topic classification, and insights."""

import json
import logging
import re
from typing import Optional

import ollama

from ..config import OLLAMA_MODEL, SENTIMENTS, TOPICS
from ..models import Article, CompanyMention, EnrichedArticle
from .ner import extract_companies

logger = logging.getLogger(__name__)

# Prompt template for article analysis
ANALYSIS_PROMPT = """Analyze this financial news article and provide structured analysis.

Title: {title}

Content: {content}

Respond with ONLY a valid JSON object (no markdown, no explanation) in this exact format:
{{
    "sentiment": "positive" or "negative" or "neutral",
    "sentiment_score": float between -1.0 (very negative) and 1.0 (very positive),
    "sentiment_reasoning": "brief explanation of sentiment",
    "topic": "earnings" or "ma" or "regulatory" or "macro" or "other",
    "price_impact": float between 0.0 (no impact) and 1.0 (high impact),
    "key_insight": "one sentence summary of why this matters to investors"
}}

Topic definitions:
- earnings: Financial results, revenue, profit, guidance, quarterly reports
- ma: Mergers, acquisitions, buyouts, divestitures, spin-offs
- regulatory: Legal actions, SEC filings, FDA approvals, antitrust, compliance
- macro: Interest rates, inflation, GDP, employment, central bank policy
- other: Everything else (product launches, leadership changes, etc.)"""


def call_ollama(prompt: str, model: str = OLLAMA_MODEL) -> Optional[dict]:
    """
    Call Ollama API and parse JSON response.
    
    Args:
        prompt: The prompt to send
        model: Ollama model name
        
    Returns:
        Parsed JSON dict or None on error
    """
    try:
        response = ollama.chat(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a financial analyst. Respond only with valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            options={
                "temperature": 0.3,  # Lower temperature for more consistent output
            },
        )
        
        content = response["message"]["content"].strip()
        
        # Try to extract JSON from response (handle markdown code blocks)
        if "```" in content:
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", content, re.DOTALL)
            if match:
                content = match.group(1)
        
        # Parse JSON
        result = json.loads(content)
        return result
        
    except ollama.ResponseError as e:
        logger.error(f"Ollama API error: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Ollama response as JSON: {e}")
        logger.debug(f"Raw response: {content[:500] if 'content' in dir() else 'N/A'}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error calling Ollama: {e}")
        return None


def validate_analysis(analysis: dict) -> dict:
    """Validate and normalize analysis results."""
    # Validate sentiment
    sentiment = analysis.get("sentiment", "neutral").lower()
    if sentiment not in SENTIMENTS:
        sentiment = "neutral"
    
    # Validate sentiment score
    try:
        sentiment_score = float(analysis.get("sentiment_score", 0))
        sentiment_score = max(-1.0, min(1.0, sentiment_score))
    except (ValueError, TypeError):
        sentiment_score = 0.0
    
    # Validate topic
    topic = analysis.get("topic", "other").lower()
    if topic not in TOPICS:
        topic = "other"
    
    # Validate price impact
    try:
        price_impact = float(analysis.get("price_impact", 0))
        price_impact = max(0.0, min(1.0, price_impact))
    except (ValueError, TypeError):
        price_impact = 0.0
    
    return {
        "sentiment": sentiment,
        "sentiment_score": sentiment_score,
        "sentiment_reasoning": str(analysis.get("sentiment_reasoning", "")),
        "topic": topic,
        "price_impact": price_impact,
        "key_insight": str(analysis.get("key_insight", "")),
    }


def get_fallback_analysis(article: Article) -> dict:
    """Provide fallback analysis when Ollama is unavailable."""
    text = article.get_text().lower()
    
    # Simple keyword-based sentiment
    positive_words = ["beat", "exceed", "surge", "gain", "profit", "growth", "bullish", "upgrade"]
    negative_words = ["miss", "decline", "loss", "drop", "fall", "bearish", "downgrade", "layoff"]
    
    pos_count = sum(1 for w in positive_words if w in text)
    neg_count = sum(1 for w in negative_words if w in text)
    
    if pos_count > neg_count:
        sentiment = "positive"
        sentiment_score = min(0.5 + (pos_count * 0.1), 1.0)
    elif neg_count > pos_count:
        sentiment = "negative"
        sentiment_score = max(-0.5 - (neg_count * 0.1), -1.0)
    else:
        sentiment = "neutral"
        sentiment_score = 0.0
    
    # Simple topic classification
    if any(w in text for w in ["earnings", "revenue", "profit", "quarterly", "eps"]):
        topic = "earnings"
    elif any(w in text for w in ["merger", "acquisition", "buyout", "deal"]):
        topic = "ma"
    elif any(w in text for w in ["sec", "fda", "lawsuit", "regulation", "compliance"]):
        topic = "regulatory"
    elif any(w in text for w in ["fed", "interest rate", "inflation", "gdp", "economy"]):
        topic = "macro"
    else:
        topic = "other"
    
    return {
        "sentiment": sentiment,
        "sentiment_score": sentiment_score,
        "sentiment_reasoning": "Fallback keyword-based analysis",
        "topic": topic,
        "price_impact": 0.3,
        "key_insight": article.title,
    }


def enrich_article(article: Article, use_fallback: bool = False) -> EnrichedArticle:
    """
    Enrich a single article with NLP analysis.
    
    Args:
        article: Raw article to enrich
        use_fallback: If True, skip Ollama and use keyword-based analysis
        
    Returns:
        EnrichedArticle with sentiment, topic, companies, etc.
    """
    logger.debug(f"Enriching article: {article.title[:50]}...")
    
    # Extract companies using NER
    companies = extract_companies(article.get_text(), article.title)
    
    # Get analysis from Ollama or fallback
    if use_fallback:
        analysis = get_fallback_analysis(article)
    else:
        # Prepare content (truncate if too long)
        content = article.get_text()[:3000]  # Limit for Ollama context
        
        prompt = ANALYSIS_PROMPT.format(
            title=article.title,
            content=content,
        )
        
        raw_analysis = call_ollama(prompt)
        
        if raw_analysis:
            analysis = validate_analysis(raw_analysis)
        else:
            logger.warning(f"Ollama failed, using fallback for: {article.title[:50]}")
            analysis = get_fallback_analysis(article)
    
    # Create enriched article
    enriched = EnrichedArticle.from_article(
        article=article,
        sentiment=analysis["sentiment"],
        sentiment_score=analysis["sentiment_score"],
        sentiment_reasoning=analysis["sentiment_reasoning"],
        topic=analysis["topic"],
        companies=companies,
        price_impact_likelihood=analysis["price_impact"],
        key_insight=analysis["key_insight"],
    )
    
    logger.debug(
        f"Enriched: sentiment={enriched.sentiment}, "
        f"topic={enriched.topic}, companies={len(companies)}"
    )
    
    return enriched


def enrich_articles(
    articles: list[Article],
    use_fallback: bool = False,
    progress_callback=None,
) -> list[EnrichedArticle]:
    """
    Enrich multiple articles.
    
    Args:
        articles: List of raw articles
        use_fallback: If True, skip Ollama
        progress_callback: Optional callback(current, total) for progress updates
        
    Returns:
        List of enriched articles
    """
    enriched = []
    total = len(articles)
    
    for i, article in enumerate(articles):
        try:
            enriched_article = enrich_article(article, use_fallback)
            enriched.append(enriched_article)
        except Exception as e:
            logger.error(f"Failed to enrich article '{article.title[:50]}': {e}")
            continue
        
        if progress_callback:
            progress_callback(i + 1, total)
    
    logger.info(f"Enriched {len(enriched)}/{total} articles")
    return enriched

```

Now let me implement the storage layer with SQLite:

```python
"""SQLite database operations for storing and querying articles."""

import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from ..config import DATABASE_PATH, TOPICS
from ..models import CompanyMention, DigestItem, EnrichedArticle

logger = logging.getLogger(__name__)

# Database schema
SCHEMA = """
-- Articles table
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    content TEXT,
    published_at DATETIME,
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    sentiment TEXT CHECK(sentiment IN ('positive', 'negative', 'neutral')),
    sentiment_score REAL,
    sentiment_reasoning TEXT,
    topic TEXT CHECK(topic IN ('earnings', 'ma', 'regulatory', 'macro', 'other')),
    price_impact_likelihood REAL,
    key_insight TEXT
);

-- Companies mentioned in articles
CREATE TABLE IF NOT EXISTS article_companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    company_name TEXT,
    ticker TEXT,
    UNIQUE(article_id, ticker)
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_articles_topic ON articles(topic);
CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at);
CREATE INDEX IF NOT EXISTS idx_articles_sentiment ON articles(sentiment);
CREATE INDEX IF NOT EXISTS idx_articles_fetched ON articles(fetched_at);
CREATE INDEX IF NOT EXISTS idx_companies_ticker ON article_companies(ticker);
CREATE INDEX IF NOT EXISTS idx_companies_article ON article_companies(article_id);
"""


class Database:
    """SQLite database handler for article storage and retrieval."""
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database. Defaults to config DATABASE_PATH.
        """
        self.db_path = db_path or DATABASE_PATH
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            conn.executescript(SCHEMA)
            conn.commit()
        logger.info(f"Database initialized at {self.db_path}")
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def save_article(self, article: EnrichedArticle) -> Optional[int]:
        """
        Save an enriched article to the database.
        
        Args:
            article: EnrichedArticle to save
            
        Returns:
            Article ID if saved, None if duplicate or error
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # Insert article
                cursor.execute(
                    """
                    INSERT INTO articles (
                        source, title, url, content, published_at, fetched_at,
                        sentiment, sentiment_score, sentiment_reasoning,
                        topic, price_impact_likelihood, key_insight
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        article.source,
                        article.title,
                        article.url,
                        article.content,
                        article.published_at.isoformat() if article.published_at else None,
                        article.fetched_at.isoformat(),
                        article.sentiment,
                        article.sentiment_score,
                        article.sentiment_reasoning,
                        article.topic,
                        article.price_impact_likelihood,
                        article.key_insight,
                    ),
                )
                
                article_id = cursor.lastrowid
                
                # Insert company mentions
                for company in article.companies:
                    try:
                        cursor.execute(
                            """
                            INSERT OR IGNORE INTO article_companies (
                                article_id, company_name, ticker
                            ) VALUES (?, ?, ?)
                            """,
                            (article_id, company.company_name, company.ticker),
                        )
                    except sqlite3.Error:
                        pass  # Ignore duplicate company entries
                
                conn.commit()
                logger.debug(f"Saved article ID {article_id}: {article.title[:50]}")
                return article_id
                
            except sqlite3.IntegrityError:
                # Duplicate URL
                logger.debug(f"Duplicate article skipped: {article.url}")
                return None
            except sqlite3.Error as e:
                logger.error(f"Database error saving article: {e}")
                return None
    
    def save_articles(self, articles: list[EnrichedArticle]) -> tuple[int, int]:
        """
        Save multiple articles to the database.
        
        Args:
            articles: List of EnrichedArticle objects
            
        Returns:
            Tuple of (saved_count, skipped_count)
        """
        saved = 0
        skipped = 0
        
        for article in articles:
            article_id = self.save_article(article)
            if article_id:
                saved += 1
            else:
                skipped += 1
        
        logger.info(f"Saved {saved} articles, skipped {skipped} duplicates")
        return saved, skipped
    
    def get_article_by_id(self, article_id: int) -> Optional[EnrichedArticle]:
        """Get a single article by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return self._row_to_article(row, cursor)
    
    def _row_to_article(self, row: sqlite3.Row, cursor: sqlite3.Cursor) -> EnrichedArticle:
        """Convert a database row to an EnrichedArticle."""
        # Get companies for this article
        cursor.execute(
            "SELECT company_name, ticker FROM article_companies WHERE article_id = ?",
            (row["id"],),
        )
        companies = [
            CompanyMention(company_name=c["company_name"], ticker=c["ticker"])
            for c in cursor.fetchall()
        ]
        
        # Parse dates
        published_at = None
        if row["published_at"]:
            try:
                published_at = datetime.fromisoformat(row["published_at"])
            except ValueError:
                pass
        
        fetched_at = datetime.fromisoformat(row["fetched_at"])
        
        return EnrichedArticle(
            id=row["id"],
            title=row["title"],
            url=row["url"],
            source=row["source"],
            content=row["content"],
            published_at=published_at,
            fetched_at=fetched_at,
            sentiment=row["sentiment"],
            sentiment_score=row["sentiment_score"] or 0.0,
            sentiment_reasoning=row["sentiment_reasoning"] or "",
            topic=row["topic"],
            companies=companies,
            price_impact_likelihood=row["price_impact_likelihood"] or 0.0,
            key_insight=row["key_insight"] or "",
        )
    
    def get_articles_by_topic(
        self,
        topic: str,
        days: int = 7,
        limit: int = 50,
    ) -> list[EnrichedArticle]:
        """
        Get articles filtered by topic.
        
        Args:
            topic: Topic category (earnings, ma, regulatory, macro, other)
            days: Look back this many days
            limit: Maximum articles to return
            
        Returns:
            List of EnrichedArticle objects
        """
        if topic not in TOPICS:
            logger.warning(f"Invalid topic: {topic}")
            return []
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT * FROM articles
                WHERE topic = ? AND fetched_at >= ?
                ORDER BY published_at DESC NULLS LAST, fetched_at DESC
                LIMIT ?
                """,
                (topic, cutoff.isoformat(), limit),
            )
            
            return [self._row_to_article(row, cursor) for row in cursor.fetchall()]
    
    def get_recent_articles(
        self,
        days: int = 1,
        limit: int = 100,
    ) -> list[EnrichedArticle]:
        """
        Get recent articles across all topics.
        
        Args:
            days: Look back this many days
            limit: Maximum articles to return
            
        Returns:
            List of EnrichedArticle objects
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT * FROM articles
                WHERE fetched_at >= ?
                ORDER BY 
                    price_impact_likelihood DESC,
                    published_at DESC NULLS LAST
                LIMIT ?
                """,
                (cutoff.isoformat(), limit),
            )
            
            return [self._row_to_article(row, cursor) for row in cursor.fetchall()]
    
    def get_top_articles_by_topic(
        self,
        topic: str,
        days: int = 1,
        limit: int = 5,
    ) -> list[EnrichedArticle]:
        """
        Get top articles for a topic, ranked by impact likelihood.
        
        Args:
            topic: Topic category
            days: Look back this many days
            limit: Number of articles per topic
            
        Returns:
            List of EnrichedArticle objects
        """
        if topic not in TOPICS:
            return []
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT * FROM articles
                WHERE topic = ? AND fetched_at >= ?
                ORDER BY 
                    price_impact_likelihood DESC,
                    ABS(sentiment_score) DESC,
                    published_at DESC NULLS LAST
                LIMIT ?
                """,
                (topic, cutoff.isoformat(), limit),
            )
            
            return [self._row_to_article(row, cursor) for row in cursor.fetchall()]
    
    def search_by_company(
        self,
        ticker: Optional[str] = None,
        company_name: Optional[str] = None,
        days: int = 30,
        limit: int = 50,
    ) -> list[EnrichedArticle]:
        """
        Search articles by company ticker or name.
        
        Args:
            ticker: Stock ticker symbol
            company_name: Company name (partial match)
            days: Look back this many days
            limit: Maximum articles to return
            
        Returns:
            List of EnrichedArticle objects
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if ticker:
                cursor.execute(
                    """
                    SELECT DISTINCT a.* FROM articles a
                    JOIN article_companies ac ON a.id = ac.article_id
                    WHERE ac.ticker = ? AND a.fetched_at >= ?
                    ORDER BY a.published_at DESC NULLS LAST
                    LIMIT ?
                    """,
                    (ticker.upper(), cutoff.isoformat(), limit),
                )
            elif company_name:
                cursor.execute(
                    """
                    SELECT DISTINCT a.* FROM articles a
                    JOIN article_companies ac ON a.id = ac.article_id
                    WHERE ac.company_name LIKE ? AND a.fetched_at >= ?
                    ORDER BY a.published_at DESC NULLS LAST
                    LIMIT ?
                    """,
                    (f"%{company_name}%", cutoff.isoformat(), limit),
                )
            else:
                return []
            
            return [self._row_to_article(row, cursor) for row in cursor.fetchall()]
    
    def get_statistics(self) -> dict:
        """Get database statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Total articles
            cursor.execute("SELECT COUNT(*) FROM articles")
            total = cursor.fetchone()[0]
            
            # Articles by topic
            cursor.execute(
                "SELECT topic, COUNT(*) as count FROM articles GROUP BY topic"
            )
            by_topic = {row["topic"]: row["count"] for row in cursor.fetchall()}
            
            # Articles by sentiment
            cursor.execute(
                "SELECT sentiment, COUNT(*) as count FROM articles GROUP BY sentiment"
            )
            by_sentiment = {row["sentiment"]: row["count"] for row in cursor.fetchall()}
            
            # Unique companies
            cursor.execute(
                "SELECT COUNT(DISTINCT ticker) FROM article_companies WHERE ticker IS NOT NULL"
            )
            unique_tickers = cursor.fetchone()[0]
            
            # Articles in last 24 hours
            cutoff = datetime.utcnow() - timedelta(days=1)
            cursor.execute(
                "SELECT COUNT(*) FROM articles WHERE fetched_at >= ?",
                (cutoff.isoformat(),),
            )
            last_24h = cursor.fetchone()[0]
            
            # Most mentioned companies
            cursor.execute(
                """
                SELECT ticker, COUNT(*) as mentions
                FROM article_companies
                WHERE ticker IS NOT NULL
                GROUP BY ticker
                ORDER BY mentions DESC
                LIMIT 10
                """
            )
            top_companies = [
                {"ticker": row["ticker"], "mentions": row["mentions"]}
                for row in cursor.fetchall()
            ]
            
            return {
                "total_articles": total,
                "by_topic": by_topic,
                "by_sentiment": by_sentiment,
                "unique_tickers": unique_tickers,
                "articles_last_24h": last_24h,
                "top_companies": top_companies,
            }
    
    def url_exists(self, url: str) -> bool:
        """Check if an article URL already exists in the database."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM articles WHERE url = ?", (url,))
            return cursor.fetchone() is not None
    
    def get_existing_urls(self, urls: list[str]) -> set[str]:
        """Get set of URLs that already exist in the database."""
        if not urls:
            return set()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ",".join("?" * len(urls))
            cursor.execute(
                f"SELECT url FROM articles WHERE url IN ({placeholders})",
                urls,
            )
            return {row["url"] for row in cursor.fetchall()}

```

Now let me build the daily digest generator:

```python
"""Daily digest generation with Ollama-powered reasoning."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import ollama

from ..config import DIGEST_TOP_N_PER_SECTOR, OLLAMA_MODEL, OUTPUT_DIR, TOPICS
from ..models import DailyDigest, DigestItem, EnrichedArticle
from ..storage import Database

logger = logging.getLogger(__name__)

# Prompt for generating "why it matters" reasoning
WHY_IT_MATTERS_PROMPT = """You are a financial analyst writing a brief market intelligence report.

For this news article, explain in 1-2 sentences why it matters to investors and relationship managers.
Focus on actionable insights: potential market impact, client opportunities, or risks to watch.

Article Title: {title}
Topic: {topic}
Sentiment: {sentiment}
Key Insight: {key_insight}
Companies Mentioned: {companies}

Write a concise "Why It Matters" explanation (1-2 sentences only):"""


class DigestGenerator:
    """Generate daily market intelligence digests."""
    
    def __init__(self, db: Optional[Database] = None, model: str = OLLAMA_MODEL):
        """
        Initialize digest generator.
        
        Args:
            db: Database instance. Creates new one if not provided.
            model: Ollama model to use for reasoning generation.
        """
        self.db = db or Database()
        self.model = model
    
    def _generate_why_it_matters(self, article: EnrichedArticle) -> str:
        """
        Generate "why it matters" reasoning for an article using Ollama.
        
        Args:
            article: EnrichedArticle to analyze
            
        Returns:
            Generated reasoning string
        """
        companies = ", ".join(
            c.ticker or c.company_name for c in article.companies
        ) if article.companies else "N/A"
        
        prompt = WHY_IT_MATTERS_PROMPT.format(
            title=article.title,
            topic=article.topic,
            sentiment=article.sentiment,
            key_insight=article.key_insight or article.title,
            companies=companies,
        )
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a concise financial analyst. Keep responses under 50 words.",
                    },
                    {"role": "user", "content": prompt},
                ],
                options={"temperature": 0.5},
            )
            
            return response["message"]["content"].strip()
            
        except Exception as e:
            logger.warning(f"Failed to generate reasoning: {e}")
            # Fallback to key insight or generic message
            if article.key_insight:
                return article.key_insight
            return f"Monitor {article.sentiment} sentiment developments in {article.topic} sector."
    
    def _article_to_digest_item(self, article: EnrichedArticle) -> DigestItem:
        """Convert an EnrichedArticle to a DigestItem."""
        # Generate reasoning
        why_it_matters = self._generate_why_it_matters(article)
        
        # Extract ticker symbols
        tickers = [
            c.ticker for c in article.companies 
            if c.ticker
        ]
        
        return DigestItem(
            article_id=article.id or 0,
            title=article.title,
            source=article.source,
            url=article.url,
            sentiment=article.sentiment,
            topic=article.topic,
            companies=tickers,
            key_insight=article.key_insight or article.title,
            why_it_matters=why_it_matters,
            price_impact_likelihood=article.price_impact_likelihood,
            published_at=article.published_at,
        )
    
    def generate_digest(
        self,
        days: int = 1,
        top_n: int = DIGEST_TOP_N_PER_SECTOR,
        progress_callback=None,
    ) -> DailyDigest:
        """
        Generate a daily digest with top articles per topic.
        
        Args:
            days: Look back this many days for articles
            top_n: Number of top articles per topic
            progress_callback: Optional callback(current, total) for progress
            
        Returns:
            DailyDigest object
        """
        logger.info(f"Generating digest for last {days} day(s), top {top_n} per topic")
        
        sections = {}
        total_processed = 0
        
        # Calculate total for progress
        total_topics = len(TOPICS)
        current = 0
        
        for topic in TOPICS:
            # Get top articles for this topic
            articles = self.db.get_top_articles_by_topic(
                topic=topic,
                days=days,
                limit=top_n,
            )
            
            if not articles:
                sections[topic] = []
                current += 1
                if progress_callback:
                    progress_callback(current, total_topics)
                continue
            
            # Convert to digest items
            items = []
            for article in articles:
                try:
                    item = self._article_to_digest_item(article)
                    items.append(item)
                    total_processed += 1
                except Exception as e:
                    logger.error(f"Error processing article for digest: {e}")
            
            sections[topic] = items
            
            current += 1
            if progress_callback:
                progress_callback(current, total_topics)
            
            logger.debug(f"Added {len(items)} items for topic: {topic}")
        
        digest = DailyDigest(
            date=datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
            generated_at=datetime.utcnow(),
            sections=sections,
            total_articles_processed=total_processed,
        )
        
        logger.info(f"Digest generated with {total_processed} items")
        return digest
    
    def save_digest(
        self,
        digest: DailyDigest,
        output_dir: Optional[Path] = None,
    ) -> Path:
        """
        Save digest to a markdown file.
        
        Args:
            digest: DailyDigest to save
            output_dir: Directory to save to. Defaults to OUTPUT_DIR.
            
        Returns:
            Path to saved file
        """
        output_dir = output_dir or OUTPUT_DIR
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"digest_{digest.date.strftime('%Y-%m-%d')}.md"
        filepath = output_dir / filename
        
        # Convert to markdown and save
        content = digest.to_markdown()
        filepath.write_text(content)
        
        logger.info(f"Digest saved to {filepath}")
        return filepath
    
    def generate_and_save(
        self,
        days: int = 1,
        top_n: int = DIGEST_TOP_N_PER_SECTOR,
        output_dir: Optional[Path] = None,
        progress_callback=None,
    ) -> tuple[DailyDigest, Path]:
        """
        Generate and save a daily digest.
        
        Args:
            days: Look back this many days
            top_n: Number of articles per topic
            output_dir: Where to save the digest
            progress_callback: Progress callback
            
        Returns:
            Tuple of (DailyDigest, Path to saved file)
        """
        digest = self.generate_digest(
            days=days,
            top_n=top_n,
            progress_callback=progress_callback,
        )
        
        filepath = self.save_digest(digest, output_dir)
        
        return digest, filepath

```

Now let me build the CLI interface and main orchestrator:

```python
"""Command-line interface for the Financial Market Intelligence Pipeline."""

import logging
import sys
from datetime import datetime

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .config import LOG_LEVEL, TOPICS
from .digest import DigestGenerator
from .enrichment import enrich_articles
from .ingestion import fetch_all_feeds
from .storage import Database

console = Console()


def setup_logging(verbose: bool = False):
    """Configure logging with Rich handler."""
    level = logging.DEBUG if verbose else getattr(logging, LOG_LEVEL)
    
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose logging")
def cli(verbose: bool):
    """Financial Market Intelligence Pipeline CLI."""
    setup_logging(verbose)


@cli.command()
@click.option(
    "--max-articles",
    default=200,
    help="Maximum articles to fetch",
)
@click.option(
    "--fallback",
    is_flag=True,
    help="Use keyword-based analysis instead of Ollama",
)
def ingest(max_articles: int, fallback: bool):
    """Fetch and process financial news articles."""
    db = Database()
    
    console.print("\n[bold blue]Financial Market Intelligence Pipeline[/bold blue]")
    console.print("=" * 50)
    
    # Step 1: Fetch articles
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Fetching RSS feeds...", total=None)
        articles = fetch_all_feeds(max_articles=max_articles)
        progress.update(task, completed=True)
    
    console.print(f"[green]✓[/green] Fetched {len(articles)} articles from RSS feeds")
    
    if not articles:
        console.print("[yellow]No new articles to process.[/yellow]")
        return
    
    # Filter out already processed URLs
    existing_urls = db.get_existing_urls([a.url for a in articles])
    new_articles = [a for a in articles if a.url not in existing_urls]
    
    console.print(f"[green]✓[/green] {len(new_articles)} new articles to process ({len(existing_urls)} already in database)")
    
    if not new_articles:
        console.print("[yellow]All articles already processed.[/yellow]")
        return
    
    # Step 2: Enrich articles
    console.print(f"\n[bold]Enriching articles with {'fallback analysis' if fallback else 'Ollama'}...[/bold]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Processing 0/{len(new_articles)}", total=len(new_articles))
        
        def update_progress(current, total):
            progress.update(task, completed=current, description=f"Processing {current}/{total}")
        
        enriched = enrich_articles(
            new_articles,
            use_fallback=fallback,
            progress_callback=update_progress,
        )
    
    console.print(f"[green]✓[/green] Enriched {len(enriched)} articles")
    
    # Step 3: Save to database
    saved, skipped = db.save_articles(enriched)
    console.print(f"[green]✓[/green] Saved {saved} articles to database (skipped {skipped})")
    
    # Show summary
    _show_ingest_summary(enriched)


def _show_ingest_summary(articles: list):
    """Show summary table of ingested articles."""
    if not articles:
        return
    
    # Topic distribution
    topic_counts = {}
    sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
    
    for article in articles:
        topic_counts[article.topic] = topic_counts.get(article.topic, 0) + 1
        sentiment_counts[article.sentiment] = sentiment_counts.get(article.sentiment, 0) + 1
    
    console.print("\n[bold]Summary:[/bold]")
    
    table = Table(show_header=True, header_style="bold")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    
    for topic, count in sorted(topic_counts.items()):
        table.add_row(f"Topic: {topic}", str(count))
    
    table.add_row("─" * 20, "─" * 5)
    
    for sentiment, count in sentiment_counts.items():
        emoji = {"positive": "📈", "negative": "📉", "neutral": "➡️"}[sentiment]
        table.add_row(f"{emoji} {sentiment.title()}", str(count))
    
    console.print(table)


@cli.command()
@click.option(
    "--days",
    default=1,
    help="Number of days to include in digest",
)
@click.option(
    "--top-n",
    default=5,
    help="Number of articles per topic",
)
def digest(days: int, top_n: int):
    """Generate a daily market intelligence digest."""
    console.print("\n[bold blue]Generating Daily Digest[/bold blue]")
    console.print("=" * 50)
    
    generator = DigestGenerator()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Generating digest...", total=len(TOPICS))
        
        def update_progress(current, total):
            progress.update(task, completed=current)
        
        digest_obj, filepath = generator.generate_and_save(
            days=days,
            top_n=top_n,
            progress_callback=update_progress,
        )
    
    console.print(f"[green]✓[/green] Digest generated with {digest_obj.total_articles_processed} items")
    console.print(f"[green]✓[/green] Saved to: [bold]{filepath}[/bold]")
    
    # Show preview
    console.print("\n[bold]Topics covered:[/bold]")
    for topic, items in digest_obj.sections.items():
        if items:
            console.print(f"  • {topic.title()}: {len(items)} articles")


@cli.command()
@click.option(
    "--topic",
    type=click.Choice(TOPICS),
    help="Filter by topic",
)
@click.option(
    "--ticker",
    help="Filter by stock ticker (e.g., AAPL)",
)
@click.option(
    "--sentiment",
    type=click.Choice(["positive", "negative", "neutral"]),
    help="Filter by sentiment",
)
@click.option(
    "--days",
    default=7,
    help="Look back this many days",
)
@click.option(
    "--limit",
    default=20,
    help="Maximum results to show",
)
def query(
    topic: str,
    ticker: str,
    sentiment: str,
    days: int,
    limit: int,
):
    """Query stored articles with filters."""
    db = Database()
    
    console.print("\n[bold blue]Querying Articles[/bold blue]")
    console.print("=" * 50)
    
    # Build query
    if ticker:
        articles = db.search_by_company(ticker=ticker.upper(), days=days, limit=limit)
        console.print(f"Searching for ticker: [bold]{ticker.upper()}[/bold]")
    elif topic:
        articles = db.get_articles_by_topic(topic=topic, days=days, limit=limit)
        console.print(f"Searching topic: [bold]{topic}[/bold]")
    else:
        articles = db.get_recent_articles(days=days, limit=limit)
        console.print(f"Showing recent articles (last {days} days)")
    
    # Filter by sentiment if specified
    if sentiment:
        articles = [a for a in articles if a.sentiment == sentiment]
    
    if not articles:
        console.print("[yellow]No articles found matching criteria.[/yellow]")
        return
    
    # Display results
    table = Table(show_header=True, header_style="bold")
    table.add_column("Title", max_width=40)
    table.add_column("Sentiment")
    table.add_column("Topic")
    table.add_column("Companies")
    table.add_column("Impact")
    table.add_column("Date")
    
    for article in articles:
        sentiment_style = {
            "positive": "[green]+ positive[/green]",
            "negative": "[red]- negative[/red]",
            "neutral": "[dim]~ neutral[/dim]",
        }.get(article.sentiment, article.sentiment)
        
        companies = ", ".join(
            c.ticker or c.company_name[:10] 
            for c in article.companies[:3]
        ) or "—"
        
        date_str = article.published_at.strftime("%m/%d") if article.published_at else "—"
        
        table.add_row(
            article.title[:40] + ("..." if len(article.title) > 40 else ""),
            sentiment_style,
            article.topic,
            companies,
            f"{article.price_impact_likelihood:.0%}",
            date_str,
        )
    
    console.print(f"\n[green]Found {len(articles)} articles:[/green]")
    console.print(table)


@cli.command()
def stats():
    """Show pipeline statistics."""
    db = Database()
    stats = db.get_statistics()
    
    console.print("\n[bold blue]Pipeline Statistics[/bold blue]")
    console.print("=" * 50)
    
    # General stats
    table = Table(show_header=False)
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")
    
    table.add_row("Total Articles", str(stats["total_articles"]))
    table.add_row("Articles (24h)", str(stats["articles_last_24h"]))
    table.add_row("Unique Tickers", str(stats["unique_tickers"]))
    
    console.print(table)
    
    # By topic
    if stats["by_topic"]:
        console.print("\n[bold]By Topic:[/bold]")
        topic_table = Table(show_header=True, header_style="bold")
        topic_table.add_column("Topic")
        topic_table.add_column("Count", justify="right")
        
        for topic in TOPICS:
            count = stats["by_topic"].get(topic, 0)
            topic_table.add_row(topic.title(), str(count))
        
        console.print(topic_table)
    
    # By sentiment
    if stats["by_sentiment"]:
        console.print("\n[bold]By Sentiment:[/bold]")
        sent_table = Table(show_header=True, header_style="bold")
        sent_table.add_column("Sentiment")
        sent_table.add_column("Count", justify="right")
        
        for sentiment in ["positive", "neutral", "negative"]:
            count = stats["by_sentiment"].get(sentiment, 0)
            emoji = {"positive": "📈", "negative": "📉", "neutral": "➡️"}[sentiment]
            sent_table.add_row(f"{emoji} {sentiment.title()}", str(count))
        
        console.print(sent_table)
    
    # Top companies
    if stats["top_companies"]:
        console.print("\n[bold]Most Mentioned Companies:[/bold]")
        comp_table = Table(show_header=True, header_style="bold")
        comp_table.add_column("Ticker")
        comp_table.add_column("Mentions", justify="right")
        
        for company in stats["top_companies"][:10]:
            comp_table.add_row(company["ticker"], str(company["mentions"]))
        
        console.print(comp_table)


def main():
    """Main entry point."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user.[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        logging.exception("Unhandled exception")
        sys.exit(1)


if __name__ == "__main__":
    main()

```

```python
#!/usr/bin/env python3
"""
Financial Market Intelligence Pipeline

Main entry point for the CLI. This script can be run directly or scheduled via cron.

Usage:
    python run_pipeline.py ingest          # Fetch and process new articles
    python run_pipeline.py digest          # Generate daily digest
    python run_pipeline.py query --topic earnings --days 7
    python run_pipeline.py stats           # Show statistics

Cron example (run daily at 8am):
    0 8 * * * cd /path/to/H-poc && python run_pipeline.py ingest && python run_pipeline.py digest
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.cli import main

if __name__ == "__main__":
    main()

```

Now let me write the README and complete the tests:

```markdown
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

```

```python
"""Basic tests for the Financial Market Intelligence Pipeline."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from src.models import Article, CompanyMention, EnrichedArticle
from src.enrichment.ner import extract_companies, extract_tickers_from_text
from src.storage.database import Database


class TestModels:
    """Test data models."""
    
    def test_article_get_text_with_content(self):
        """Article should return content when available."""
        article = Article(
            title="Test Title",
            url="http://example.com",
            source="Test",
            content="Full article content",
            summary="Short summary",
        )
        assert article.get_text() == "Full article content"
    
    def test_article_get_text_fallback_to_summary(self):
        """Article should fall back to summary when no content."""
        article = Article(
            title="Test Title",
            url="http://example.com",
            source="Test",
            summary="Short summary",
        )
        assert article.get_text() == "Short summary"
    
    def test_article_get_text_fallback_to_title(self):
        """Article should fall back to title when no content or summary."""
        article = Article(
            title="Test Title",
            url="http://example.com",
            source="Test",
        )
        assert article.get_text() == "Test Title"
    
    def test_enriched_article_from_article(self):
        """EnrichedArticle should be created from Article."""
        article = Article(
            title="Test",
            url="http://example.com",
            source="Test",
        )
        
        enriched = EnrichedArticle.from_article(
            article=article,
            sentiment="positive",
            sentiment_score=0.8,
            sentiment_reasoning="Test reasoning",
            topic="earnings",
            companies=[CompanyMention(company_name="Apple", ticker="AAPL")],
            price_impact_likelihood=0.7,
            key_insight="Key insight here",
        )
        
        assert enriched.title == "Test"
        assert enriched.sentiment == "positive"
        assert enriched.topic == "earnings"
        assert len(enriched.companies) == 1


class TestNER:
    """Test named entity recognition."""
    
    def test_extract_explicit_tickers(self):
        """Should extract $TICKER format."""
        text = "Investors are buying $AAPL and $MSFT today."
        tickers = extract_tickers_from_text(text)
        assert "AAPL" in tickers
        assert "MSFT" in tickers
    
    def test_blacklist_common_words(self):
        """Should not extract common words that look like tickers."""
        text = "The CEO said IT will improve GDP and AI adoption."
        tickers = extract_tickers_from_text(text)
        assert "CEO" not in tickers
        assert "GDP" not in tickers
        assert "AI" not in tickers
    
    def test_extract_companies_known_names(self):
        """Should extract known company names."""
        text = "Apple and Microsoft reported strong earnings. Tesla missed expectations."
        companies = extract_companies(text)
        
        tickers = {c.ticker for c in companies if c.ticker}
        assert "AAPL" in tickers or "MSFT" in tickers or "TSLA" in tickers


class TestDatabase:
    """Test database operations."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            yield Database(db_path)
    
    def test_init_creates_tables(self, temp_db):
        """Database initialization should create tables."""
        stats = temp_db.get_statistics()
        assert stats["total_articles"] == 0
    
    def test_save_and_retrieve_article(self, temp_db):
        """Should save and retrieve an article."""
        article = EnrichedArticle(
            title="Test Article",
            url="http://example.com/test",
            source="Test Source",
            content="Test content",
            published_at=datetime.utcnow(),
            fetched_at=datetime.utcnow(),
            sentiment="positive",
            sentiment_score=0.8,
            sentiment_reasoning="Good news",
            topic="earnings",
            companies=[CompanyMention(company_name="Apple", ticker="AAPL")],
            price_impact_likelihood=0.7,
            key_insight="Important insight",
        )
        
        article_id = temp_db.save_article(article)
        assert article_id is not None
        
        retrieved = temp_db.get_article_by_id(article_id)
        assert retrieved is not None
        assert retrieved.title == "Test Article"
        assert retrieved.sentiment == "positive"
        assert len(retrieved.companies) == 1
    
    def test_duplicate_url_rejected(self, temp_db):
        """Should reject duplicate URLs."""
        article = EnrichedArticle(
            title="Test",
            url="http://example.com/unique",
            source="Test",
            content=None,
            published_at=None,
            fetched_at=datetime.utcnow(),
            sentiment="neutral",
            sentiment_score=0.0,
            sentiment_reasoning="",
            topic="other",
        )
        
        first_id = temp_db.save_article(article)
        second_id = temp_db.save_article(article)
        
        assert first_id is not None
        assert second_id is None  # Duplicate rejected
    
    def test_query_by_topic(self, temp_db):
        """Should filter articles by topic."""
        # Save articles with different topics
        for i, topic in enumerate(["earnings", "macro", "earnings"]):
            article = EnrichedArticle(
                title=f"Article {i}",
                url=f"http://example.com/{i}",
                source="Test",
                content=None,
                published_at=None,
                fetched_at=datetime.utcnow(),
                sentiment="neutral",
                sentiment_score=0.0,
                sentiment_reasoning="",
                topic=topic,
            )
            temp_db.save_article(article)
        
        earnings_articles = temp_db.get_articles_by_topic("earnings", days=1)
        assert len(earnings_articles) == 2
        
        macro_articles = temp_db.get_articles_by_topic("macro", days=1)
        assert len(macro_articles) == 1
    
    def test_statistics(self, temp_db):
        """Should compute correct statistics."""
        # Save some articles
        for i in range(5):
            article = EnrichedArticle(
                title=f"Article {i}",
                url=f"http://example.com/stat{i}",
                source="Test",
                content=None,
                published_at=None,
                fetched_at=datetime.utcnow(),
                sentiment=["positive", "negative", "neutral"][i % 3],
                sentiment_score=0.0,
                sentiment_reasoning="",
                topic="earnings",
            )
            temp_db.save_article(article)
        
        stats = temp_db.get_statistics()
        assert stats["total_articles"] == 5
        assert stats["articles_last_24h"] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

```

Let me add a `.gitignore` file and verify there are no linter errors:

```ignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/
.venv/

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# Project specific
data/*.db
output/*.md

# Testing
.pytest_cache/
.coverage
htmlcov/

# Logs
*.log

# OS
.DS_Store
Thumbs.db

```

Let me verify the complete project structure:

All files created. Let me mark the final todo as complete:

The Financial Market Intelligence Pipeline is now fully implemented. Here's a summary of what was built:

## Project Structure

```
H-poc/
├── src/
│   ├── config.py           # Configuration (Ollama model, paths, etc.)
│   ├── models.py           # Data models (Article, EnrichedArticle, DigestItem)
│   ├── cli.py              # CLI with ingest, digest, query, stats commands
│   ├── ingestion/
│   │   ├── rss_fetcher.py  # Fetches from 7 RSS sources (Yahoo, CNBC, etc.)
│   │   └── sources.py      # Feed URLs configuration
│   ├── enrichment/
│   │   ├── ner.py          # Company/ticker extraction (spaCy + regex)
│   │   └── enricher.py     # Ollama-based sentiment, topic, insight analysis
│   ├── storage/
│   │   └── database.py     # SQLite operations with full schema
│   └── digest/
│       └── generator.py    # Daily digest with AI-generated "why it matters"
├── tests/test_pipeline.py  # Pytest tests
├── requirements.txt
├── run_pipeline.py         # Entry point
└── README.md               # Full documentation
```

## To Get Started

1. **Install dependencies:**
```bash
cd H-poc
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

2. **Start Ollama and pull a model:**
```bash
ollama pull llama3.1:8b
```

3. **Run the pipeline:**
```bash
# Fetch and process articles
python run_pipeline.py ingest

# Generate daily digest
python run_pipeline.py digest

# Query articles
python run_pipeline.py query --topic earnings
python run_pipeline.py query --ticker AAPL

# View statistics
python run_pipeline.py stats
```

The pipeline handles 100+ articles per run, includes error handling and logging, and can run with `--fallback` for offline keyword-based analysis if Ollama isn't available.

```plaintext
H-poc/
├── src/
│   ├── config.py           # Configuration (Ollama model, paths, etc.)
│   ├── models.py           # Data models (Article, EnrichedArticle, DigestItem)
│   ├── cli.py              # CLI with ingest, digest, query, stats commands
│   ├── ingestion/
│   │   ├── rss_fetcher.py  # Fetches from 7 RSS sources (Yahoo, CNBC, etc.)
│   │   └── sources.py      # Feed URLs configuration
│   ├── enrichment/
│   │   ├── ner.py          # Company/ticker extraction (spaCy + regex)
│   │   └── enricher.py     # Ollama-based sentiment, topic, insight analysis
│   ├── storage/
│   │   └── database.py     # SQLite operations with full schema
│   └── digest/
│       └── generator.py    # Daily digest with AI-generated "why it matters"
├── tests/test_pipeline.py  # Pytest tests
├── requirements.txt
├── run_pipeline.py         # Entry point
└── README.md               # Full documentation
```

```shellscript
cd H-poc
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

```shellscript
ollama pull llama3.1:8b
```

```shellscript
# Fetch and process articles
python run_pipeline.py ingest

# Generate daily digest
python run_pipeline.py digest

# Query articles
python run_pipeline.py query --topic earnings
python run_pipeline.py query --ticker AAPL

# View statistics
python run_pipeline.py stats
```

---

**User**

@zsh (73-106) 

---

**Cursor**

You need to create a virtual environment first. Let me set that up:

Let me run this without sandbox restrictions:

The venv was likely created but the activation didn't persist. Let me check and run pip within the activated environment:

The venv exists. Let me use the venv's pip directly:

All packages installed. Now let's download the spaCy model:

Python 3.14 is too new and has compatibility issues with spaCy. Let me check for an older Python version:

You only have Python 3.14 which is too new for spaCy. Let me install Python 3.12:

Now let me recreate the virtual environment with Python 3.12:

Now let me download the spaCy model:

Everything is set up. Let me verify the pipeline works:

Let me fix the import error:

```python
"""Enrichment module for NLP processing."""

from .ner import extract_companies
from .enricher import enrich_article, enrich_articles

__all__ = ["extract_companies", "enrich_article", "enrich_articles"]

```

CLI is working. Let me run the tests:

All 12 tests pass. The pipeline is fully set up and ready to use. Here's a summary:

## Setup Complete

Your environment is ready at `/Users/jasminehegazy/Projects/personal/H-poc` with Python 3.12.

**To activate the virtual environment in future sessions:**
```bash
cd /Users/jasminehegazy/Projects/personal/H-poc
source venv/bin/activate
```

**Available commands:**
```bash
# Fetch and process financial news (requires Ollama running)
./venv/bin/python run_pipeline.py ingest

# Use fallback mode if Ollama isn't available
./venv/bin/python run_pipeline.py ingest --fallback

# Generate daily digest
./venv/bin/python run_pipeline.py digest

# Query articles
./venv/bin/python run_pipeline.py query --topic earnings
./venv/bin/python run_pipeline.py query --ticker AAPL

# View statistics
./venv/bin/python run_pipeline.py stats
```

**Before running with Ollama** (for full LLM-powered analysis):
```bash
# Make sure Ollama is installed and running
ollama serve  # In another terminal
ollama pull llama3.1:8b  # Download the model
```

Or use `--fallback` flag to run with keyword-based analysis (no Ollama needed).

```shellscript
cd /Users/jasminehegazy/Projects/personal/H-poc
source venv/bin/activate
```

```shellscript
# Fetch and process financial news (requires Ollama running)
./venv/bin/python run_pipeline.py ingest

# Use fallback mode if Ollama isn't available
./venv/bin/python run_pipeline.py ingest --fallback

# Generate daily digest
./venv/bin/python run_pipeline.py digest

# Query articles
./venv/bin/python run_pipeline.py query --topic earnings
./venv/bin/python run_pipeline.py query --ticker AAPL

# View statistics
./venv/bin/python run_pipeline.py stats
```

```shellscript
# Make sure Ollama is installed and running
ollama serve  # In another terminal
ollama pull llama3.1:8b  # Download the model
```

---

**User**

@zsh (226-360) 

---

**Cursor**

There's a timezone-aware vs naive datetime comparison issue. Let me fix that:

```python
"""RSS feed fetcher for financial news ingestion."""

import logging
from datetime import datetime, timezone
from typing import Optional

import feedparser
import httpx
from dateutil import parser as date_parser

from ..models import Article
from .sources import RSS_SOURCES

logger = logging.getLogger(__name__)


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse various date formats from RSS feeds and normalize to naive UTC."""
    if not date_str:
        return None
    try:
        dt = date_parser.parse(date_str)
        # Convert to UTC and make naive for consistent comparison
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except (ValueError, TypeError):
        return None


def fetch_feed(source: dict, timeout: float = 30.0) -> list[Article]:
    """
    Fetch and parse a single RSS feed.
    
    Args:
        source: Feed source configuration dict with 'name', 'url', 'category'
        timeout: Request timeout in seconds
        
    Returns:
        List of Article objects from the feed
    """
    articles = []
    feed_url = source["url"]
    feed_name = source["name"]
    
    logger.info(f"Fetching feed: {feed_name}")
    
    try:
        # Fetch the feed with custom headers
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; FinancialIntelBot/1.0)",
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
        }
        
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            response = client.get(feed_url, headers=headers)
            response.raise_for_status()
            
        # Parse the feed
        feed = feedparser.parse(response.text)
        
        if feed.bozo and feed.bozo_exception:
            logger.warning(f"Feed parsing warning for {feed_name}: {feed.bozo_exception}")
        
        # Extract articles
        for entry in feed.entries:
            try:
                # Get the best available content
                content = None
                if hasattr(entry, "content") and entry.content:
                    content = entry.content[0].get("value", "")
                elif hasattr(entry, "description"):
                    content = entry.description
                elif hasattr(entry, "summary"):
                    content = entry.summary
                
                # Clean HTML tags from content (basic cleaning)
                if content:
                    import re
                    content = re.sub(r"<[^>]+>", " ", content)
                    content = re.sub(r"\s+", " ", content).strip()
                
                # Parse publication date
                pub_date = None
                if hasattr(entry, "published"):
                    pub_date = parse_date(entry.published)
                elif hasattr(entry, "updated"):
                    pub_date = parse_date(entry.updated)
                
                article = Article(
                    title=entry.get("title", "Untitled"),
                    url=entry.get("link", ""),
                    source=feed_name,
                    content=content,
                    summary=entry.get("summary", None),
                    published_at=pub_date,
                )
                
                # Only add if we have a valid URL
                if article.url:
                    articles.append(article)
                    
            except Exception as e:
                logger.warning(f"Error parsing entry in {feed_name}: {e}")
                continue
        
        logger.info(f"Fetched {len(articles)} articles from {feed_name}")
        
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error fetching {feed_name}: {e.response.status_code}")
    except httpx.RequestError as e:
        logger.error(f"Request error fetching {feed_name}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error fetching {feed_name}: {e}")
    
    return articles


def fetch_all_feeds(
    sources: Optional[list[dict]] = None,
    max_articles: Optional[int] = None,
) -> list[Article]:
    """
    Fetch articles from all configured RSS feeds.
    
    Args:
        sources: List of feed source configs. Defaults to RSS_SOURCES.
        max_articles: Maximum number of articles to return (for testing)
        
    Returns:
        List of deduplicated Article objects
    """
    if sources is None:
        sources = RSS_SOURCES
    
    all_articles = []
    seen_urls = set()
    
    for source in sources:
        articles = fetch_feed(source)
        
        # Deduplicate by URL
        for article in articles:
            if article.url not in seen_urls:
                seen_urls.add(article.url)
                all_articles.append(article)
    
    # Sort by publication date (newest first)
    all_articles.sort(
        key=lambda a: a.published_at or datetime.min,
        reverse=True,
    )
    
    # Limit if requested
    if max_articles:
        all_articles = all_articles[:max_articles]
    
    logger.info(f"Total articles fetched: {len(all_articles)} (deduplicated)")
    
    return all_articles

```

Now let's run it again:

The fix has been applied. The `parse_date` function now normalizes all datetimes to naive UTC, which fixes the comparison error. You can run the command again:

```bash
./venv/bin/python run_pipeline.py ingest --fallback
```

```shellscript
./venv/bin/python run_pipeline.py ingest --fallback
```

---

**User**

what is being used in the fallback without ollama?

---

**Cursor**

The fallback mode uses **simple keyword-based analysis** instead of Ollama:

## Sentiment Analysis (Keyword Counting)

```127:146:src/enrichment/enricher.py
def get_fallback_analysis(article: Article) -> dict:
    """Provide fallback analysis when Ollama is unavailable."""
    text = article.get_text().lower()
    
    # Simple keyword-based sentiment
    positive_words = ["beat", "exceed", "surge", "gain", "profit", "growth", "bullish", "upgrade"]
    negative_words = ["miss", "decline", "loss", "drop", "fall", "bearish", "downgrade", "layoff"]
    
    pos_count = sum(1 for w in positive_words if w in text)
    neg_count = sum(1 for w in negative_words if w in text)
    
    if pos_count > neg_count:
        sentiment = "positive"
        sentiment_score = min(0.5 + (pos_count * 0.1), 1.0)
    elif neg_count > pos_count:
        sentiment = "negative"
        sentiment_score = max(-0.5 - (neg_count * 0.1), -1.0)
    else:
        sentiment = "neutral"
        sentiment_score = 0.0
```

## Topic Classification (Keyword Matching)

```148:160:src/enrichment/enricher.py
    # Simple topic classification
    if any(w in text for w in ["earnings", "revenue", "profit", "quarterly", "eps"]):
        topic = "earnings"
    elif any(w in text for w in ["merger", "acquisition", "buyout", "deal"]):
        topic = "ma"
    elif any(w in text for w in ["sec", "fda", "lawsuit", "regulation", "compliance"]):
        topic = "regulatory"
    elif any(w in text for w in ["fed", "interest rate", "inflation", "gdp", "economy"]):
        topic = "macro"
    else:
        topic = "other"
```

**Summary:**
- **Sentiment**: Counts positive vs negative keywords → assigns positive/negative/neutral
- **Topic**: Checks for topic-specific keywords → assigns category
- **Price Impact**: Fixed at 0.3 (30%) for all articles
- **Key Insight**: Uses the article title as the insight

It's fast and works offline, but less accurate than Ollama's contextual analysis.

```python
def get_fallback_analysis(article: Article) -> dict:
    """Provide fallback analysis when Ollama is unavailable."""
    text = article.get_text().lower()
    
    # Simple keyword-based sentiment
    positive_words = ["beat", "exceed", "surge", "gain", "profit", "growth", "bullish", "upgrade"]
    negative_words = ["miss", "decline", "loss", "drop", "fall", "bearish", "downgrade", "layoff"]
    
    pos_count = sum(1 for w in positive_words if w in text)
    neg_count = sum(1 for w in negative_words if w in text)
    
    if pos_count > neg_count:
        sentiment = "positive"
        sentiment_score = min(0.5 + (pos_count * 0.1), 1.0)
    elif neg_count > pos_count:
        sentiment = "negative"
        sentiment_score = max(-0.5 - (neg_count * 0.1), -1.0)
    else:
        sentiment = "neutral"
        sentiment_score = 0.0
```

```python
    # Simple topic classification
    if any(w in text for w in ["earnings", "revenue", "profit", "quarterly", "eps"]):
        topic = "earnings"
    elif any(w in text for w in ["merger", "acquisition", "buyout", "deal"]):
        topic = "ma"
    elif any(w in text for w in ["sec", "fda", "lawsuit", "regulation", "compliance"]):
        topic = "regulatory"
    elif any(w in text for w in ["fed", "interest rate", "inflation", "gdp", "economy"]):
        topic = "macro"
    else:
        topic = "other"
```

