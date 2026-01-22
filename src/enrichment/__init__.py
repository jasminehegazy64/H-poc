"""Enrichment module for NLP processing."""

from .ner import extract_companies
from .enricher import enrich_article, enrich_articles

__all__ = ["extract_companies", "enrich_article", "enrich_articles"]
