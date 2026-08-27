"""CLI principal de PARKER."""

import json
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from parker.core.abi_checker import check_abi_compliance
from parker.core.report import print_abi_report

app = typer.Typer(
    name="parker",
    help="Auditor de estabilidad de ABI, visibilidad de símbolos y cabeceras C",
    add_completion=True
)
console = Console()


@app.command()
def audit(
    header: Path = typer.Argument(..., help="Archivo de cabecera C (.h) a auditar", exists=True),
    binary: Optional[Path] = typer.Option(None, "--binary", "-b", help="Biblioteca compartida (.so) o archivo objeto (.o) a contrastar", exists=True),
    json_output: bool = typer.Option(False, "--json", help="Emitir salida en formato JSON estructurado")
):
    """Audita la cabecera y contrasta los símbolos exportados por la biblioteca."""
    report = check_abi_compliance(header, binary)

    if json_output:
        print(json.dumps(report.model_dump(), indent=2, ensure_ascii=False))
    else:
        print_abi_report(report)

    if not report.passed:
        raise typer.Exit(code=1)


@app.command()
def version():
    """Muestra la versión de PARKER."""
    from parker import __version__
    console.print(f"[bold cyan]PARKER[/bold cyan] versión [green]{__version__}[/green]")


if __name__ == "__main__":
    app()
