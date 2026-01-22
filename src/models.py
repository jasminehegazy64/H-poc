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
