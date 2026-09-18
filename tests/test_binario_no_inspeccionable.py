"""Regresión de PARKER-D0301: no acusar de "no encontradas" a funciones que no se pudieron verificar.

Si `nm` fallaba o el archivo no era ELF, `inspect_elf_symbols` tragaba la
excepción y devolvía 0 símbolos: PRK003 (ERROR) marcaba como no implementada a
cada función de la cabecera, incluso las que sí estaban en la librería real.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

from parker.core.abi_checker import check_abi_compliance
from parker.core.symbol_inspector import BinarioNoInspeccionable, inspect_elf_symbols

necesita_toolchain = pytest.mark.skipif(
    not (shutil.which("gcc") and shutil.which("nm")), reason="requiere gcc y nm"
)

CABECERA = "int primitiva_ok(int x);\nint otra_funcion(int y);\n"
FUENTE = '#include "tda.h"\nint primitiva_ok(int x) { return x + 1; }\nint otra_funcion(int y) { return y * 2; }\n'


@pytest.fixture
def proyecto(tmp_path):
    (tmp_path / "tda.h").write_text(CABECERA, encoding="utf-8")
    (tmp_path / "tda.c").write_text(FUENTE, encoding="utf-8")
    return tmp_path


@necesita_toolchain
def test_un_archivo_que_no_es_elf_no_es_inspeccionable(tmp_path):
    falso = tmp_path / "falso.so"
    falso.write_text("texto plano, no es ELF\n", encoding="utf-8")
    with pytest.raises(BinarioNoInspeccionable):
        inspect_elf_symbols(falso)


@necesita_toolchain
def test_binario_invalido_no_genera_prk003_falsos(proyecto):
    falso = proyecto / "falso.so"
    falso.write_text("texto plano\n", encoding="utf-8")
    reporte = check_abi_compliance(proyecto / "tda.h", falso)

    codigos = [i.code for i in reporte.issues]
    assert "PRK003" not in codigos
    assert codigos.count("PRK000") == 1


@necesita_toolchain
def test_libreria_real_no_produce_falsos_positivos(proyecto):
    lib = proyecto / "libtda.so"
    subprocess.run(["gcc", "-shared", "-fPIC", str(proyecto / "tda.c"), "-o", str(lib)], check=True)
    reporte = check_abi_compliance(proyecto / "tda.h", lib)
    assert [i.code for i in reporte.issues] == []


@necesita_toolchain
def test_una_funcion_realmente_ausente_sigue_detectandose(proyecto):
    (proyecto / "tda.h").write_text(CABECERA + "int fantasma(void);\n", encoding="utf-8")
    lib = proyecto / "libtda.so"
    subprocess.run(["gcc", "-shared", "-fPIC", str(proyecto / "tda.c"), "-o", str(lib)], check=True)
    reporte = check_abi_compliance(proyecto / "tda.h", lib)
    prk003 = [i for i in reporte.issues if i.code == "PRK003"]
    assert [i.symbol_name for i in prk003] == ["fantasma"]


def test_sin_nm_se_informa_en_vez_de_devolver_cero_simbolos(tmp_path, monkeypatch):
    def sin_nm(*a, **k):
        raise FileNotFoundError("nm")

    monkeypatch.setattr("parker.core.symbol_inspector.subprocess.run", sin_nm)
    binario = tmp_path / "x.so"
    binario.write_bytes(b"\x7fELF")
    with pytest.raises(BinarioNoInspeccionable, match="nm"):
        inspect_elf_symbols(binario)
