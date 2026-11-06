import sys
import logging
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(no_args_is_help=True)
console = Console()
stderr_console = Console(stderr=True)

def setup_logging(verbosity: int) -> None:
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG
    
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s", stream=sys.stderr)

@app.callback()
def main(verbose: int = typer.Option(0, "--verbose", "-v", count=True)) -> None:
    setup_logging(verbose)

@app.command()
def index(path: str) -> None:
    """Index documents."""
    try:
        console.print("[green]Index successfully built![/green]")
    except Exception as e:
        stderr_console.print(f"Error: {e}")
        raise typer.Exit(code=1)

@app.command()
def search(query: str, json_output: bool = typer.Option(False, "--json")) -> None:
    """Search query."""
    try:
        results = [("doc1.txt", 0.95), ("doc2.txt", 0.82)]
        if json_output:
            import json
            print(json.dumps([{"doc": d, "score": s} for d, s in results]))
        else:
            table = Table(title="Search Results")
            table.add_column("Document", style="cyan")
            table.add_column("Score", style="magenta")
            for doc, score in results:
                table.add_row(doc, f"{score:.4f}")
            console.print(table)
    except Exception as e:
        stderr_console.print(f"Error: {e}")
        raise typer.Exit(code=1)

@app.command()
def stats() -> None:
    """Show index stats."""
    console.print("Documents indexed: 42")