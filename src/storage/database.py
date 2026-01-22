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
