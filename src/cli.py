"""Command-line interface for the Financial Market Intelligence Pipeline."""

import logging
import sys
from datetime import datetime

import click
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .config import LOG_LEVEL, TOPICS
from .digest import DigestGenerator
from .enrichment import enrich_articles
from .ingestion import fetch_all_feeds
from .storage import Database

console = Console()


def setup_logging(verbose: bool = False):
    """Configure logging with Rich handler."""
    level = logging.DEBUG if verbose else getattr(logging, LOG_LEVEL)
    
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose logging")
def cli(verbose: bool):
    """Financial Market Intelligence Pipeline CLI."""
    setup_logging(verbose)


@cli.command()
@click.option(
    "--max-articles",
    default=200,
    help="Maximum articles to fetch",
)
@click.option(
    "--fallback",
    is_flag=True,
    help="Use keyword-based analysis instead of Ollama",
)
def ingest(max_articles: int, fallback: bool):
    """Fetch and process financial news articles."""
    db = Database()
    
    console.print("\n[bold blue]Financial Market Intelligence Pipeline[/bold blue]")
    console.print("=" * 50)
    
    # Step 1: Fetch articles
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Fetching RSS feeds...", total=None)
        articles = fetch_all_feeds(max_articles=max_articles)
        progress.update(task, completed=True)
    
    console.print(f"[green]✓[/green] Fetched {len(articles)} articles from RSS feeds")
    
    if not articles:
        console.print("[yellow]No new articles to process.[/yellow]")
        return
    
    # Filter out already processed URLs
    existing_urls = db.get_existing_urls([a.url for a in articles])
    new_articles = [a for a in articles if a.url not in existing_urls]
    
    console.print(f"[green]✓[/green] {len(new_articles)} new articles to process ({len(existing_urls)} already in database)")
    
    if not new_articles:
        console.print("[yellow]All articles already processed.[/yellow]")
        return
    
    # Step 2: Enrich articles
    console.print(f"\n[bold]Enriching articles with {'fallback analysis' if fallback else 'Ollama'}...[/bold]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Processing 0/{len(new_articles)}", total=len(new_articles))
        
        def update_progress(current, total):
            progress.update(task, completed=current, description=f"Processing {current}/{total}")
        
        enriched = enrich_articles(
            new_articles,
            use_fallback=fallback,
            progress_callback=update_progress,
        )
    
    console.print(f"[green]✓[/green] Enriched {len(enriched)} articles")
    
    # Step 3: Save to database
    saved, skipped = db.save_articles(enriched)
    console.print(f"[green]✓[/green] Saved {saved} articles to database (skipped {skipped})")
    
    # Show summary
    _show_ingest_summary(enriched)


def _show_ingest_summary(articles: list):
    """Show summary table of ingested articles."""
    if not articles:
        return
    
    # Topic distribution
    topic_counts = {}
    sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
    
    for article in articles:
        topic_counts[article.topic] = topic_counts.get(article.topic, 0) + 1
        sentiment_counts[article.sentiment] = sentiment_counts.get(article.sentiment, 0) + 1
    
    console.print("\n[bold]Summary:[/bold]")
    
    table = Table(show_header=True, header_style="bold")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    
    for topic, count in sorted(topic_counts.items()):
        table.add_row(f"Topic: {topic}", str(count))
    
    table.add_row("─" * 20, "─" * 5)
    
    for sentiment, count in sentiment_counts.items():
        emoji = {"positive": "📈", "negative": "📉", "neutral": "➡️"}[sentiment]
        table.add_row(f"{emoji} {sentiment.title()}", str(count))
    
    console.print(table)


@cli.command()
@click.option(
    "--days",
    default=1,
    help="Number of days to include in digest",
)
@click.option(
    "--top-n",
    default=5,
    help="Number of articles per topic",
)
def digest(days: int, top_n: int):
    """Generate a daily market intelligence digest."""
    console.print("\n[bold blue]Generating Daily Digest[/bold blue]")
    console.print("=" * 50)
    
    generator = DigestGenerator()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Generating digest...", total=len(TOPICS))
        
        def update_progress(current, total):
            progress.update(task, completed=current)
        
        digest_obj, filepath = generator.generate_and_save(
            days=days,
            top_n=top_n,
            progress_callback=update_progress,
        )
    
    console.print(f"[green]✓[/green] Digest generated with {digest_obj.total_articles_processed} items")
    console.print(f"[green]✓[/green] Saved to: [bold]{filepath}[/bold]")
    
    # Show preview
    console.print("\n[bold]Topics covered:[/bold]")
    for topic, items in digest_obj.sections.items():
        if items:
            console.print(f"  • {topic.title()}: {len(items)} articles")


