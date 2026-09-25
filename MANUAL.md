# Manual de Uso y Referencia Técnica: parker

> **PARKER** — Auditor de estabilidad de ABIs, visibilidad de símbolos y compatibilidad binaria en C
> **Versión:** `0.1.0` · **CLI principal:** `parker` · **Plugin Ripley:** `abi_audit`

---

## 1. Arquitectura y Propósito Pedagógico

`parker` forma parte del ecosistema de herramientas de la cátedra de Programación 1 (UNRN). Su objetivo central es resolver de forma modular, determinista y automatizada las tareas asociadas a su dominio específico dentro del ciclo de desarrollo, evaluación y aprendizaje de software en C.

### Alcance Funcional (Qué cubre)
- Auditoría de Application Binary Interface (ABI) y control de visibilidad de símbolos en bibliotecas compartidas y objetos C en ELF (`.so` / `.o`). Los `.dll` de Windows no se inspeccionan.
- Detección de fuga de símbolos internos: advertencia sobre funciones globales no documentadas que carecen del calificador `static`.
- Verificación de consistencia entre prototipos de funciones públicas de la cabecera `.h` y la tabla de exportación de símbolos en el binario compilado.

### Límites de Responsabilidad y Delegación (Qué no cubre)
- Verificación de opacidad de TDAs en código fuente (delegado a `motoko`).
- Auditoría de alineación y padding de structs (delegado a `brett`).
- Medición de costos de saltos o tablas de salto (delegado a `rachel`).

### Principios de Diseño
- **Enfoque Pedagógico:** Diagnósticos y mensajes en español rioplatense orientados a facilitar la comprensión de errores conceptuales.
- **Salida Estructurada Dual:** Soporte nativo para visualización enriquecida en terminal (Rich) y salida parseable para orquestadores (`--json`).
- **Integración Contractual:** Capacidad de emitir secciones de reporte para `dredd` (`dredd-section`) y actuar como satélite orquestado por `ripley`.
- **Idempotencia y Robustez:** Validación de precondiciones y comandos de autodiagnóstico (`doctor`) para verificación del entorno.

---

## 2. Instalación y Requisitos

