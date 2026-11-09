import sys
import time
import logging
from typing import Optional, Literal
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from findex.index import InvertedIndex, build_index_parallel
from findex.scoring import BM25Scorer, TfIdfScorer
from findex.search import execute_search
from findex.index import open_index

app = typer.Typer(help="findex — Ranked Boolean Search Engine CLI")
console = Console()
error_console = Console(stderr=True)

def setup_logging(verbosity: int) -> None:
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG
    logging.basicConfig(level=level, format="[%(levelname)s] %(message)s", stream=sys.stderr)

@app.command()
def index(
    corpus_dir: Path = typer.Argument(..., help="Path to corpus directory"),
    out: Path = typer.Option(..., "--out", "-o", help="Output index file path"),
    positions: bool = typer.Option(False, "--positions", help="Store token positions"),
    workers: int = typer.Option(1, "--workers", "-w", help="Number of workers"),
    executor: Literal["serial", "threads", "processes"] = typer.Option("serial", "--executor", "-e", help="Executor type"),
    verbose: int = typer.Option(0, "--verbose", "-v", count=True, help="Increase verbosity level")
) -> None:
    """Build and save inverted index with parallel support."""
    setup_logging(verbose)
    if not corpus_dir.exists():
        error_console.print(f"Error: Corpus directory '{corpus_dir}' does not exist.")
        raise typer.Exit(code=1)

    t0 = time.perf_counter()
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task(description="Building index...", total=None)
        idx = build_index_parallel(str(corpus_dir), workers=workers, executor_type=executor, keep_positions=positions)

    if str(out).endswith(".json"):
        idx.save_json(str(out))
    else:
        idx.save_pickle(str(out))

    t1 = time.perf_counter()
    console.print(f"[bold green]Success:[/bold green] Index built in {t1 - t0:.4f}s using {executor} (workers={workers}) and saved to {out}")

@app.command()
def search(
    index_path: Path = typer.Argument(..., help="Path to index file"),
    query: str = typer.Argument(..., help="Boolean search query"),
    scorer_name: Literal["bm25", "tfidf"] = typer.Option("bm25", "--scorer", help="Scoring algorithm"),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Number of results"),
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON to stdout"),
    verbose: int = typer.Option(0, "--verbose", "-v", count=True, help="Increase verbosity level")
) -> None:
    """Search query in index and display ranked results."""
    setup_logging(verbose)
    if not index_path.exists():
        error_console.print(f"Error: Index file '{index_path}' not found.")
        raise typer.Exit(code=1)

    try:
        with open_index(str(index_path)) as idx:
            scorer = BM25Scorer() if scorer_name == "bm25" else TfIdfScorer()
            results = execute_search(idx, query, scorer, top_k=top_k)
    except Exception as e:
        error_console.print(f"Error executing search: {e}")
        raise typer.Exit(code=1)

    if json_output:
        import json
        out_data = [{"doc_id": r.doc_id, "score": r.score, "filename": r.filename} for r in results]
        sys.stdout.write(json.dumps(out_data, ensure_ascii=False) + "\n")
        return

    table = Table(title=f"Search Results for '{query}'")
    table.add_column("Rank", justify="right", style="cyan")
    table.add_column("Score", justify="right", style="magenta")
    table.add_column("Doc ID", justify="right", style="green")
    table.add_column("File", style="yellow")

    for i, res in enumerate(results, start=1):
        table.add_row(str(i), f"{res.score:.4f}", str(res.doc_id), res.filename)

    console.print(table)

@app.command()
def stats(
    corpus_dir: Path = typer.Argument(..., help="Path to corpus directory"),
    eager: bool = typer.Option(False, "--eager", help="Use eager mode"),
    verbose: int = typer.Option(0, "--verbose", "-v", count=True, help="Verbosity level")
) -> None:
    """Print corpus statistics."""
    setup_logging(verbose)
    console.print(f"Analysing corpus at {corpus_dir} (eager={eager})...")

if __name__ == "__main__":
    app()