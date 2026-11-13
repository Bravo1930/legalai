# Guía Integral de Despliegue e Infraestructura Híbrida
## LegalAI México • Plataforma Jurídica Empresarial

Este documento establece las directrices de arquitectura, configuración y despliegue para operar la plataforma en tres modalidades: **PC Local de Desarrollo**, **Servidor Privado On-Premises** y **Despliegue Híbrido en AWS**.

---

## 1. Topologías de Despliegue Soportadas

```mermaid
flowchart TD
    subgraph Local["1. PC Local (Desarrollo & Diagnóstico)"]
        L_OLLAMA["Ollama Local (NVIDIA GPU 6GB)"]
        L_BACKEND["FastAPI Backend (127.0.0.1:8000)"]
        L_FRONTEND["Next.js UI (localhost:3001)"]
        L_DB["PostgreSQL 16 + pgvector"]
        L_REDIS["Redis Local (o Fallback DB)"]
        L_WORM["Almacenamiento Local WORM"]

        L_FRONTEND --> L_BACKEND
        L_BACKEND --> L_DB
        L_BACKEND --> L_REDIS
        L_BACKEND --> L_OLLAMA
        L_BACKEND --> L_WORM
    end

    subgraph Private["2. Servidor Privado On-Premises (Soberano)"]
        P_NGINX["Nginx TLS 1.3 Reverse Proxy (:443)"]
        P_FRONTEND["Contenedor Next.js Standalone (:3000)"]
        P_BACKEND["Contenedor FastAPI Multi-Worker (:8000)"]
        P_WORKER["Trabajador Asíncrono (OCR & Pipeline)"]
        P_DB["PostgreSQL 16 (pgdata_prod)"]
        P_REDIS["Redis 7 con Contraseña"]
        P_BACKUP["Servicio de Respaldo Cifrado Diario"]
        P_GPU["Ollama GPU en Red Interna Aislada"]

        P_NGINX --> P_FRONTEND
        P_NGINX --> P_BACKEND
        P_BACKEND --> P_DB
        P_BACKEND --> P_REDIS
        P_BACKEND --> P_GPU
        P_WORKER --> P_DB
        P_WORKER --> P_REDIS
        P_WORKER --> P_GPU
        P_BACKUP --> P_DB
    end

    subgraph Hybrid["3. Despliegue Híbrido AWS + GPU Privada"]
        AWS_ALB["AWS Application Load Balancer"]
        AWS_ECS["AWS ECS Fargate (Frontend & Backend)"]
        AWS_RDS["AWS RDS PostgreSQL 16 (Multi-AZ + KMS)"]
        AWS_ELASTI["AWS ElastiCache Redis (TLS + Auth)"]
        AWS_S3["AWS S3 WORM Vault (Object Lock + SSE-KMS)"]
        AWS_VPN["Túnel Seguro AWS Site-to-Site VPN / Direct Connect"]
        ON_PREM_GPU["Servidor On-Premises GPU Privado (Ollama mTLS)"]

        AWS_ALB --> AWS_ECS
        AWS_ECS --> AWS_RDS
        AWS_ECS --> AWS_ELASTI
        AWS_ECS --> AWS_S3
        AWS_ECS -- "Inferencia Privada Cifrada" --> AWS_VPN --> ON_PREM_GPU
    end
```

---

## 2. Modalidad 1: PC Local (Desarrollo & Piloto)

### Requisitos de Hardware y Software
- **Sistema Operativo:** Windows 10/11 64-bit, Ubuntu 22.04 LTS o macOS (Apple Silicon).
- **Procesador:** 4 núcleos mínimo (8 núcleos recomendado).
- **Memoria RAM:** 16 GB mínimo.
- **GPU:** NVIDIA RTX 3050 Laptop (4GB-6GB VRAM) o superior con CUDA 12.x instalado.
- **Software:** Python 3.11+, Node.js 20+, PostgreSQL 16 con extensión `pgvector`, Ollama v0.3+.

### Puesta en Marcha Local
1. **Configurar el entorno virtual de Python:**
   ```powershell
   python -m venv backend\.venv
   & "backend\.venv\Scripts\Activate.ps1"
   pip install -r backend\requirements.txt
   ```

