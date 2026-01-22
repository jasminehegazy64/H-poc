"""Data ingestion module."""

from .rss_fetcher import fetch_all_feeds, fetch_feed
from .sources import RSS_SOURCES

__all__ = ["fetch_all_feeds", "fetch_feed", "RSS_SOURCES"]
