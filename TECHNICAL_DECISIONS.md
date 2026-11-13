# Registro de Decisiones Técnicas y Arquitectónicas (ADR)
## Plataforma LegalAI México

---

### ADR-001: Selección de Runtime Python 3.11 para el Backend
* **Estado:** Aprobado
* **Contexto:**
  El entorno anfitrión dispone de Python 3.14.6 y Python 3.11.15 (`C:\Users\Asus\.local\bin\python3.11.exe`). Aunque Python 3.14 es la versión más reciente, la mayoría de librerías del ecosistema de inteligencia artificial (PyTorch, bibliotecas de embeddings, dependencias nativas de tokenización, Pydantic compiled wheels y pgvector drivers) carecen de soporte binario estable o presentan incompatibilidades en Windows para Python 3.14.
* **Decisión:**
  Fijar **Python 3.11.15** como la versión oficial del backend y los trabajadores asíncronos. Se configurará un entorno virtual dedicado (`backend/.venv`) usando explícitamente el ejecutable de Python 3.11.
* **Consecuencias:**
  * Estabilidad absoluta con SQLAlchemy 2.0, FastAPI, PyTorch, LangChain/LlamaIndex, psycopg3 y pgvector.
  * Compatibilidad uniforme entre el desarrollo local en Windows y los contenedores Docker Linux (`python:3.11-slim`).

---

### ADR-002: Asignación de Modelos Ollama según el Hardware Detectado
* **Estado:** Aprobado
* **Contexto:**
  La inspección física del equipo reveló:
  * GPU dedicada: **NVIDIA GeForce RTX 4050 Laptop GPU (6,141 MiB VRAM / 6 GB GDDR6)**.
  * CPU: **AMD Ryzen 5 7535HS (6 núcleos, 12 hilos)**.
  * RAM del sistema: **16 GB DDR5** (con ~4.3 GB libres al momento de la inspección).
  * Modelos preinstalados en Ollama local: `bge-m3:latest` (1.15 GB), `qwen3.5:4b` (3.38 GB), `hermes3:latest` (4.66 GB), `qwen2.5-coder:7b` (4.68 GB), `gemma3:4b` (3.33 GB), `qwen3.6:latest` (23 GB).
* **Decisión:**
  1. **Embeddings Jurídicos:** Asignar **`bge-m3:latest`**. Ocupa únicamente 1.15 GB de VRAM, permitiendo generación de vectores de 1024 dimensiones en milisegundos con alta retención de español jurídico.
  2. **Inferencia y Análisis de Documentos:** Asignar **`qwen3.5:4b`** como modelo de cabecera predeterminado (ocupa ~3.4 GB de VRAM) y alternativamente **`qwen2.5-coder:7b`** (ocupa ~4.7 GB de VRAM) para tareas de generación de salidas JSON estrictas y análisis contractual profundo.
  3. **Restricción Estricta:** Bloquear en el backend la selección de modelos de 23 GB (`qwen3.6`) en el entorno local, ya que superarían la VRAM (6 GB) y la memoria física libre del sistema (4.3 GB), lo cual provocaría *swapping* masivo, congelamiento del sistema operativo o fallos catastróficos por Out Of Memory (OOM).
* **Consecuencias:**
  * Inferencia 100% acelerada por GPU a alta velocidad (>35-50 tokens/segundo).
  * Operación sin riesgo de degradar el rendimiento del equipo de trabajo.

---

### ADR-003: Estrategia de Aislamiento Multi-Tenant y Seguridad de Datos
* **Estado:** Aprobado
* **Contexto:**
  La plataforma será utilizada inicialmente por un bufete de abogados mexicano y posteriormente comercializada a múltiples despachos bajo modelo SaaS. La información documental de un despacho es confidencial y está protegida por el Secreto Profesional del Abogado y la LFPDPPP.
* **Decisión:**
  * Implementar arquitectura de **Base de Datos Compartida con Aislamiento Estricto por Fila (*Shared Database, Tenant-Partitioned*)**.
  * Cada tabla de negocio incluye `tenant_id: UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT`.
  * Middleware `TenantContextMiddleware` inyecta automáticamente el tenant en las transacciones mediante variables de contexto asíncronas de Python (`contextvars`).
  * En PostgreSQL se activarán políticas de *Row-Level Security (RLS)* como capa de defensa en profundidad.
  * Rutas de almacenamiento lógico y físico segregadas por tenant.
* **Consecuencias:**
  * Cero riesgo de fuga cruzada de datos entre despachos.
  * Facilidad de escalamiento y respaldo selectivo por despacho.

---

### ADR-004: Estrategia de Persistencia Vectorial y PostgreSQL 16
* **Estado:** Aprobado
* **Contexto:**
  PostgreSQL 16 está en ejecución como servicio local en el puerto 5432. Sin embargo, la extensión `pgvector` no se encuentra instalada en el directorio de extensiones del servidor local de Windows.