2. **Verificar los modelos de Ollama:**
   ```powershell
   ollama list
   # Deben estar descargados al menos:
   # qwen3.5:4b (LLM de análisis) y bge-m3:latest (Embeddings)
   ```

3. **Iniciar el Backend FastAPI:**
   ```powershell
   $env:PYTHONPATH="backend"
   & "backend\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

4. **Iniciar el Frontend Next.js:**
   ```powershell
   npm --prefix frontend install
   npm --prefix frontend run dev -- -p 3001
   ```

5. **Acceso:** Navegar a `http://localhost:3001` con las credenciales de administrador de despacho.

---

## 3. Modalidad 2: Servidor Privado On-Premises (Producción Soberana)

Esta modalidad garantiza el **100% de residencia de datos dentro de las instalaciones del despacho**, idóneo para bufetes con estrictas políticas de secreto fiduciario.

### Estructura de Contenedores en `docker-compose.prod.yml`
- **`nginx`:** Terminación TLS 1.3 con certificados de la firma, rate limiting de 5 req/min en login y bloqueo de accesos a puertos internos.
- **`frontend`:** Contenedor compilado en modo `standalone` de Next.js, ejecutándose bajo el usuario sin privilegios `nextjs` (UID 1001).
- **`backend`:** Contenedor FastAPI con múltiples workers Uvicorn bajo el usuario seguro `appuser` (UID 10001).
- **`worker`:** Contenedor asíncrono para pipeline de OCR y extracción.
- **`db`:** PostgreSQL 16 con extensión `pgvector`, aislado en la red interna `backend_net`.
- **`redis`:** Redis 7 con autenticación por contraseña (`requirepass`).
- **`db_backup`:** Daemon de respaldo automático que ejecuta cada noche a las 02:00 AM un volcado comprimido y cifrado con **AES-256-CBC**.

### Pasos de Despliegue en Servidor Privado
1. **Copiar variables de entorno:**
   ```bash
   cp .env.production.example .env
   # Editar .env con contraseñas robustas y claves aleatorias
   ```

2. **Colocar certificados SSL/TLS:**
   ```bash
   mkdir -p nginx/certs
   # Colocar fullchain.pem y privkey.pem en nginx/certs/
   ```

