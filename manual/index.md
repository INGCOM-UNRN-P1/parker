---
title: "Manual de Referencia: parker"
subtitle: "Parker — Auditor de Estabilidad de ABIs, Visibilidad de Símbolos y Librerías Dinámicas"
author: "Cátedra de Algoritmos y Programación"
date: "2026-08-31"
---

(manual-parker)=
# Parker — Auditor de Estabilidad de ABIs, Visibilidad de Símbolos y Librerías Dinámicas

````{abstract}
**Rol en el ecosistema:** Auditoría de binarios y librerías compartidas (`.so` / `.dylib`) para validar que solo se exporten los símbolos públicos declarados en la API y evitar contaminación del espacio de nombres global.
````

---

(manual-parker-proposito)=
## 1. Propósito y Filosofía Pedagógica

La herramienta **`parker`** forma parte del ecosistema oficial de software de la cátedra. Su diseño sigue principios pedagógicos rigurosos:

1. **Evidencia Técnica Directa**: Todo diagnóstico se fundamenta en la norma ISO C (C11/C23), en el modelo de memoria del sistema o en convenciones arquitectónicas formales.
2. **Acción Correctiva Concreta**: Cada advertencia incluye la prescripción técnica inmediata para resolver el defecto sin recurrir a conjeturas.
3. **Autonomía del Estudiante**: Facilita la autoevaluación local antes de la entrega final del trabajo práctico.
4. **Objetividad Docente**: Estandariza la corrección automática eliminando discrepancias subjetivas en la evaluación.

---

(manual-parker-instalacion)=
## 2. Instalación y Diagnóstico del Entorno

````{important}
Asegurate de contar con el compilador GCC/Clang y las librerías del sistema instaladas antes de ejecutar `parker`.
````

Para comprobar el estado de salud de tu entorno de trabajo y las dependencias auxiliares:

````{code-block} bash
# Comprobación de dependencias del sistema
parker doctor
````

Si se detecta la falta de alguna utilidad (como `gdb`, `valgrind`, `clang-format` o `typst`), el comando indicará el paquete exacto a instalar según tu distribución GNU/Linux o entorno MSYS2.

---

(manual-parker-comandos)=
## 3. Referencia Completa de Comandos CLI

A continuación se detallan los subcomandos principales disponibles en `parker`:

| Sintaxis del Comando | Descripción y Efecto |
| :--- | :--- |
| `parker audit-symbols ./lib/libtda.so include/tda.h` | Compara los símbolos exportados por la librería con los prototipos del header. |
| `parker check-abi --v1 lib_v1.so --v2 lib_v2.so` | Detecta incompatibilidades binarias (ABI breaks) entre versiones. |
| `parker hide-symbols src/ -o lib_clean.so` | Aplica `__attribute__((visibility("hidden")))` a funciones privadas. |
| `parker doctor` | Verifica herramientas de introspección binaria (`nm`, `readelf`, `objdump`). |

````{tip}
Podés agregar el flag `--json` a la mayoría de los comandos para exportar resultados en formato estructurado o `--md` para generar reportes Markdown para el informe de entrega.
````

---

(manual-parker-tutorial)=
## 4. Tutorial Paso a Paso con Ejemplos Reales

### Caso de Estudio

Considerá el siguiente fragmento de código representativo:

````{code-block} c
:linenos:
// Función privada interna que NO debe exportarse en la librería
__attribute__((visibility("hidden")))
void balancear_arbol_interno(void *nodo) {
    // detalle privado
}

// Función pública de la API
__attribute__((visibility("default")))
void arbol_insertar(void *arbol, int clave) {
    // llamada pública
}
````

### Ejecución de la Herramienta

Ejecutá el análisis desde tu terminal:

````{code-block} bash
parker audit-symbols ./lib/libtda.so include/tda.h
````

### Salida Obtenida en Consola

````{code-block} text
[!] PARKER ABI AUDITOR: 2 símbolos privados expuestos en libtda.so:
    • 'nodo_crear_interno' (Exportado globalmente en tabla de símbolos ELF).
    • 'buffer_temporal' (Variable global visible externamente).
Sugerencia: Marcá estas funciones como 'static' o agregá '__attribute__((visibility("hidden")))'. 
````

````{note}
Prestá atención a la explicación pedagógica generada: la herramienta no solo señala la línea del problema, sino que explica la causa raíz y el impacto en memoria o arquitectura.
````

