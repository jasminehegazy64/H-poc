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