3. **Compilar y levantar los servicios:**
   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   ```

4. **Verificar el estado de salud:**
   ```bash
   docker compose -f docker-compose.prod.yml ps
   curl -k https://localhost/healthz
   ```

---

## 4. Modalidad 3: Despliegue Híbrido en AWS

> [!IMPORTANT]
> **REGLA DE COSTOS Y SOBERANÍA:** Ningún recurso de AWS debe ser aprovisionado sin autorización presupuestal explícita.
> La información confidencial de clientes **NUNCA se envía a modelos de lenguaje en la nube (OpenAI, Bedrock, Anthropic)**; en modo híbrido, la inferencia permanece confinada al servidor GPU privado mediante túnel VPN.

### Evaluación y Especificación de Servicios AWS

| Servicio AWS | Propósito en la Plataforma Legal | Configuración Recomendada | Nivel de Seguridad |
| :--- | :--- | :--- | :--- |
| **Amazon S3** | Bóveda inmutable WORM para contratos y demandas originales. | S3 Object Lock en modo *Compliance* (inmutable), SSE-KMS, Versioning activo, Bloqueo de acceso público (100%). | **Máximo** (Cumple Código de Comercio Art. 49). |
| **Amazon ECS (Fargate)** | Ejecución de contenedores de backend y frontend sin gestionar servidores EC2. | Tareas Fargate en subredes privadas, sin IP pública, orquestadas tras un Application Load Balancer. | **Alto** (Aislamiento a nivel de kernel). |
| **Amazon RDS PostgreSQL** | Base de datos relacional y búsqueda vectorial con `pgvector`. | PostgreSQL 16 Multi-AZ en subredes aisladas de base de datos, cifrado en reposo con AWS KMS, Automated Backups activos (35 días). | **Máximo** (Sin acceso desde internet). |
| **Amazon ElastiCache** | Cola de mensajería y caché de alto rendimiento. | Redis 7 con TLS en tránsito y Token de autenticación, desplegado en subredes privadas. | **Alto**. |
| **AWS KMS** | Llave maestra administrada por el cliente (CMK) para cifrar datos en S3 y RDS. | Política de llave restrictiva (`LegalAI-MasterKey`), rotación automática anual. | **Crítico**. |
| **AWS CloudWatch** | Centralización de logs de aplicación, alarmas de infraestructura y auditoría. | Log Groups cifrados con retención de 365 días para cumplimiento de auditoría forense. | **Alto**. |
| **AWS IAM** | Roles de ejecución de tareas con mínimo privilegio (`Least Privilege`). | `LegalAIEcsTaskRole` con permisos exclusivos a su bucket S3 específico y KMS. | **Crítico** (Cero llaves hardcodeadas). |

### Arquitectura de Red en AWS (3-Tier VPC)
1. **Subredes Públicas (DMZ):** Alojan únicamente el Application Load Balancer (ALB) con certificado de AWS Certificate Manager (ACM).
2. **Subredes Privadas de Aplicación:** Alojan las tareas de ECS Fargate (Backend FastAPI y Frontend Next.js). La salida a internet se realiza exclusivamente a través de NAT Gateway para actualizaciones de sistema.
3. **Subredes Aisladas de Datos:** Alojan RDS PostgreSQL y ElastiCache Redis. No tienen conexión ni rutas hacia internet.
4. **Túnel VPN hacia Servidor GPU Privado:** Un túnel **AWS Site-to-Site VPN** conecta la VPC de AWS con la red local del despacho donde opera el servidor con GPU NVIDIA y Ollama, utilizando autenticación mutua y cifrado IPsec IKEv2.

---

## 5. Matriz de Variables de Entorno de Producción

| Variable | Descripción | Valor por Defecto / Ejemplo |
| :--- | :--- | :--- |
| `ENVIRONMENT` | Entorno de ejecución de la plataforma | `production` |
| `DATABASE_URL` | Cadena de conexión PostgreSQL con SSL | `postgresql://user:pass@host:5432/legal_ai_db?sslmode=require` |
| `REDIS_URL` | Cadena de conexión Redis con contraseña | `redis://:pass@host:6379/0` (o `rediss://...` con TLS) |
| `OLLAMA_BASE_URL` | URL del servidor de inferencia de IA local/privado | `http://127.0.0.1:11434` o `https://gpu.internal:11434` |
| `OLLAMA_API_KEY` | Bearer token para proxy autenticado | Token secreto de al menos 32 caracteres |
| `OLLAMA_ALLOW_PUBLIC_IPS` | Candado anti-exfiltración a la nube | `false` (OBLIGATORIO en producción) |
| `STORAGE_BACKEND` | Tipo de almacenamiento inmutable | `local` (en disco) o `s3` (compatible AWS/MinIO) |
| `S3_BUCKET_NAME` | Nombre del bucket de bóveda WORM | `legal-ai-documents-vault-prod` |
| `S3_SERVER_SIDE_ENCRYPTION` | Algoritmo de cifrado en reposo | `AES256` o `aws:kms` |
| `S3_KMS_KEY_ID` | ARN de llave KMS de AWS | `arn:aws:kms:us-east-1:...` |
| `BACKUP_ENCRYPTION_KEY` | Contraseña simétrica para cifrar dumps | Llave AES-256 de 32 bytes |

---

## 6. Procedimiento de Verificación en Pruebas

Antes de certificar cualquier despliegue como apto para producción, se deben ejecutar obligatoriamente las siguientes tres pruebas de aceptación:

```bash
# 1. Validación de compilación del frontend sin errores de tipado
npm --prefix frontend run build

# 2. Batería completa de pruebas de backend (45 pruebas unitarias e integración)
pytest backend/tests -v

# 3. Diagnóstico integral de salud de la plataforma
curl -s http://127.0.0.1:8000/api/v1/health | jq .
```

Si las tres comprobaciones arrojan código de salida `0` y estado `"healthy"`, la plataforma se encuentra lista para recibir tráfico jurídico en producción.
