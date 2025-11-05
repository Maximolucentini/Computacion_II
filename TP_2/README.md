# COMPUTACIÓN II – TP2  
## Sistema de Scraping y Análisis Web Distribuido

Este trabajo práctico implementa un sistema distribuido de **scraping y análisis web** usando Python.  
El sistema está formado por **dos servidores** que cooperan:

- **Servidor A – Scraping asíncrono (asyncio + aiohttp)**  
- **Servidor B – Procesamiento pesado (multiprocessing + socketserver)**  

El cliente sólo se comunica con el **Servidor A** (Parte C – Transparencia para el cliente).  

Además se implementan las **3 opciones del Bonus Track**:

1. **Cola de tareas con IDs** (`/tasks`, `/status/{task_id}`, `/result/{task_id}`)
2. **Rate limiting por dominio + caché en memoria con TTL**
3. **Análisis avanzado** en el Servidor B (tecnologías, SEO, JSON-LD, accesibilidad)

El servidor de scraping también incluye un **límite configurable de tamaño máximo de HTML**, para evitar descargar páginas demasiado grandes y proteger recursos.

---

## Requisitos previos

- **Python 3.10+** (probado con Python 3.x en Linux)
- `pip` para instalar dependencias
- Conexión a Internet para poder hacer scraping de sitios reales

Dependencias de Python (las mismas que indica el enunciado):

```bash
pip install aiohttp beautifulsoup4 lxml Pillow selenium aiofiles
```

> Opcional: para screenshots reales con Selenium se necesita Chrome/Firefox y su driver (ChromeDriver o GeckoDriver).  
> Si no están configurados, el sistema genera un **screenshot placeholder** con Pillow para que el TP siga funcionando.

También se incluye un `requirements.txt` para instalarlas de una sola vez.

---

## Instalación

1. Clonar o copiar el proyecto en una carpeta llamada `TP2` (como pide el enunciado).

2. Crear y activar un entorno virtual:

### Linux / macOS

```bash
cd TP2
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Windows (PowerShell)

```bash
cd TP2
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

Para salir del entorno virtual:

```bash
deactivate
```

---

## Estructura del proyecto

Se respeta la estructura sugerida en el enunciado, con un archivo extra para el análisis avanzado:

```text
TP2/
├── server_scraping.py          # Servidor asyncio (Parte A + Bonus)
├── server_processing.py        # Servidor multiprocessing (Parte B + Bonus)
├── client.py                   # Cliente de prueba (Parte C)
├── scraper/
│   ├── __init__.py
│   ├── html_parser.py          # Parsing HTML + estructura + lista de imágenes
│   ├── metadata_extractor.py   # Extracción de meta tags (description, keywords, og:*)
│   └── async_http.py           # Cliente HTTP asíncrono (aiohttp + límite de tamaño)
├── processor/
│   ├── __init__.py
│   ├── screenshot.py           # Generación de screenshot (Selenium + fallback Pillow)
│   ├── performance.py          # Análisis de rendimiento del HTML principal
│   ├── image_processor.py      # Descarga y generación de thumbnails
│   └── advanced_analysis.py    # BONUS: tecnologías, SEO, JSON-LD, accesibilidad
├── common/
│   ├── __init__.py
│   ├── protocol.py             # Protocolo length(4 bytes) + JSON para sockets
│   └── serialization.py        # Serialización JSON <-> bytes
├── tests/
│   ├── test_scraper.py         # Tests del servidor A (cola de tareas + límite HTML)
│   └── test_processor.py       # Tests de funciones de procesamiento (servidor B)
├── requirements.txt
└── README.md
```

---

## Ejecución

### 1. Levantar el Servidor de Procesamiento (Parte B)

En una terminal:

```bash
cd TP2
source .venv/bin/activate            # en Windows: .\.venv\Scripts\Activate.ps1
python server_processing.py -i 127.0.0.1 -p 9000 -n 4
```

Parámetros:

- `-i / --ip` : IP de escucha (soporta IPv4 e IPv6)  
- `-p / --port` : puerto del servidor B  
- `-n / --processes` : cantidad de procesos en el pool (`multiprocessing`).  
  Si se omite, usa `multiprocessing.cpu_count()`.

Responsabilidades del servidor B:

- Recibir solicitudes desde A por sockets TCP.  
- Ejecutar en procesos separados:
  - **Captura de screenshot** (PNG, base64).  
  - **Análisis de rendimiento** (tiempo de carga, tamaño total, número de requests).  
  - **Análisis de imágenes** (thumbnails).  
  - **Análisis avanzado** (bonus): tecnologías, SEO, JSON-LD, accesibilidad.  
- Devolver resultados a A mediante el protocolo definido.

---

### 2. Levantar el Servidor de Scraping Asíncrono (Parte A)

En otra terminal:

```bash
cd TP2
source .venv/bin/activate
python server_scraping.py -i 127.0.0.1 -p 8000 -w 4 -r 60 --cache-ttl 3600 --max-html-size 10
```

Parámetros:

- `-i / --ip` : IP de escucha (IPv4 o IPv6).  
- `-p / --port` : puerto del servidor A.  
- `-w / --workers` : cantidad de tareas concurrentes máximas (semáforo asyncio).  
- `-r / --rate-limit` : máximo de requests por minuto por dominio (0 = sin límite).  
- `--cache-ttl` : TTL en segundos de la caché en memoria (0 = sin caché).
- `--max-html-size` : **tamaño máximo de HTML en MB** (default: `10`).  
  Si el servidor detecta (por `Content-Length` o por la suma de chunks) que la página supera ese límite, **cancela la descarga y devuelve un error controlado**.

Responsabilidades del servidor A:

- Recibir URLs vía HTTP.  
- Hacer **scraping asíncrono** de la página (no bloquear el event loop).  
- Aplicar límite de tamaño de HTML antes de descargar demasiado contenido.  
- Extraer:
  - Título  
  - Links  
  - Meta tags (description, keywords, Open Graph)  
  - Estructura de headers H1–H6  
  - Cantidad de imágenes + lista de URLs de imágenes  
- Coordinar con el **Servidor B** usando sockets TCP y protocolo length+JSON.  
- Consolidar resultados y devolver un **JSON único** al cliente.  

Además, implementa:

- **Rate limiting** por dominio (Bonus Opción 2).  
- **Caché** de resultados recientes con TTL configurable (Bonus Opción 2).  
- **Cola de tareas con IDs** (Bonus Opción 1).  

---

### 3. Ejecutar el cliente (Parte C)

Con ambos servidores levantados:

```bash
cd TP2
source .venv/bin/activate
python client.py -i 127.0.0.1 -p 8000 https://example.com https://www.python.org
```

Parámetros:

- `-i / --ip` : IP del servidor A.  
- `-p / --port` : puerto del servidor A.  
- `-t / --timeout` : timeout total por request.  
- `-c / --concurrency` : máximo de requests concurrentes del cliente hacia A.  
- `urls` : lista de URLs a analizar.

El cliente:

- Solo se comunica con A (transparencia para el cliente – Parte C).  
- Llama a `/scrape?url=...` y muestra un resumen:
  - Título, cantidad de links, cantidad de imágenes.  
  - Meta tags principales.  
  - Métricas de rendimiento.  
  - Si hay screenshot y thumbnails disponibles.  

---

## Endpoints HTTP del Servidor A

### 1. Health check

```text
GET /
```

Respuesta:

```json
{"status": "ok"}
```

---

### 2. Scraping sin cola (modo síncrono para el cliente)

```text
GET  /scrape?url=https://example.com
POST /scrape   {"url": "https://example.com"}
```

Formato de respuesta :

