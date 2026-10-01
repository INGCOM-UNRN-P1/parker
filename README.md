# PARKER — Auditor de Estabilidad de ABI y Visibilidad de Símbolos en C

> 📖 **Manual de Usuario:** Para una guía exhaustiva de comandos, banderas, arquitectura y ejemplos, consultá el [Manual de Uso](MANUAL.md).

**PARKER** es un linter y evaluador de interfaces binarias (ABI) en C. Audita bibliotecas compartidas (`.so`), archivos objeto (`.o`) y cabeceras (`.h`) para detectar fugas de símbolos privados, símbolos faltantes y malas prácticas en interfaces públicas.

---

## 🎯 Alcance

### Qué cubre
- Auditoría de Application Binary Interface (ABI) y control de visibilidad de símbolos en bibliotecas compartidas y objetos C en ELF (`.so` / `.o`). Los `.dll` de Windows no se inspeccionan.
- Detección de fuga de símbolos internos: advertencia sobre funciones globales no documentadas que carecen del calificador `static`.
- Verificación de consistencia entre prototipos de funciones públicas de la cabecera `.h` y la tabla de exportación de símbolos en el binario compilado.

### Qué no cubre (Límites y Delegación)
- Verificación de opacidad de TDAs en código fuente (delegado a `motoko`).
- Auditoría de alineación y padding de structs (delegado a `brett`).
- Medición de costos de saltos o tablas de salto (delegado a `rachel`).

---

## 📋 Requisitos

### Requisitos de Sistema y Entorno
- Linux / WSL / POSIX. Python >= 3.10.

### Dependencias Externas y Binarios
- `nm` (binutils). Es la única herramienta que parker invoca; `readelf` y `objdump` no se usan.

### Integración en el Ecosistema
- CLI `parker`. Plugin registrado en `ripley.plugins` (`abi_audit`).

---

## 🚀 Uso Rápido

```bash
# Auditar solo cabecera
parker audit tda_lista.h

# Contrastar cabecera contra biblioteca compilada
parker audit tda_lista.h --binary libtda_lista.so

# Salida estructurada JSON
parker audit tda_lista.h --json
```

---

## 🔍 Reglas Auditadas

- **`PRK001`**: Funciones declaradas `static` dentro de cabeceras públicas.
- **`PRK002`**: Símbolos exportados en la biblioteca sin declaración en la cabecera (fuga de ABI).
- **`PRK003`**: Símbolos declarados en cabecera pública no encontrados en la biblioteca compilada.

<!-- p1:referencia:inicio — generado por p1-tools/scripts/readme_generado.py: no editar a mano -->

## Referencia rápida

### Requisitos

- Python ≥ 3.11 y [uv](https://docs.astral.sh/uv/getting-started/installation/).
- Programas del sistema: `gcc`.

| Sistema | `gcc` |
|:--|:--|
| Debian / Ubuntu | `sudo apt install gcc` |
| Fedora | `sudo dnf install gcc` |
| Windows | incluido en el entorno de la cátedra (MSYS2 UCRT64) |
| macOS | `xcode-select --install` (clang como `gcc`) |

### Comandos

| Comando | Descripción |
|:--|:--|
| `parker check`, `parker audit` | Audita la cabecera (o todas las de un directorio) y contrasta los símbolos exportados por los binarios. |
| `parker report` | Genera directamente la sección de reporte Markdown de PARKER para Dredd. |
| `parker doctor` | Verifica el estado del entorno de auditoría ABI PARKER (Python, nm, GCC). |

Ayuda de cada comando: `parker <comando> -h`.

### Salida JSON

Con `--json`, estos comandos emiten el resultado como JSON por la salida estándar, para usarlo desde scripts, ripley o dredd: `parker check`, `parker audit`, `parker doctor`. El de `doctor --json` lleva `schema_version` y `ok`.

### Códigos de salida

| Código | Significado |
|:--|:--|
| `0` | Terminó bien (en `doctor`: está todo lo requerido). |
| `1` | El comando encontró problemas (hallazgos, pruebas que fallan, un umbral que no se alcanza) o un dato no se pudo usar (un archivo ilegible, un formato inválido). |
| `2` | Error de uso: comando, opción o argumento inválido. |

<!-- p1:referencia:fin -->
