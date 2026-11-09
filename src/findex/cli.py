from findex.crawler import crawl_site
import asyncio
import json

@app.command()
def crawl(
    start_url: str = typer.Argument(..., help="Starting URL to crawl"),
    out_jsonl: Path = typer.Option("corpus.jsonl", "--out", "-o", help="Output JSONL file path"),
    max_pages: int = typer.Option(200, "--max-pages", "-m", help="Maximum pages to collect"),
    concurrency: int = typer.Option(5, "--concurrency", "-c", help="Concurrency level")
) -> None:
    """Run async web crawler and save pages to JSONL."""
    console.print(f"[bold cyan]Starting crawler for {start_url} (max_pages={max_pages}, concurrency={concurrency})[/bold cyan]")
    
    async def run():
        with open(out_jsonl, "w", encoding="utf-8") as f:
            t0 = time.perf_counter()
            async for page in crawl_site(start_url, max_pages=max_pages, concurrency=concurrency):
                f.write(json.dumps({"doc_id": page["doc_id"], "filename": page["url"], "text": page["html"]}, ensure_ascii=False) + "\n")
                console.print(f"[{page['doc_id']}/{max_pages}] Collected: {page['url']}")
            t1 = time.perf_counter()
            console.print(f"[bold green]Crawled successfully in {t1 - t0:.2f}s. Saved to {out_jsonl}[/bold green]")

    asyncio.run(run())