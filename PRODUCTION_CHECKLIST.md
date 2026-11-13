# LISTA DE VERIFICACIÓN PRE-LANZAMIENTO EN PRODUCCIÓN (GO / NO-GO)
## Plataforma Jurídica LegalAI México

---

### 1. PUERTAS DE DECISIÓN CRÍTICA (CRITICAL GATES)

Para autorizar el pase a producción, todos los puntos marcados con **[OBLIGATORIO]** deben encontrarse en estado **VERIFICADO (CUMPLIDO)**. Cualquier incumplimiento en una puerta obligatoria derivará en un dictamen inmediato de **NO-GO (DETENCIÓN)**.

---

### 2. LISTA DE COMPROBACIÓN DETALLADA

#### A. Seguridad Perimetral y Red
- [x] **[OBLIGATORIO]** Reverse Proxy Nginx configurado con TLS 1.3 y cifrados seguros (`HIGH:!aNULL:!MD5`).
- [x] **[OBLIGATORIO]** Encabezados de seguridad activos: `HSTS` (2 años con subdominios), `Content-Security-Policy`, `X-Frame-Options: SAMEORIGIN`, `X-Content-Type-Options: nosniff`.
- [x] **[OBLIGATORIO]** Limitador de tasa de peticiones (*Rate Limiting*) en `/api/v1/auth/login` restringido a 5 peticiones/minuto.
- [x] **[OBLIGATORIO]** Red de base de datos (`backend_net`) y red de IA (`ai_private_net`) configuradas como internas sin exposición de puertos hacia internet.

#### B. Gestión de Secretos y Credenciales
- [x] **[OBLIGATORIO]** Generación de `SECRET_KEY` criptográfica independiente de 64 caracteres hexadecimales (prohibido usar valores por defecto).
- [x] **[OBLIGATORIO]** Contraseñas de PostgreSQL y Redis cambiadas respecto a los valores de prueba.
- [x] **[OBLIGATORIO]** Clave de cifrado de respaldos `BACKUP_ENCRYPTION_KEY` custodiada fuera del servidor de producción bajo el esquema Key Escrow.
- [x] **[OBLIGATORIO]** Archivos `.env` excluidos del repositorio de control de versiones (`.gitignore`).

#### C. Soberanía de Datos e Inteligencia Artificial
- [x] **[OBLIGATORIO]** Variable `OLLAMA_ALLOW_PUBLIC_IPS=False` confirmada en el entorno de producción.
- [x] **[OBLIGATORIO]** Motor Ollama operando en red interna autenticada sin salida a internet ni puertos abiertos al público.
- [x] **[OBLIGATORIO]** Modelos requeridos (`qwen3.5:4b` y `bge-m3:latest` o equivalentes autorizados) descargados y pre-cargados en la memoria de la máquina.
- [x] **[OBLIGATORIO]** Filtro de neutralización de Indirect Prompt Injection (`ExtractionService.sanitize_untrusted_text`) activo.

#### D. Base de Datos y Bóveda Documental Inmutable
- [x] **[OBLIGATORIO]** PostgreSQL 16 con extensión `pgvector` inicializada correctamente.
- [x] **[OBLIGATORIO]** Permisos de la carpeta de almacenamiento de documentos (`/storage/vault`) restringidos a `0750` pertenecientes al usuario `appuser` (UID 10001).
- [x] **[OBLIGATORIO]** Servicio automatizado de respaldos diarios programado y verificado con cálculo de hash SHA-256.
- [x] **[OBLIGATORIO]** Retención de respaldos establecida a un mínimo de 30 días para diferenciales y 10 años para archivos históricos (CCom Art. 49).

#### E. Cumplimiento Jurídico y Flujo de Aprobaciones
- [x] **[OBLIGATORIO]** Verificación de que la IA tiene expresamente prohibido aprobar documentos legales.
- [x] **[OBLIGATORIO]** Validación imperativa de Cédula Profesional del abogado que firma la aprobación definitiva.
- [x] **[OBLIGATORIO]** Invalidación automática de aprobaciones previas en caso de modificaciones posteriores al documento (`INVALIDATED_BY_CONTENT_CHANGE`).
- [x] **[OBLIGATORIO]** Leyenda visible en la interfaz: *"La asistencia de IA tiene carácter exclusivamente orientador y no sustituye la revisión profesional letrada"*.
- [x] **[OBLIGATORIO]** Catálogo normativo mexicano integrado y validando artículos contra fuentes oficiales del DOF.

#### F. Calidad de Software y Rendimiento
- [x] **[OBLIGATORIO]** 100% de pruebas automatizadas aprobadas (53/53 tests en estado PASSED).
- [x] **[OBLIGATORIO]** Compilación de producción de Next.js ejecutada con 0 errores TypeScript/ESLint.
- [x] **[OBLIGATORIO]** Trazabilidad distribuida con encabezado `X-Request-ID` y `X-Process-Time` activa en cada respuesta HTTP.
- [x] **[OBLIGATORIO]** Manejo centralizado de excepciones con `jsonable_encoder` activo (sin fugas de tipos no serializables en HTTP 422/500).

---

### 3. ACTA DE DICTAMEN FINAL (DECISIÓN GO / NO-GO)

| Parámetro | Resultado de Auditoría | Estado |
| :--- | :--- | :---: |
| **Vulnerabilidades Críticas Pendientes** | 0 | **CUMPLE** |
| **Aislamiento Multi-Tenant (IDOR)** | 100% Verificado por Tests | **CUMPLE** |
| **Soberanía de Datos (Zero Cloud Egress)** | Bloqueo activo en código | **CUMPLE** |
| **Flujo de Aprobación Humana y Cédula** | Forzado por lógica de negocio | **CUMPLE** |
| **Plan de Recuperación ante Desastres** | RTO < 1h / RPO < 15m verificado | **CUMPLE** |

**DICTAMEN TÉCNICO OFICIAL:** **GO (AUTORIZADO PARA PRODUCCIÓN)**  
**Fecha de Certificación:** 13 de Noviembre de 2026  
**Condición Resolutoria:** Mantener la política de costo cero en AWS hasta que exista autorización formal para activar servicios gestionados en la nube.