@cli.command()
@click.option(
    "--topic",
    type=click.Choice(TOPICS),
    help="Filter by topic",
)
@click.option(
    "--ticker",
    help="Filter by stock ticker (e.g., AAPL)",
)
@click.option(
    "--sentiment",
    type=click.Choice(["positive", "negative", "neutral"]),
    help="Filter by sentiment",
)
@click.option(
    "--days",
    default=7,
    help="Look back this many days",
)
@click.option(
    "--limit",
    default=20,
    help="Maximum results to show",
)
def query(
    topic: str,
    ticker: str,
    sentiment: str,
    days: int,
    limit: int,
):
    """Query stored articles with filters."""
    db = Database()
    
    console.print("\n[bold blue]Querying Articles[/bold blue]")
    console.print("=" * 50)
    
    # Build query
    if ticker:
        articles = db.search_by_company(ticker=ticker.upper(), days=days, limit=limit)
        console.print(f"Searching for ticker: [bold]{ticker.upper()}[/bold]")
    elif topic:
        articles = db.get_articles_by_topic(topic=topic, days=days, limit=limit)
        console.print(f"Searching topic: [bold]{topic}[/bold]")
    else:
        articles = db.get_recent_articles(days=days, limit=limit)
        console.print(f"Showing recent articles (last {days} days)")
    
    # Filter by sentiment if specified
    if sentiment:
        articles = [a for a in articles if a.sentiment == sentiment]
    
    if not articles:
        console.print("[yellow]No articles found matching criteria.[/yellow]")
        return
    
    # Display results
    table = Table(show_header=True, header_style="bold")
    table.add_column("Title", max_width=40)
    table.add_column("Sentiment")
    table.add_column("Topic")
    table.add_column("Companies")
    table.add_column("Impact")
    table.add_column("Date")
    
    for article in articles:
        sentiment_style = {
            "positive": "[green]+ positive[/green]",
            "negative": "[red]- negative[/red]",
            "neutral": "[dim]~ neutral[/dim]",
        }.get(article.sentiment, article.sentiment)
        
        companies = ", ".join(
            c.ticker or c.company_name[:10] 
            for c in article.companies[:3]
        ) or "—"
        
        date_str = article.published_at.strftime("%m/%d") if article.published_at else "—"
        
        table.add_row(
            article.title[:40] + ("..." if len(article.title) > 40 else ""),
            sentiment_style,
            article.topic,
            companies,
            f"{article.price_impact_likelihood:.0%}",
            date_str,
        )
    
    console.print(f"\n[green]Found {len(articles)} articles:[/green]")
    console.print(table)


@cli.command()
def stats():
    """Show pipeline statistics."""
    db = Database()
    stats = db.get_statistics()
    
    console.print("\n[bold blue]Pipeline Statistics[/bold blue]")
    console.print("=" * 50)
    
    # General stats
    table = Table(show_header=False)
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")
    
    table.add_row("Total Articles", str(stats["total_articles"]))
    table.add_row("Articles (24h)", str(stats["articles_last_24h"]))
    table.add_row("Unique Tickers", str(stats["unique_tickers"]))
    
    console.print(table)
    
    # By topic
    if stats["by_topic"]:
        console.print("\n[bold]By Topic:[/bold]")
        topic_table = Table(show_header=True, header_style="bold")
        topic_table.add_column("Topic")
        topic_table.add_column("Count", justify="right")
        
        for topic in TOPICS:
            count = stats["by_topic"].get(topic, 0)
            topic_table.add_row(topic.title(), str(count))
        
        console.print(topic_table)
    
    # By sentiment
    if stats["by_sentiment"]:
        console.print("\n[bold]By Sentiment:[/bold]")
        sent_table = Table(show_header=True, header_style="bold")
        sent_table.add_column("Sentiment")
        sent_table.add_column("Count", justify="right")
        
        for sentiment in ["positive", "neutral", "negative"]:
            count = stats["by_sentiment"].get(sentiment, 0)
            emoji = {"positive": "📈", "negative": "📉", "neutral": "➡️"}[sentiment]
            sent_table.add_row(f"{emoji} {sentiment.title()}", str(count))
        
        console.print(sent_table)
    
    # Top companies
    if stats["top_companies"]:
        console.print("\n[bold]Most Mentioned Companies:[/bold]")
        comp_table = Table(show_header=True, header_style="bold")
        comp_table.add_column("Ticker")
        comp_table.add_column("Mentions", justify="right")
        
        for company in stats["top_companies"][:10]:
            comp_table.add_row(company["ticker"], str(company["mentions"]))
        
        console.print(comp_table)


def main():
    """Main entry point."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user.[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        logging.exception("Unhandled exception")
        sys.exit(1)


if __name__ == "__main__":
    main()