### Requisitos del Sistema
- **Python:** `>= 3.10` (recomendado Python 3.11 o 3.12).
- **Gestor de paquetes:** [`uv`](https://github.com/astral-sh/uv) (entorno estándar de cátedra).
- **Toolchain C (si aplica):** GCC / Clang, Make, GDB y bibliotecas estándar de desarrollo.

### Instalación en el Entorno de Usuario
Para instalar la herramienta de forma global y aislada en el sistema mediante `uv tool`:
```bash
uv tool install --editable /home/mrtin/dev/tools/parker
```

### Verificación de Instalación
Ejecutá el comando `doctor` para constatar que todas las dependencias y binarios requeridos estén presentes y operativos:
```bash
parker doctor
```

---

## 3. Guía Integral de Comandos (CLI)

| Comando | Descripción Breve |
| :--- | :--- |
| [`parker check`](#check) | Audita la cabecera (o todas las de un directorio) y contrasta los símbolos exportados por los binarios. |
| [`parker audit`](#audit) | Audita la cabecera (o todas las de un directorio) y contrasta los símbolos exportados por los binarios. |
| [`parker report`](#report) | Genera directamente la sección de reporte Markdown de PARKER para Dredd. |
| [`parker doctor`](#doctor) | Verifica el estado del entorno de auditoría ABI PARKER (Python, nm, GCC). |

### `parker check`

Audita la cabecera (o todas las de un directorio) y contrasta los símbolos exportados por los binarios.

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `header` | `<class 'pathlib._local.Path'>` | Cabecera C (.h) o directorio de proyecto (cabeceras y .so/.o descubiertos) |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--binary`, `-b` | `Optional[List[pathlib._local.Path]]` | `None` | Biblioteca compartida (.so) u objeto (.o) a contrastar; se puede repetir |
| `--json` | `<class 'bool'>` | `False` | Emitir salida en formato JSON estructurado |
| `--md`, `--output-md` | `Optional[pathlib._local.Path]` | `None` | Generar sección de reporte en formato Markdown para fusión en Dredd. |

#### Ejemplo de Invocación
```bash
parker check <header>
```

### `parker audit`

Audita la cabecera (o todas las de un directorio) y contrasta los símbolos exportados por los binarios.

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `header` | `<class 'pathlib._local.Path'>` | Cabecera C (.h) o directorio de proyecto (cabeceras y .so/.o descubiertos) |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--binary`, `-b` | `Optional[List[pathlib._local.Path]]` | `None` | Biblioteca compartida (.so) u objeto (.o) a contrastar; se puede repetir |
| `--json` | `<class 'bool'>` | `False` | Emitir salida en formato JSON estructurado |
| `--md`, `--output-md` | `Optional[pathlib._local.Path]` | `None` | Generar sección de reporte en formato Markdown para fusión en Dredd. |

#### Ejemplo de Invocación
```bash
parker audit <header>
```

### `parker report`

Genera directamente la sección de reporte Markdown de PARKER para Dredd.

#### Argumentos
| Argumento | Tipo | Descripción |
| :--- | :--- | :--- |
| `header` | `<class 'pathlib._local.Path'>` | Cabecera C (.h) o directorio de proyecto |

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--output`, `-o` | `Optional[pathlib._local.Path]` | `None` | Ruta de destino del archivo Markdown. |
| `--binary`, `-b` | `Optional[List[pathlib._local.Path]]` | `None` | Biblioteca compartida (.so) u objeto (.o); se puede repetir. |

#### Ejemplo de Invocación
```bash
parker report <header>
```

### `parker doctor`

Verifica el estado del entorno de auditoría ABI PARKER (Python, nm, GCC).

#### Opciones y Banderas
| Opción / Banderas | Tipo | Por Defecto | Descripción |
| :--- | :--- | :--- | :--- |
| `--json` | `<class 'bool'>` | `False` | Emitir diagnóstico en formato JSON estructurado. |

#### Ejemplo de Invocación
```bash
parker doctor
```

---

## 4. Formatos de Salida e Integración con el Ecosistema

### Modo Interactivo / Terminal (Rich)
Por defecto, la herramienta renderiza paneles, árboles y tablas estilizadas para facilitar la lectura del estudiante y docente en terminales modernas con soporte ANSI.

### Modo Estructurado JSON (`--json`)
Para integración con pipelines de CI/CD, scripts de automatización u orquestadores externos, la opción `--json` emite un documento JSON estricto por la salida estándar (`stdout`), dirigiendo cualquier mensaje de logging a `stderr`:
```bash
parker check --json
```

### Integración con Dredd (`dredd-section`)
Cuando la herramienta genera reportes de evaluación para entregas de alumnos, produce una sección Markdown estandarizada conforme al contrato de integración de Dredd (v1.0.0):
```markdown
<!-- dredd-section: parker, tool=parker, version=0.1.0, status=ok -->
```
Este encabezado garantiza la agregación determinista de los hallazgos en la rúbrica docente.

### Integración con Ripley
`parker` está registrada en el catálogo de plugins satélites de Ripley (`SATELLITE_CATALOG`). Puede invocarse directamente a través del motor de evaluación de Ripley configurando el análisis en `ripley.toml`.

---

## 5. Diagnóstico y Códigos de Salida

### Códigos de Retorno (`exit code`)
| Código | Significado |
| :---: | :--- |
| `0` | Ejecución exitosa sin hallazgos críticos ni errores de sintaxis. |
| `1` | Hallazgos pedagógicos detectados, infracción de reglas o advertencias activas. |
| `2` | Error de sintaxis en argumentos CLI o archivo fuente no encontrado. |
| `>2` | Error no recuperable del sistema, fallo de memoria o excepción interna. |

### Diagnóstico del Entorno (`doctor`)
Ante comportamientos inesperados, verificá el estado operativo con:
```bash
parker doctor
```
Comprueba la presencia de las dependencias requeridas y la integridad de los componentes del paquete.