```json
{
  "url": "https://example.com",
  "timestamp": "2025-11-03T15:30:00Z",
  "scraping_data": {
    "title": "Título de la página",
    "links": ["url1", "url2"],
    "meta_tags": {
      "description": "...",
      "keywords": "...",
      "og:title": "..."
    },
    "structure": {
      "h1": 1,
      "h2": 3,
      "h3": 0,
      "h4": 0,
      "h5": 0,
      "h6": 0
    },
    "images_count": 5,
    "images": ["https://example.com/img1.jpg", "..."]
  },
  "processing_data": {
    "screenshot": "base64_png_o_placeholder",
    "performance": {
      "load_time_ms": 1234,
      "total_size_kb": 200.5,
      "num_requests": 1
    },
    "thumbnails": ["base64_thumb1", "base64_thumb2"],
    "advanced": {
      "url": "https://example.com",
      "technologies": {
        "frameworks_js": ["React"],
        "cms": "WordPress",
        "other": ["Bootstrap"]
      },
      "seo": {
        "score": 80,
        "has_meta_description": true,
        "has_keywords": true,
        "has_h1": true,
        "title_length": 20,
        "h1_count": 1
      },
      "structured_data": {
        "json_ld_count": 1,
        "schema_org_detected": true,
        "examples": []
      },
      "accessibility": {
        "total_images": 5,
        "images_with_alt": 4,
        "alt_coverage": 0.8
      }
    }
  },
  "status": "success",
  "processing_status": "success"
}
```

En caso de error se devuelve un JSON con `"status": "error"` y mensaje descriptivo, con códigos HTTP apropiados:

- `400` → URL inválida / parámetros faltantes  
- `413` → **HTML demasiado grande** (supera `--max-html-size`)  
- `502` → error al hacer scraping (problemas de red, HTTP 4xx/5xx)  
- `500` → error interno inesperado  

---

### 3. Cola de tareas (Bonus – Opción 1)

**Crear tarea**

```text
POST /tasks
Body JSON: {"url": "https://example.com"}
```

Respuesta:

```json
{
  "task_id": "ab12cd34ef...",
  "status": "pending"
}
```

**Consultar estado**

```text
GET /status/{task_id}
```

Respuesta típica:

```json
{
  "task_id": "ab12cd34ef...",
  "status": "scraping | processing | completed | failed | pending",
  "url": "https://example.com",
  "created_at": "2025-11-03T15:30:00Z",
  "error": "..."         // solo si status = failed
}
```

**Obtener resultado**

```text
GET /result/{task_id}
```

- Mientras la tarea no termine:

```json
{
  "task_id": "ab12cd34ef...",
  "status": "scraping",
  "url": "https://example.com",
  "message": "La tarea aún no está completada"
}
```

- Cuando termina correctamente:

```json
{
  "task_id": "ab12cd34ef...",
  "status": "completed",
  "url": "https://example.com",
  "result": { ... mismo JSON que /scrape ... }
}
```

---

## Manejo de errores

Siguiendo las consignas del TP:

- **URLs inválidas**  
  - Se valida esquema (`http`/`https`) y host con `urllib.parse`.  
  - Respuesta: HTTP 400 + JSON `{"status": "error", "error": "..."}`
- **Timeouts de scraping**  
  - Se usa `aiohttp.ClientTimeout(total=30)` y se captura `asyncio.TimeoutError`.  
  - Respuesta: HTTP 502 con mensaje de timeout.
- **Errores HTTP (4xx/5xx)**  
  - `resp.raise_for_status()` lanza excepción capturada como `HttpError`.  
  - Respuesta: HTTP 502 con mensaje de error HTTP.
- **HTML demasiado grande**  
  - En `scraper/async_http.py` se controla tanto el encabezado `Content-Length` como el tamaño real acumulado por chunks.  
  - Si se supera el límite configurado (`--max-html-size` en MB), se lanza `ContentTooLargeError` y el servidor A responde con **HTTP 413** y un JSON de error.
- **Errores de comunicación A ↔ B**  
  - Se capturan `ConnectionRefusedError`, `asyncio.TimeoutError`, `OSError`.  
  - En ese caso se devuelve igualmente el `scraping_data`, pero `processing_status = "failed"` y `processing_data` con campos `None`/vacíos.
