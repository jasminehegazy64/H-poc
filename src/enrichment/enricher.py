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
