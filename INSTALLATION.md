# Guía de Instalación, Configuración y Despliegue
## Plataforma LegalAI México

Esta guía documenta los procedimientos oficiales para configurar, ejecutar y verificar la plataforma en entorno de desarrollo local (Windows/Linux), servidor privado on-premise y contenedor Docker.

---

## 1. Requisitos Previos del Sistema

| Componente | Requisito Mínimo | Estado en Entorno Verificado |
| :--- | :--- | :--- |
| **Sistema Operativo** | Windows 10/11 x64 o Linux Ubuntu 22.04+ | Windows 11 Pro |
| **Python** | Python 3.11.x (Obligatorio por compatibilidad IA) | Python 3.11.15 (`C:\Users\Asus\.local\bin\python3.11.exe`) |
| **Node.js** | Node.js v20.x o v22.x | Node.js v22.23.1 con npm 10.9.8 |
| **Base de Datos** | PostgreSQL 16 (con soporte para pgvector) | PostgreSQL 16 en puerto 5432 |
| **Ollama Local** | Ollama v0.40+ con modelos descargados | Ollama en `127.0.0.1:11434` con `bge-m3:latest` y `qwen3.5:4b` |
| **GPU (Recomendada)**| NVIDIA con soporte CUDA (≥ 4 GB VRAM) | NVIDIA GeForce RTX 4050 Laptop GPU (6 GB VRAM) |

---

## 2. Variables de Entorno (`.env`)

El archivo `.env` en la raíz del proyecto controla todos los parámetros del sistema. Se proporciona una plantilla completa en `.env.example`.

```bash
# Copiar plantilla base si es una nueva instalación
cp .env.example .env
```

Parámetros clave configurados para el entorno local:
```ini
ENVIRONMENT=development
DATABASE_URL=postgresql://postgres@localhost:5432/legal_ai_db
REDIS_URL=redis://localhost:6379/0
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_EMBEDDING_MODEL=bge-m3:latest
OLLAMA_LLM_MODEL=qwen3.5:4b
```

---

## 3. Modo 1: Ejecución Local Nativa (Recomendada para Desarrollo Rápido)

### Paso A: Base de Datos PostgreSQL
1. Asegurarse de que el servicio de PostgreSQL esté en ejecución:
   ```powershell
   Get-Service -Name *postgres*
   ```
2. Crear la base de datos `legal_ai_db` si no existe:
   ```powershell
   & "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -p 5432 -c "CREATE DATABASE legal_ai_db;"
   ```

### Paso B: Backend FastAPI y Entorno Virtual Python 3.11
1. Crear el entorno virtual e instalar dependencias:
   ```powershell
   & "C:\Users\Asus\.local\bin\python3.11.exe" -m venv backend\.venv
   & "backend\.venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
   ```
2. Iniciar el servidor backend FastAPI:
   ```powershell
   $env:PYTHONPATH="backend"
   & "backend\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   * El backend inicializa automáticamente las tablas en PostgreSQL y carga el seed inicial del despacho demo.
   * Documentación interactiva Swagger: [http://127.0.0.1:8000/api/v1/docs](http://127.0.0.1:8000/api/v1/docs)
   * Endpoint de salud: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

### Paso C: Trabajador Asíncrono (Worker)
En una terminal secundaria:
```powershell
$env:PYTHONPATH="backend"
& "backend\.venv\Scripts\python.exe" -m app.workers.worker
```
* Si Redis no está encendido, el worker procesa en modo sondeo transaccional desde PostgreSQL automáticamente.

### Paso D: Frontend Next.js con TypeScript
En una terminal adicional:
```powershell
cd frontend
npm install
npm run dev
```
* La aplicación web estará disponible en [http://localhost:3000](http://localhost:3000).

---

## 4. Modo 2: Despliegue con Docker y Docker Compose

Para despliegue contenerizado unificado (incluyendo PostgreSQL con `pgvector` oficial y Redis):

1. Iniciar Docker Desktop.
2. Ejecutar la pila completa de servicios:
   ```bash
   docker compose up --build -d
   ```
3. Verificar el estado de los contenedores:
   ```bash
   docker compose ps
   ```
4. Consultar logs del backend y workers:
   ```bash
   docker compose logs -f backend worker
   ```
5. Detener el sistema:
   ```bash
   docker compose down
   ```

---

## 5. Credenciales Iniciales de Demostración (Seed)

Al arrancar por primera vez, el backend provisiona automáticamente los datos base:

* **Despacho Jurídico:** `Bufete Jurídico México & Asociados`
* **Identificador de Despacho (Slug):** `despacho-demo`
* **Correo de Acceso:** `admin@legalai.mx`
* **Contraseña:** `Admin1234!`
* **Rol:** `SUPER_ADMIN`
* **Cédula Profesional:** `12345678`

---

## 6. Ejecución de la Suite de Pruebas Automatizadas

El backend incluye pruebas de integración y unitarias que validan la salud de los servicios, el flujo de autenticación, el hashing de contraseñas, la emisión de JWT y el aislamiento de despachos:

```powershell
$env:PYTHONPATH="backend"
& "backend\.venv\Scripts\python.exe" -m pytest "backend\tests" -v
```

Todas las pruebas se ejecutan contra la base de datos real con rollback o aislamiento sin datos confidenciales reales.
