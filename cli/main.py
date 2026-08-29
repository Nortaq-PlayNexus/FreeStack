"""
CLI entry point for FreeStack.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..core.config import settings
from ..core.database import init_db, close_db, db_manager
from ..core.logging import setup_logging, get_logger

app = typer.Typer(
    name="freestack",
    help="FreeStack - A production-grade, modular full-stack development framework",
    add_completion=True,
    rich_markup_mode="rich",
)

console = Console()
logger = get_logger(__name__)


def version_callback(value: bool):
    """Show version and exit."""
    if value:
        console.print(f"FreeStack version 0.1.0")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", callback=version_callback, is_eager=True),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Path to config file"),
    env: Optional[str] = typer.Option(None, "--env", "-e", help="Environment (development/staging/production)"),
):
    """FreeStack CLI - Manage your FreeStack application."""
    # Load config if provided
    if config:
        os.environ["FREESTACK_CONFIG_FILE"] = str(config)

    if env:
        os.environ["FREESTACK_APP__ENVIRONMENT"] = env

    # Setup logging
    setup_logging()


# =============================================================================
# Database Commands
# =============================================================================
db_app = typer.Typer(help="Database management commands")
app.add_typer(db_app, name="db")


@db_app.command("upgrade")
def db_upgrade(
    revision: str = typer.Argument("head", help="Target revision"),
):
    """Run database migrations."""
    from alembic.config import Config
    from alembic import command

    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, revision)
    console.print(f"[green]Database upgraded to {revision}[/green]")


@db_app.command("downgrade")
def db_downgrade(
    revision: str = typer.Argument("-1", help="Target revision"),
):
    """Rollback database migrations."""
    from alembic.config import Config
    from alembic import command

    alembic_cfg = Config("alembic.ini")
    command.downgrade(alembic_cfg, revision)
    console.print(f"[green]Database downgraded to {revision}[/green]")


@db_app.command("revision")
def db_revision(
    message: str = typer.Option(..., "--message", "-m", help="Migration message"),
    autogenerate: bool = typer.Option(True, "--autogenerate/--no-autogenerate", help="Auto-generate migration"),
):
    """Create a new migration."""
    from alembic.config import Config
    from alembic import command

    alembic_cfg = Config("alembic.ini")
    command.revision(alembic_cfg, message=message, autogenerate=autogenerate)
    console.print(f"[green]Migration created: {message}[/green]")


@db_app.command("current")
def db_current():
    """Show current migration revision."""
    from alembic.config import Config
    from alembic import command

    alembic_cfg = Config("alembic.ini")
    command.current(alembic_cfg)


@db_app.command("history")
def db_history():
    """Show migration history."""
    from alembic.config import Config
    from alembic import command

    alembic_cfg = Config("alembic.ini")
    command.history(alembic_cfg)


@db_app.command("seed")
def db_seed():
    """Seed database with development data."""
    asyncio.run(_seed_db())


async def _seed_db():
    """Seed database with development data."""
    from ..models.user import User, UserStatus
    from ..core.auth import get_password_hash
    from ..core.database import db_manager

    await init_db()

    async with db_manager.session() as session:
        from ..core.database import BaseRepository
        user_repo = BaseRepository(session, User)

        # Create admin user
        admin = await user_repo.get_by(email="admin@freestack.local")
        if not admin:
            admin = await user_repo.create(
                email="admin@freestack.local",
                username="admin",
                hashed_password=get_password_hash("admin123"),
                full_name="Admin User",
                status=UserStatus.ACTIVE,
                roles=["superadmin"],
                permissions=[],
            )
            console.print(f"[green]Created admin user: {admin.email}[/green]")

        # Create test user
        test_user = await user_repo.get_by(email="user@freestack.local")
        if not test_user:
            test_user = await user_repo.create(
                email="user@freestack.local",
                username="testuser",
                hashed_password=get_password_hash("user123"),
                full_name="Test User",
                status=UserStatus.ACTIVE,
                roles=["user"],
                permissions=[],
            )
            console.print(f"[green]Created test user: {test_user.email}[/green]")

    await close_db()
    console.print("[green]Database seeded successfully[/green]")


# =============================================================================
# API Server Commands
# =============================================================================
api_app = typer.Typer(help="API server commands")
app.add_typer(api_app, name="api")


@api_app.command("serve")
def api_serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload"),
    workers: int = typer.Option(1, "--workers", "-w", help="Number of workers"),
):
    """Start the API server."""
    import uvicorn

    uvicorn.run(
        "api.main:create_app",
        host=host,
        port=port,
        reload=reload,
        workers=workers if not reload else 1,
        factory=True,
    )


@api_app.command("shell")
def api_shell():
    """Start interactive shell with app context."""
    import IPython
    from ..core.database import init_db

    asyncio.run(init_db())

    console.print("[green]FreeStack shell ready. App context loaded.[/green]")
    IPython.embed()


# =============================================================================
# Worker Commands
# =============================================================================
worker_app = typer.Typer(help="Background worker commands")
app.add_typer(worker_app, name="worker")


@worker_app.command("start")
def worker_start(
    concurrency: int = typer.Option(4, "--concurrency", "-c", help="Number of concurrent jobs"),
    queues: str = typer.Option("default,high,low", "--queues", "-q", help="Comma-separated queue names"),
):
    """Start the background worker."""
    from ..services.worker import run_worker

    queue_list = [q.strip() for q in queues.split(",")]
    asyncio.run(run_worker(concurrency=concurrency, queues=queue_list))


@worker_app.command("monitor")
def worker_monitor():
    """Monitor worker queue statistics."""
    from ..services.worker import monitor_queues

    asyncio.run(monitor_queues())


# =============================================================================
# Scheduler Commands
# =============================================================================
scheduler_app = typer.Typer(help="Task scheduler commands")
app.add_typer(scheduler_app, name="scheduler")


@scheduler_app.command("start")
def scheduler_start():
    """Start the task scheduler."""
    from ..services.scheduler import run_scheduler

    asyncio.run(run_scheduler())


# =============================================================================
# WebSocket Commands
# =============================================================================
ws_app = typer.Typer(help="WebSocket server commands")
app.add_typer(ws_app, name="ws")


@ws_app.command("serve")
def ws_serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind"),
    port: int = typer.Option(8001, "--port", "-p", help="Port to bind"),
):
    """Start the WebSocket server."""
    from ..services.websocket import run_websocket_server

    asyncio.run(run_websocket_server(host=host, port=port))


# =============================================================================
# Utility Commands
# =============================================================================
util_app = typer.Typer(help="Utility commands")
app.add_typer(util_app, name="generate")


@util_app.command("secret")
def generate_secret(
    length: int = typer.Option(32, "--length", "-l", help="Key length in bytes"),
):
    """Generate a secure secret key."""
    import secrets
    key = secrets.token_hex(length)
    console.print(f"[green]{key}[/green]")


@util_app.command("openapi")
def generate_openapi(
    output: Path = typer.Option("openapi.json", "--output", "-o", help="Output file"),
):
    """Generate OpenAPI specification."""
    import json
    from ..api.main import create_app

    app_instance = create_app()
    openapi_spec = app_instance.openapi()

    output.write_text(json.dumps(openapi_spec, indent=2))
    console.print(f"[green]OpenAPI spec written to {output}[/green]")


# =============================================================================
# Shell Command
# =============================================================================
@app.command()
def shell():
    """Start Python shell with app context."""
    import IPython
    from ..core.database import init_db

    asyncio.run(init_db())

    console.print("[green]FreeStack shell ready. App context loaded.[/green]")
    IPython.embed()


if __name__ == "__main__":
    app()