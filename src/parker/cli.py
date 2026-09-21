"""CLI principal de PARKER."""

import json
from pathlib import Path
from typing import List, Optional
import typer
from rich.console import Console
from rich.table import Table
from parker.core.abi_checker import auditar_abi, check_abi_project
from parker.core.report import print_abi_report

app = typer.Typer(
    name="parker",
    help="Auditor de estabilidad de ABI, visibilidad de símbolos y cabeceras C",
    add_completion=True
)
console = Console()
err_console = Console(stderr=True)


def _version_callback(value: bool) -> None:
    if value:
        from parker import __version__
        console.print(f"[bold cyan]PARKER[/bold cyan] versión [green]{__version__}[/green]")
        raise typer.Exit(code=0)


@app.callback()
def main_callback(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", help="Muestra la versión de PARKER.",
        callback=_version_callback, is_eager=True,
    ),
) -> None:
    pass


def generar_seccion_markdown(report) -> str:
    """Genera sección de auditoría de ABI y visibilidad de símbolos para Dredd."""
    lines = [
        "<!-- dredd-section: parker v1.0.0 -->\n",
        "## Auditoría de ABI y Visibilidad de Símbolos (Parker)\n",
    ]
    if len(report.headers) == 1:
        lines.append(f"- **Cabecera analizada:** `{report.headers[0]}`")
    else:
        lines.append(f"- **Cabeceras analizadas:** {len(report.headers)}")
    if report.binaries:
        lines.append(f"- **Binarios contrastados:** {', '.join(f'`{b}`' for b in report.binaries)}")
    lines.append(f"- **Símbolos declarados:** {report.total_declarations_in_header}")
    lines.append(f"- **Problemas de ABI detectados:** {len(report.issues)}\n")
    if not report.issues:
        lines.append("> [!TIP]\n> **Conformidad ABI:** Todos los símbolos exportados coinciden limpiamente con las declaraciones de la cabecera sin rupturas de interfaz.\n")
    else:
        if report.passed:
            lines.append("> [!NOTE]\n> **Advertencias de ABI:** no hay discrepancias críticas, pero hay puntos a revisar.\n")
        else:
            lines.append("> [!WARNING]\n> **Discrepancias de ABI:** Se detectaron símbolos faltantes, visibilidad incorrecta o divergencias de tipos.\n")
        lines.append("| Símbolo | Tipo | Severidad | Diagnóstico | Sugerencia |")
        lines.append("| :--- | :---: | :---: | :--- | :--- |")
        for iss in report.issues:
            sym_limpio = iss.symbol_name.replace("|", "&#124;")
            msg_limpio = iss.message.replace("|", "&#124;")
            sug_limpio = iss.suggestion.replace("|", "&#124;")
            lines.append(f"| `{sym_limpio}` | `{iss.code}` | **{iss.severity}** | {msg_limpio} | {sug_limpio} |")
        lines.append("")
    return "\n".join(lines)


def _auditar(destino: Path, binarios: Optional[List[Path]]):
    """Un archivo se toma como cabecera; un directorio como proyecto (cabeceras y binarios descubiertos)."""
    if destino.is_dir():
        report = check_abi_project(destino, binarios)
        if not report.headers:
            err_console.print(f"[bold red]Error:[/bold red] no hay cabeceras .h en {destino}.")
            raise typer.Exit(code=2)
        return report
    if destino.suffix != ".h":
        err_console.print(
            f"[bold red]Error:[/bold red] {destino.name} no es una cabecera .h ni un directorio."
        )
        raise typer.Exit(code=2)
    return auditar_abi([destino], binarios or [])


