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
