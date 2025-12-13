import sys
import subprocess
from typing import Annotated, Optional
from pathlib import Path

import typer
import uvicorn

from brain_box.security import get_password_hash
from brain_box.config import settings, _xdg_config_home
from brain_box.main import app as main_app

SYSTEMD_USER_PATH = Path(_xdg_config_home) / "systemd" / "user" / "brain_box.service"
SERVICE_TEMPLATE = """
[Unit]
Description=Brain Box Daemon
After=network.target

[Service]
ExecStart={exec_cmd} start
Restart=on-failure
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=default.target
"""

app = typer.Typer()


@app.command()
def start(
    host: Annotated[
        Optional[str],
        typer.Option(help="Host to bind."),
    ] = None,
    port: Annotated[
        Optional[int],
        typer.Option(help="Port to bind."),
    ] = None,
) -> None:
    """Starts the Brain Box web server."""

    final_host = host or settings.general.host
    final_port = port or settings.general.port

    uvicorn.run(
        main_app,
        host=final_host,
        port=final_port,
        ssl_certfile=settings.general.cert,
        ssl_keyfile=settings.general.cert_key,
    )


@app.command()
def install_service(
    force: Annotated[
        bool, typer.Option("--force", "-f", help="Overwrite existing service file.")
    ] = False,
):
    """Installs Brain Box as a user-level systemd service."""

    if getattr(sys, "frozen", False) or "__compiled__" in globals():
        # Running as a compiled binary
        exec_cmd = sys.executable
    else:
        # Running as a script
        exec_cmd = f"{sys.executable} -m brain_box.cli"

    service_content = SERVICE_TEMPLATE.format(exec_cmd=exec_cmd)

    if SYSTEMD_USER_PATH.exists() and not force:
        typer.secho(
            f"⚠️  Service file exists: {SYSTEMD_USER_PATH}", fg=typer.colors.YELLOW
        )
        raise typer.Exit(code=1)

    SYSTEMD_USER_PATH.parent.mkdir(parents=True, exist_ok=True)
    SYSTEMD_USER_PATH.write_text(service_content, encoding="utf-8")

    typer.secho(
        f"✅ Generated service file at: {SYSTEMD_USER_PATH}", fg=typer.colors.GREEN
    )

    try:
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
        subprocess.run(
            ["systemctl", "--user", "enable", "--now", SYSTEMD_USER_PATH], check=True
        )
        typer.secho("🎉 Brain Box service started!", fg=typer.colors.CYAN)
    except subprocess.CalledProcessError:
        typer.secho("❌ Failed to interact with systemctl.", fg=typer.colors.RED)
        raise typer.Exit(code=1)


@app.command()
def hash_password():
    """Generates a secure password hash."""

    password = typer.prompt("Enter password", hide_input=True)

    if not password.strip():
        typer.secho(
            "❌ Error: Password cannot be empty.", fg=typer.colors.RED, bold=True
        )

        raise typer.Exit(code=1)

    hashed_password = get_password_hash(password)

    typer.secho(
        "\n✅ Password hash generated successfully!", fg=typer.colors.GREEN, bold=True
    )
    typer.echo("To enable password protection, add this to your config file:")

    typer.secho("[security]", fg=typer.colors.YELLOW)
    typer.secho(f'hashed_password = "{hashed_password}"', fg=typer.colors.YELLOW)

    typer.echo("\nAfter saving the file, restart the service to apply changes:")
    typer.secho("  systemctl --user restart brain_box.service", fg=typer.colors.CYAN)


if __name__ == "__main__":
    app()
