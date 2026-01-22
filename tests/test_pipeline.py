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