- **Errores en el pool de procesos (B)**  
  - Se captura la excepción al hacer `future.result()` y se responde con `"status": "error"` hacia A, que luego lo traduce.

---

## Tests

Con el entorno virtual activo:

```bash
cd TP2
source .venv/bin/activate

# Tests del servidor A (asyncio, cola de tareas y límite de tamaño de HTML)
python -m tests.test_scraper

# Tests de funciones de procesamiento del servidor B
python -m tests.test_processor
```

### `tests/test_scraper.py`

Incluye pruebas de:

- **Caso feliz de scraping** sobre `https://example.com`, verificando que:
  - El servidor A responde con HTTP 200.
  - El JSON tiene `status == "success"` y las claves esperadas en `scraping_data` y `processing_data`.
- **URLs inválidas**:  
  - Chequea que se devuelva HTTP 400 y un mensaje de error adecuado.
- **Cola de tareas (Bonus Opción 1)**:  
  - Flujo completo con creación de tarea (`/tasks`), consulta de estado (`/status/{task_id}`) y obtención de resultado (`/result/{task_id}`).
- **Límite máximo de HTML con mocks**:  
  - Tests unitarios de `fetch_html` usando `unittest.mock` para simular respuestas HTTP:
    - Caso donde `Content-Length` o el tamaño acumulado **supera** `max_html_size`: se verifica que se lance `ContentTooLargeError` con un mensaje descriptivo.
    - Caso donde el contenido está **dentro del límite**: se verifica que se devuelva correctamente el HTML decodificado y la URL final.

De esta forma el comportamiento del **tamaño máximo de HTML** queda verificado de forma automática sin depender de páginas reales gigantes.

### `tests/test_processor.py`

Pruebas sobre el servidor B (a nivel de funciones):

- `analyze_performance`:  
  - Recibe un HTML sintético y devuelve métricas (`load_time_ms`, `total_size_kb`, `num_requests`).
- `generate_thumbnails`:  
  - Verifica que se manejen correctamente las descargas fallidas y que las miniaturas se generen (o se devuelva lista vacía) sin romper.
- `analyze_advanced`:  
  - Usa un HTML de ejemplo con tags típicos para probar detección de tecnologías, SEO básico, JSON-LD y accesibilidad.

---

## Notas sobre screenshots

- Si **Selenium + driver** están correctamente instalados, `processor/screenshot.py` genera una captura real de la página en PNG y la devuelve en base64.  
- Si no, el módulo genera una imagen simple (placeholder) con texto `"Screenshot no disponible"` usando Pillow.  
  De esta forma, la funcionalidad de screenshot está implementada sin hacer fallar el resto del sistema.

---

## Resumen de cobertura de consignas

- **Parte A – Servidor Asyncio**  
  - Uso de `asyncio` + `aiohttp`.  
  - Scraping asíncrono, extracción de título, links, meta tags, estructura H1–H6, cantidad de imágenes.  
  - Comunicación asíncrona con el servidor B mediante sockets TCP y protocolo length+JSON.
  - Límite de tamaño máximo de HTML configurable y manejo de error correspondiente (HTTP 413).

- **Parte B – Servidor Multiprocessing**  
  - Uso de `socketserver` + `ProcessPoolExecutor` (multiprocessing).  
  - Screenshot, análisis de rendimiento, thumbnails de imágenes.  

- **Parte C – Transparencia para el Cliente**  
  - Cliente solo habla con A; B es completamente transparente.  

- **Bonus Track**  
  - Opción 1: sistema de cola con `task_id` y endpoints `/tasks`, `/status/{task_id}`, `/result/{task_id}`.  
  - Opción 2: rate limiting por dominio + caché en memoria con TTL.  
  - Opción 3: análisis avanzado en B (tecnologías, SEO, JSON-LD, accesibilidad).