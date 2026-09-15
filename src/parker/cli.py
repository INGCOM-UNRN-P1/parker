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


def generar_seccion_markdown(report) -> str:
    """Genera sección de auditoría de ABI y visibilidad de símbolos para Dredd."""
    lines = [
        "<!-- dredd-section: parker v1.0.0 -->\n",
        "## Auditoría de ABI y Visibilidad de Símbolos (Parker)\n",
    ]
    lines.append(f"- **Cabecera analizada:** `{Path(report.header_file).name}`")
    if report.binary_file:
        lines.append(f"- **Binario contrastado:** `{Path(report.binary_file).name}`")
    lines.append(f"- **Símbolos declarados:** {len(report.declared_symbols)}")
    lines.append(f"- **Problemas de ABI detectados:** {len(report.issues)}\n")
    if report.passed:
        lines.append("> [!TIP]\n> **Conformidad ABI:** Todos los símbolos exportados coinciden limpiamente con las declaraciones de la cabecera sin rupturas de interfaz.\n")
    else:
        lines.append("> [!WARNING]\n> **Discrepancias de ABI:** Se detectaron símbolos faltantes, visibilidad incorrecta o divergencias de tipos.\n")
        lines.append("| Símbolo | Tipo | Severidad | Diagnóstico | Sugerencia |")
        lines.append("| :--- | :---: | :---: | :--- | :--- |")
        for iss in report.issues:
            sym_limpio = iss.symbol_name.replace("|", "&#124;")
            msg_limpio = iss.message.replace("|", "&#124;")
            sug_limpio = iss.suggestion.replace("|", "&#124;")
            lines.append(f"| `{sym_limpio}` | `{iss.issue_type}` | **{iss.severity}** | {msg_limpio} | {sug_limpio} |")
        lines.append("")
    return "\n".join(lines)


@app.command("audit")
@app.command("check")
def audit(
    header: Path = typer.Argument(..., help="Archivo de cabecera C (.h) a auditar", exists=True),
    binary: Optional[Path] = typer.Option(None, "--binary", "-b", help="Biblioteca compartida (.so) o archivo objeto (.o) a contrastar", exists=True),
    json_output: bool = typer.Option(False, "--json", help="Emitir salida en formato JSON estructurado"),
    output_md: Optional[Path] = typer.Option(None, "--md", "--output-md", help="Generar sección de reporte en formato Markdown para fusión en Dredd."),
):
    """Audita la cabecera y contrasta los símbolos exportados por la biblioteca."""
    report = check_abi_compliance(header, binary)

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
    header: Path = typer.Argument(..., help="Archivo de cabecera C (.h) a auditar", exists=True),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Ruta de destino del archivo Markdown."),
    binary: Optional[Path] = typer.Option(None, "--binary", "-b", help="Biblioteca compartida (.so) u objeto (.o)."),
):
    """Genera directamente la sección de reporte Markdown de PARKER para Dredd."""
    report = check_abi_compliance(header, binary)
    md_content = generar_seccion_markdown(report)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(md_content, encoding="utf-8")
        console.print(f"[bold green]✓ Reporte Markdown generado en:[/bold green] {output}")
    else:
        print(md_content)


@app.command()
def version():
    """Muestra la versión de PARKER."""
    from parker import __version__
    console.print(f"[bold cyan]PARKER[/bold cyan] versión [green]{__version__}[/green]")


if __name__ == "__main__":
    app()