@app.command("audit")
@app.command("check")
def audit(
    header: Path = typer.Argument(..., help="Cabecera C (.h) o directorio de proyecto (cabeceras y .so/.o descubiertos)", exists=True),
    binary: Optional[List[Path]] = typer.Option(None, "--binary", "-b", help="Biblioteca compartida (.so) u objeto (.o) a contrastar; se puede repetir", exists=True),
    json_output: bool = typer.Option(False, "--json", help="Emitir salida en formato JSON estructurado"),
    output_md: Optional[Path] = typer.Option(None, "--md", "--output-md", help="Generar sección de reporte en formato Markdown para fusión en Dredd."),
):
    """Audita la cabecera (o todas las de un directorio) y contrasta los símbolos exportados por los binarios."""
    report = _auditar(header, binary)

    if output_md:
        md_text = generar_seccion_markdown(report)
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(md_text, encoding="utf-8")
        console.print(f"[bold green]✓ Sección Markdown generada en:[/bold green] {output_md}")
        raise typer.Exit(code=0 if report.passed else 1)

    if json_output:
        print(json.dumps(report.model_dump(), indent=2, ensure_ascii=False))
    else:
        print_abi_report(report)

    if not report.passed:
        raise typer.Exit(code=1)


@app.command("report")
def report_cmd(
    header: Path = typer.Argument(..., help="Cabecera C (.h) o directorio de proyecto", exists=True),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Ruta de destino del archivo Markdown."),
    binary: Optional[List[Path]] = typer.Option(None, "--binary", "-b", help="Biblioteca compartida (.so) u objeto (.o); se puede repetir.", exists=True),
):
    """Genera directamente la sección de reporte Markdown de PARKER para Dredd."""
    report = _auditar(header, binary)
    md_content = generar_seccion_markdown(report)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(md_content, encoding="utf-8")
        console.print(f"[bold green]✓ Reporte Markdown generado en:[/bold green] {output}")
    else:
        print(md_content)
    if not report.passed:
        raise typer.Exit(code=1)


@app.command("doctor")
def doctor_cmd(
    json_output: bool = typer.Option(False, "--json", help="Emitir diagnóstico en formato JSON estructurado."),
) -> None:
    """Verifica el estado del entorno de auditoría ABI PARKER (Python, nm, GCC)."""
    import shutil
    import sys
    diagnostico = []

    py_ok = sys.version_info >= (3, 10)
    diagnostico.append({
        "componente": "Python Runtime",
        "estado": "OK" if py_ok else "ERROR",
        "requerido": True,
        "detalle": f"Python {sys.version.split()[0]}",
    })

    nm_path = shutil.which("nm")
    diagnostico.append({
        "componente": "Herramienta nm (binutils)",
        "estado": "OK" if nm_path else "ADVERTENCIA",
        "requerido": False,
        "detalle": nm_path or "No encontrado (requerido para inspección de símbolos en .so / .o)",
    })

    gcc_path = shutil.which("gcc")
    diagnostico.append({
        "componente": "Compilador GCC",
        "estado": "OK" if gcc_path else "ADVERTENCIA",
        "requerido": False,
        "detalle": gcc_path or "No encontrado (opcional)",
    })

    todo_ok = py_ok

    if json_output:
        payload = {
            "schema_version": "1.0.0",
            "herramienta": "parker",
            "ok": todo_ok,
            "componentes": diagnostico,
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        raise typer.Exit(code=0 if todo_ok else 1)

    tabla = Table(title="🏥 Diagnóstico del Entorno PARKER (doctor)", border_style="cyan")
    tabla.add_column("Componente", style="bold white")
    tabla.add_column("Estado", justify="center")
    tabla.add_column("Detalle")

    for c in diagnostico:
        color = "bold green" if c["estado"] == "OK" else ("bold yellow" if c["estado"] == "ADVERTENCIA" else "bold red")
        simbolo = "✓" if c["estado"] == "OK" else ("⚠️" if c["estado"] == "ADVERTENCIA" else "✗")
        tabla.add_row(c["componente"], f"[{color}]{simbolo} {c['estado']}[/{color}]", c["detalle"])

    console.print(tabla)
    if not todo_ok:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