* **Decisión:**
  * Diseñar una capa de persistencia vectorial desacoplada en SQLAlchemy:
    1. Si la extensión `vector` está habilitada en PostgreSQL, utilizar índices HNSW nativos con distancia coseno.
    2. Como soporte de alta disponibilidad y desarrollo nativo en Windows mientras se compila o habilita el binario de `pgvector` (o se usa PostgreSQL en Docker), el backend dispondrá de un adaptador vectorial que almacena los arrays de embeddings en columnas `ARRAY(Float)` con cálculo de similaridad coseno optimizado y búsqueda textual complementaria en español (`tsvector` con diccionario `spanish`).
* **Consecuencias:**
  * El desarrollo local no se bloquea por la ausencia del binario compilado de `pgvector` en Windows.
  * La migración a entornos con `pgvector` nativo (Docker o AWS Aurora / RDS) es transparente y automática mediante Alembic.

---

### ADR-005: Principio de Inmutabilidad Documental y Trazabilidad Criptográfica
* **Estado:** Aprobado
* **Contexto:**
  En el ámbito legal mexicano, la alteración inadvertida o no autorizada de un acuerdo judicial, contrato o constancia procesal invalida su valor probatorio y genera responsabilidad civil/penal.
* **Decisión:**
  * Todo documento ingresado al sistema se procesa con hashing **SHA-256** inmediato.
  * El archivo original binario se marca como de solo lectura (*Write Once, Read Many*). Queda estrictamente prohibido sobrescribir el archivo original.
  * Cualquier modificación, redacción o sugerencia se registra en tablas independientes de versionado (`document_versions`) y sugerencias (`ai_suggestions`).
* **Consecuencias:**
  * Preservación del valor probatorio y cadena de custodia documental.
  * Capacidad de auditar y comparar cualquier versión contra el documento original primigenio.

---

### ADR-006: Flujo Obligatorio Human-in-the-Loop (HITL) para Validez Jurídica
* **Estado:** Aprobado
* **Contexto:**
  Las herramientas de IA pueden generar alucinaciones, sesgos o interpretaciones descontextualizadas. Ninguna resolución o dictamen puede tener efectos legales sin el aval de un profesional del derecho.
* **Decisión:**
  * Todo análisis generado por IA nace con el estado `PENDIENTE_VALIDACION`.
  * La plataforma no permitirá exportar documentos como definitivos ni emitir dictámenes oficiales hasta que un usuario con rol `SENIOR_LAWYER` o `MANAGING_PARTNER` revise las sugerencias, efectúe correcciones y apruebe formalmente el resultado.
  * El sistema registrará en la tabla `legal_validations` la identidad del abogado, su número de Cédula Profesional, fecha, hora, observaciones y el hash de la versión validada.
* **Consecuencias:**
  * Cumplimiento estricto de las directrices del proyecto: la IA asiste, pero la responsabilidad y conclusión final recae 100% en el abogado.

---

### ADR-007: Procesamiento Asíncrono Resiliente
* **Estado:** Aprobado
* **Contexto:**
  El OCR de expedientes extensos (acuerdos de 50 a 300 páginas) y la generación de embeddings demandan tiempo y no deben bloquear el hilo principal de peticiones HTTP en FastAPI. Redis no está instalado actualmente como servicio nativo en Windows.
* **Decisión:**
  * El backend implementará una arquitectura de colas con interfaz abstracta:
    1. Modo Ligero Local: Utilizar `FastAPI BackgroundTasks` con registro transaccional de estado en PostgreSQL (`task_queue` table) para tareas de desarrollo sin requerir dependencias externas.
    2. Modo Producción / Servidor / Docker: Integración completa con Redis y Celery/ARQ para procesamiento distribuido.
* **Consecuencias:**
  * Desarrollo local fluido sin necesidad de instalar servicios externos adicionales en Windows.
  * Transición sin cambios de código al entorno contenerizado o servidor en producción.

---

### ADR-008: Seguridad, Privacidad y Cumplimiento Normativo (LFPDPPP)
* **Estado:** Aprobado
* **Contexto:**
  Los expedientes legales contienen datos personales sensibles (nombres, RFC, CURP, cuentas bancarias, hechos litigiosos).
* **Decisión:**
  * Inferencia de IA 100% confinada en `127.0.0.1:11434` (Ollama local). Cero envío de texto de expedientes a APIs de terceros públicas o no autorizadas.
  * Cifrado de contraseñas mediante algoritmo seguro `Argon2id` o `Bcrypt` con salt aleatorio.
  * Cero secretos o credenciales en el código fuente: uso obligatorio de archivos `.env` excluidos en `.gitignore` y lectura mediante `pydantic-settings`.
* **Consecuencias:**
  * Blindaje ante sanciones por violación a la Ley Federal de Protección de Datos Personales en Posesión de los Particulares (LFPDPPP) y garantía del Secreto Profesional del Abogado.
