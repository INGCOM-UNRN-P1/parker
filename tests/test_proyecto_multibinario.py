"""Regresión de PARKER-D0303 y PARKER-D0902.

D0303: con varios binarios el plugin contrastaba solo `binaries[0]` contra todas
       las cabeceras (PRK003 falsos) y el glob no recursivo perdía subdirectorios.
D0902: `audit` exigía UNA cabecera; ripley le pasaba el directorio del proyecto
       (IsADirectoryError) y el binario como argumento posicional (error de uso).
Además `audit --md` y `report` fallaban con AttributeError (`header_file`).
"""

import json
import shutil
import subprocess

import pytest
from typer.testing import CliRunner

from parker.cli import app
from parker.core.abi_checker import auditar_abi, check_abi_project, descubrir_artefactos
from parker.plugins.ripley_plugin import ParkerPlugin

runner = CliRunner()

necesita_toolchain = pytest.mark.skipif(
    not (shutil.which("gcc") and shutil.which("nm")), reason="requiere gcc y nm"
)

CABECERA_A = "int suma(int a, int b);\n"
CABECERA_B = "int resta(int a, int b);\n"


def _objeto(dirpath, nombre, codigo):
    fuente = dirpath / f"{nombre}.c"
    fuente.write_text(codigo, encoding="utf-8")
    objeto = dirpath / f"{nombre}.o"
    subprocess.run(["gcc", "-c", str(fuente), "-o", str(objeto)], check=True)
    fuente.unlink()
    return objeto


@pytest.fixture
def proyecto(tmp_path):
    """Dos cabeceras y dos objetos: cada función vive en un binario distinto."""
    (tmp_path / "a.h").write_text(CABECERA_A, encoding="utf-8")
    sub = tmp_path / "src"
    sub.mkdir()
    (sub / "b.h").write_text(CABECERA_B, encoding="utf-8")
    _objeto(tmp_path, "a", "int suma(int a, int b) { return a + b; }\n")
    _objeto(sub, "b", "int resta(int a, int b) { return a - b; }\n")
    return tmp_path


def test_el_descubrimiento_es_recursivo_e_ignora_directorios_ocultos(tmp_path):
    (tmp_path / "x.h").write_text("int x(void);", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "y.h").write_text("int y(void);", encoding="utf-8")
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "ajena.h").write_text("int ajena(void);", encoding="utf-8")
    cabeceras, _ = descubrir_artefactos(tmp_path)
    assert [c.name for c in cabeceras] == ["x.h", "y.h"]


@necesita_toolchain
def test_una_funcion_en_el_segundo_binario_no_se_acusa_de_faltante(proyecto):
    reporte = check_abi_project(proyecto)
    assert [i.code for i in reporte.issues] == []
    assert reporte.passed is True
    assert sorted(reporte.binaries) == ["a.o", "src/b.o"]


@necesita_toolchain
def test_contrastar_contra_un_solo_binario_si_acusa_lo_que_falta(proyecto):
    """Es lo que hacía el plugin: el mismo proyecto daba un falso PRK003."""
    reporte = auditar_abi([proyecto / "a.h", proyecto / "src" / "b.h"], [proyecto / "a.o"])
    assert [(i.code, i.symbol_name) for i in reporte.issues if i.code == "PRK003"] == [("PRK003", "resta")]


@necesita_toolchain
def test_una_funcion_ausente_de_todos_los_binarios_sigue_siendo_un_error(proyecto):
    (proyecto / "c.h").write_text("int nunca_implementada(void);\n", encoding="utf-8")
    reporte = check_abi_project(proyecto)
    assert [(i.code, i.symbol_name) for i in reporte.issues] == [("PRK003", "nunca_implementada")]
    assert reporte.passed is False


@necesita_toolchain
def test_un_simbolo_declarado_en_otra_cabecera_no_es_una_fuga(proyecto):
    """`resta` no está en a.h pero sí en b.h: no es PRK002."""
    reporte = check_abi_project(proyecto)
    assert not any(i.code == "PRK002" for i in reporte.issues)


@necesita_toolchain
def test_un_simbolo_exportado_sin_ninguna_cabecera_es_una_fuga(proyecto):
    _objeto(proyecto, "extra", "int oculta(void) { return 1; }\n")
    reporte = check_abi_project(proyecto)
    assert [(i.code, i.symbol_name) for i in reporte.issues] == [("PRK002", "oculta")]


@necesita_toolchain
def test_un_binario_ilegible_no_permite_afirmar_que_falte_una_funcion(proyecto):
    (proyecto / "roto.o").write_text("no es ELF\n", encoding="utf-8")
    codigos = [i.code for i in check_abi_project(proyecto).issues]
    assert codigos == ["PRK000"]


@necesita_toolchain
def test_el_plugin_ve_los_binarios_de_subdirectorios(proyecto):
    resultado = ParkerPlugin().run({"source_dir": str(proyecto)})
    assert resultado["passed"] is True
    assert resultado["issues_count"] == 0


@necesita_toolchain
def test_el_cli_acepta_un_directorio(proyecto):
    res = runner.invoke(app, ["audit", str(proyecto), "--json"])
    assert res.exit_code == 0, res.output
    datos = json.loads(res.output)
    assert datos["total_declarations_in_header"] == 2
    assert sorted(datos["binaries"]) == ["a.o", "src/b.o"]


@necesita_toolchain
def test_el_cli_acepta_varios_binary_explicitos(proyecto):
    res = runner.invoke(
        app,
        ["audit", str(proyecto / "a.h"), "-b", str(proyecto / "a.o"), "-b", str(proyecto / "src" / "b.o"), "--json"],
    )
    datos = json.loads(res.output)
    assert len(datos["binaries"]) == 2
    assert "PRK003" not in {i["code"] for i in datos["issues"]}  # b.h no se audita acá; a.h sí


@necesita_toolchain
def test_el_cli_acepta_un_archivo_y_un_binario_como_antes(proyecto):
    res = runner.invoke(app, ["audit", str(proyecto / "a.h"), "--binary", str(proyecto / "a.o"), "--json"])
    assert res.exit_code == 0, res.output


def test_un_directorio_sin_cabeceras_es_error_de_uso(tmp_path):
    res = runner.invoke(app, ["audit", str(tmp_path)])
    assert res.exit_code == 2


def test_un_archivo_que_no_es_cabecera_es_error_de_uso(tmp_path):
    fuente = tmp_path / "main.c"
    fuente.write_text("int main(void){return 0;}", encoding="utf-8")
    assert runner.invoke(app, ["audit", str(fuente)]).exit_code == 2


def test_audit_md_y_report_no_fallan(tmp_path):
    h = tmp_path / "lib.h"
    h.write_text("int f(void);\nstatic int g(void);\n", encoding="utf-8")
    salida = tmp_path / "r.md"
    res = runner.invoke(app, ["audit", str(h), "--md", str(salida)])
    assert res.exit_code == 0, res.output
    md = salida.read_text(encoding="utf-8")
    assert "`lib.h`" in md and "PRK001" in md

    res = runner.invoke(app, ["report", str(h)])
    assert res.exit_code == 0, res.output
    assert "Símbolos declarados:** 2" in res.output


@necesita_toolchain
def test_el_reporte_markdown_de_un_proyecto_lista_binarios(proyecto):
    res = runner.invoke(app, ["report", str(proyecto)])
    assert res.exit_code == 0, res.output
    assert "Cabeceras analizadas:** 2" in res.output
    assert "`a.o`" in res.output and "`src/b.o`" in res.output
