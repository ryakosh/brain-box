from typing import Annotated, Optional

import typer
import uvicorn

from brain_box.config import settings

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
        "brain_box.main:app",
        host=final_host,
        port=final_port,
        ssl_certfile=settings.general.cert,
        ssl_keyfile=settings.general.cert_key,
    )


if __name__ == "__main__":
    app()
