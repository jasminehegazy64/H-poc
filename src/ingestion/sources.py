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
