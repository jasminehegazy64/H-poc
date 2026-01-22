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
