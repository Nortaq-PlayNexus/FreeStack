"""
CLI utilities for FreeStack.
"""

from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm

console = Console()


def print_table(
    title: str,
    columns: List[str],
    rows: List[List[Any]],
    styles: Optional[List[str]] = None,
) -> None:
    """Print a formatted table."""
    table = Table(title=title, show_header=True, header_style="bold magenta")

    for i, col in enumerate(columns):
        style = styles[i] if styles and i < len(styles) else None
        table.add_column(col, style=style)

    for row in rows:
        table.add_row(*[str(cell) for cell in row])

    console.print(table)


def print_kv_pairs(data: Dict[str, Any], title: Optional[str] = None) -> None:
    """Print key-value pairs in a formatted way."""
    if title:
        console.print(f"[bold]{title}[/bold]")

    for key, value in data.items():
        console.print(f"  [cyan]{key}:[/cyan] {value}")


def confirm_action(message: str, default: bool = False) -> bool:
    """Prompt for confirmation."""
    return Confirm.ask(message, default=default)


def prompt_input(message: str, default: Optional[str] = None, password: bool = False) -> str:
    """Prompt for input."""
    return Prompt.ask(message, default=default, password=password)


def show_progress(description: str, total: Optional[int] = None):
    """Create a progress context manager."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    )


async def run_async(coro):
    """Run an async function from sync context."""
    import asyncio
    return asyncio.run(coro)