---

(manual-parker-ejercicios)=
## 5. Ejercicios Prácticos y Desafíos

Practicá el uso avanzado de **`parker`** resolviendo los siguientes ejercicios:

````{exercise} Desafío 1: Auditoría de Símbolos Exportados
Comprobar que una librería compartida solo exporta su interfaz pública.

**Instrucción de ejecución:**
```bash
parker audit-symbols ./lib/liblista.so include/lista.h
```
````

````{solution} Desafío 1
```bash
parker audit-symbols ./lib/liblista.so include/lista.h
# Verificá que la operación concluya exitosamente con código de salida 0.
```
````

````{exercise} Desafío 2: Detección de Ruptura de ABI
Verificar si cambiar el orden de campos en un struct rompe compatibilidad binaria.

**Instrucción de ejecución:**
```bash
parker check-abi --v1 lib1.so --v2 lib2.so
```
````

````{solution} Desafío 2
```bash
parker check-abi --v1 lib1.so --v2 lib2.so
# Revisá el archivo generado o el informe en terminal para confirmar la resolución del problema.
```
````

````{exercise} Desafío 3: Ocultamiento Automático de Símbolos
Compilar con `-fvisibility=hidden` y exportar selectivamente.

**Instrucción de ejecución:**
```bash
parker hide-symbols src/ -o lib/libtda.so
```
````

````{solution} Desafío 3
```bash
parker hide-symbols src/ -o lib/libtda.so
# Comprobá que la salida confirme la ausencia de advertencias o errores pendientes.
```
````

---

(manual-parker-makefile)=
## 6. Integración en el Flujo de Trabajo y Makefile

Para incorporar `parker` de forma automática a tu flujo de desarrollo, agregá la siguiente regla en el `Makefile` de tu proyecto:

````{code-block} makefile
check-parker:
	@echo "=== Ejecutando verificación con parker ==="
	parker check src/ include/

.PHONY: check-parker
````

Ejecutá `make check-parker` antes de cada commit para asegurar que tu código conserve el estado de aprobación.

---

(manual-parker-arquitectura)=
## 7. Arquitectura Interna y Mecanismo Técnico

La herramienta **`parker`** implementa un motor de alta precisión basado en:

- **Tecnología Núcleo:** `ELF Symbol Table Reader (readelf/nm) + DWARF ABI Comparator + Visibility Attribute Injector`.
- **Aislamiento y Determinismo:** Diseñada para operar sin efectos colaterales en entornos de integración continua (CI), terminales de estudiantes y servidores docentes headless.
- **Manejo de Errores Pedagógico:** Todo fallo de sintaxis, memoria o lógica se traduce en una acción prescriptiva concreta con su respectiva justificación técnica.

---

(manual-parker-ecosistema)=
## 8. Integración y Conexión con el Ecosistema

````{note}
Ninguna herramienta opera de forma aislada. **`parker`** forma parte del pipeline integral de evaluación, verificación y enseñanza de la cátedra.
````

### Diagrama de Flujo e Interoperabilidad

````{mermaid}
graph TD
    SO[libtda.so: Librería Compartida] --> PRK[Parker: Auditor de ABI]
    HDR[include/tda.h: API Pública] --> PRK
    PRK -->|Inspección Tabla ELF| NM[readelf / nm Engine]
    PRK -->|Ocultamiento de Símbolos| MOT[Motoko: Modularidad Estricta]
    PRK -->|Reporte de Estabilidad ABI| DRD[Dredd: Orquestador Masivo]
````

### Matriz de Intercambio de Datos

| Canal | Herramientas Conectadas | Tipo de Datos Transferidos |
| :--- | :--- | :--- |
| **Entradas (Inputs)** | - `Librerías compartidas (.so) y headers de exportación` | Código fuente, AST, binarios, testcases, contratos |
| **Salidas (Outputs)** | - `motoko (encapsulamiento binario)`
- `dredd (auditoría de entregas librerías)` | Informes Markdown, diagnósticos Rich, JSON, actas |
| **Sincronización** | `motoko`, `corbel`, `dredd` | Validación cruzada, flags compartidos y autofix |

### Pipeline de Integración Recomendado

Podés encadenar `parker` con otras herramientas del ecosistema en una única línea de comando:

````{code-block} bash
# Pipeline de integración típico
parker audit-symbols ./lib/libtda.so include/tda.h
````

