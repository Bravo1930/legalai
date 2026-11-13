# Arquitectura Técnica del Sistema LegalAI México

## 1. Visión General del Sistema

**LegalAI México** es una plataforma empresarial multi-inquilino (*multi-tenant*) de inteligencia artificial diseñada para la revisión, análisis, extracción y gestión integral de documentos jurídicos en la República Mexicana.

El sistema está concebido bajo el principio rector de **Human-in-the-Loop (HITL)**: *la inteligencia artificial actúa como asistente de copiloto jurídico de alta precisión; ninguna conclusión, recomendación, extracción o cambio documental surte efecto definitivo sin la aprobación explícita y trazable de un abogado facultado*.

---

## 2. Diagnóstico del Entorno de Ejecución Local

Con base en la inspección directa del host realizada por el equipo de ingeniería:

| Recurso | Especificación Detectada | Directriz Arquitectónica |
| :--- | :--- | :--- |
| **Sistema Operativo** | Windows 11 Pro (Build 10.0.26300) | Compatible con desarrollo local nativo y Docker Desktop. |
| **CPU** | AMD Ryzen 5 7535HS (6 núcleos, 12 hilos, 3.3–4.55 GHz) | Capacidad suficiente para pipelines de OCR, hashing SHA-256 concurrente y servidor web. |
| **Memoria RAM** | 16 GB DDR5 (Visible: 15.2 GB, Libre: ~4.3 GB) | Límite estricto: no se deben ejecutar modelos LLM en CPU que excedan 8 GB de RAM. |
| **GPU Dedicada** | NVIDIA GeForce RTX 4050 Laptop GPU (6 GB GDDR6, CUDA 12.7) | **Acelerador de IA primario**: Offload completo de modelos LLM ≤ 4B–7B y embeddings `bge-m3`. |
| **Almacenamiento** | Disco C (SSD NVMe): 622.6 GB libres de 952.8 GB | Almacenamiento local seguro para desarrollo y staging documental. |
| **Python** | Python 3.11.15 (`C:\Users\Asus\.local\bin\python3.11.exe`) | Versión estándar corporativa para backend FastAPI, PyTorch, SQLAlchemy y pgvector. |
| **Node.js / npm** | Node v22.23.1 / npm 10.9.8 | Runtime para frontend Next.js 14/15 con TypeScript. |
| **Ollama** | Ollama v0.40.16 en `127.0.0.1:11434` | Inferencia estrictamente en localhost. No expuesto a internet. Modelos verificados: `bge-m3` (embeddings), `qwen3.5:4b`, `qwen2.5-coder:7b`, `hermes3:8b`. |
| **PostgreSQL** | PostgreSQL 16 local (`localhost:5432`) | Servicio activo para persistencia relacional transaccional. |
| **Docker** | Docker CLI 29.6.1 (Demonio actualmente inactivo) | El sistema soportará ejecución local desacoplada y modo contenerizado completo. |

---

## 3. Diagrama de Arquitectura Global

```mermaid
flowchart TB
    subgraph ClientLayer ["Capa de Presentación (Frontend)"]
        UI["Next.js 14/15 + TypeScript\n(Tailwind CSS + Radix UI)"]
        State["Zustand / TanStack Query\n(Client State & Cache)"]
        UI <--> State
    end

    subgraph GatewayLayer ["Seguridad y API Gateway"]
        Nginx["Reverse Proxy / SSL Termination\n(Nginx / Traefik / API Gateway)"]
        CORS["CORS Policy & Rate Limiting"]
        Nginx --> CORS
    end

    subgraph BackendLayer ["Capa de Lógica de Negocio (Backend)"]
        FastAPI["FastAPI Application Server (Python 3.11)"]
        AuthMid["Auth & Tenant Context Middleware\n(JWT Bearer + RBAC)"]
        AuditMid["Append-Only Audit Middleware"]
        
        FastAPI --> AuthMid
        AuthMid --> AuditMid
        
        subgraph Services ["Servicios Especializados"]
            CaseSvc["Case & Dossier Service"]
            DocSvc["Document & Versioning Service"]
            OCRSvc["OCR & Text Extraction Service"]
            RAGSvc["Mexican Law RAG Service"]
            ReviewSvc["Legal Review & HITL Engine"]
        end
        
        AuditMid --> Services
    end

    subgraph AsyncQueue ["Procesamiento Asíncrono"]
        Redis["Redis 7 (Broker / Cache)"]
        Workers["Python Task Workers\n(OCR, Chunking, Ingestion)"]
        Redis <--> Workers
    end

    subgraph StorageLayer ["Capa de Almacenamiento Inmutable"]
        LocalStorage["Local Storage (Dev/Test)"]
        S3Storage["AWS S3 / MinIO (Prod/SaaS)\n(WORM: Write Once, Read Many)"]
    end

    subgraph DatabaseLayer ["Capa de Persistencia y Vectores"]
        PG["PostgreSQL 16 (ACID Relational)\n- Tenants & Users\n- Legal Metadata & Cases\n- Audit Trail (Immutable)"]
        PGV["pgvector Extension\n- Legal Embeddings (bge-m3: 1024-dim)\n- HNSW Index (Cosine Similarity)"]
        PG --- PGV
    end

    subgraph AIEngine ["Motor de Inferencia Local (Zero Exfiltration)"]
        OllamaLocal["Ollama Service (127.0.0.1:11434)\nGPU: NVIDIA RTX 4050 (6GB VRAM)"]
        BGE["Embeddings: bge-m3 (1.15 GB)"]
        LLM["Inference: qwen3.5:4b / qwen2.5-coder:7b"]
        OllamaLocal --- BGE
        OllamaLocal --- LLM
    end

    ClientLayer <--> GatewayLayer
    GatewayLayer <--> FastAPI
    DocSvc --> StorageLayer
    DocSvc --> AsyncQueue
    OCRSvc --> AsyncQueue
    RAGSvc <--> PGV
    RAGSvc <--> BGE
    ReviewSvc <--> LLM
    Services <--> PG
```

---

## 4. Estrategia de Aislamiento Multi-Tenant (Despachos Jurídicos)

El bufete de abogados inicial y los futuros clientes de la versión SaaS operan bajo un esquema de **Aislamiento Lógico Estricto con Particionamiento Tenant-Aware**:

1. **Identificador Canónico (`tenant_id`):**
   * Cada registro en las tablas operativas (`cases`, `documents`, `document_versions`, `ai_analyses`, `legal_validations`, `audit_logs`) contiene una clave foránea obligatoria `tenant_id` con índice B-Tree.
2. **Middleware de Inyección de Contexto:**
   * En FastAPI, cada solicitud entrante es interceptada por el `TenantContextMiddleware`.
   * El `tenant_id` se extrae de los claims verificados del token JWT firmado criptográficamente (HMAC-SHA256 con clave secreta rotativa o asimétrica RS256).
   * Se almacena en una variable de contexto asíncrona (`contextvars.ContextVar`), asegurando que ninguna función de base de datos pueda consultar datos sin filtrar implícita o explícitamente por el `tenant_id` activo.
3. **Seguridad a Nivel de Fila (PostgreSQL Row-Level Security - RLS):**
   * Se habilitará RLS en PostgreSQL:
     ```sql
     ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
     CREATE POLICY tenant_isolation_policy ON documents
     USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
     ```
4. **Aislamiento en Almacenamiento de Archivos:**
   * La estructura de almacenamiento de objetos separa estrictamente las rutas:
     `storage://tenants/{tenant_id}/cases/{case_id}/documents/{document_id}/{sha256_hash}.pdf`
   * Los enlaces de descarga son URLs prefirmadas temporales con expiración máxima de 15 minutos, accesibles únicamente tras validación de sesión y permisos.

---

## 5. Estrategia de Comunicación: PC Local, Servidor Privado y AWS

La arquitectura está concebida bajo un modelo **Híbrido de 3 Niveles** (*Three-Tier Hybrid Deployment*) para permitir el ciclo completo desde desarrollo local hasta despliegue corporativo en servidor privado on-premise o nube AWS:

```mermaid
flowchart LR
    subgraph Env1 ["Nivel 1: PC Local (Desarrollo y Testing)"]
        DevFastAPI["FastAPI (Local Python 3.11)"]
        DevPG["PostgreSQL 16 Local"]
        DevOllama["Ollama Local (RTX 4050 6GB)"]
        DevStorage["Local Disk /storage"]
        DevFastAPI --> DevPG
        DevFastAPI --> DevOllama
        DevFastAPI --> DevStorage
    end

    subgraph Env2 ["Nivel 2: Servidor Privado del Despacho (On-Premise)"]
        SrvCompose["Docker Compose Stack"]
        SrvFastAPI["FastAPI Container"]
        SrvOllama["Ollama Dedicated GPU Node"]
        SrvPG["PostgreSQL + pgvector Container"]
        SrvMinIO["MinIO S3-Compatible Storage"]
        SrvCompose --> SrvFastAPI
        SrvFastAPI --> SrvOllama
        SrvFastAPI --> SrvPG
        SrvFastAPI --> SrvMinIO
    end

    subgraph Env3 ["Nivel 3: AWS Cloud (Producción SaaS Multi-Despacho)"]
        AWSALB["AWS Application Load Balancer"]
        AWSECS["AWS ECS / Fargate (Backend FastAPI)"]
        AWSRDS["AWS RDS PostgreSQL + pgvector"]
        AWSS3["AWS S3 Bucket (SSE-KMS Encryption)"]
        AWSEC2GPU["AWS EC2 G5 / G6 Instance (Ollama Cluster)"]
        AWSALB --> AWSECS
        AWSECS --> AWSRDS
        AWSECS --> AWSS3
        AWSECS --> AWSEC2GPU
    end
```

### Protocolo de Interconexión y Gobernanza:
* **Entorno 1 (PC Local):** Funciona 100% desconectado de internet o de servidores externos para garantizar cero filtraciones durante el desarrollo.
* **Entorno 2 (Servidor Privado / On-Premise):** Ideal para despachos con políticas estrictas de secreto profesional (Art. 16 Constitucional, Secreto Profesional del Abogado y Ley Federal de Protección de Datos Personales en Posesión de Particulares - LFPDPPP). Todo el ciclo de vida documental y la inferencia de IA residen dentro de la red local del despacho (LAN/VLAN).
* **Entorno 3 (Nube AWS Multi-Despacho):**
  * Comunicación cifrada en tránsito obligatoria (TLS 1.3).
  * Reposo: Cifrado con AWS KMS con llaves independientes por despacho (*Bring Your Own Key - BYOK*).
  * Inferencia de IA: Instancias EC2 dedicadas con GPU (G5 con NVIDIA A10G) en subredes privadas sin IP pública ni acceso directo a internet, comunicadas exclusivamente mediante VPC Peering / PrivateLink con el backend FastAPI.

---

## 6. Arquitectura RAG Especializada en Jurisdicción Mexicana

Para cumplir con la directriz de **no inventar leyes, jurisprudencias ni citas**, el motor RAG estructura la información bajo los cánones del sistema jurídico mexicano:

```mermaid
flowchart TD
    DocIn["Documento Jurídico / Consulta"] --> LegalChunker["Chunker Semántico Jurídico\n(Estructurado por Capítulos, Artículos, Cláusulas o Considerandos)"]
    LegalChunker --> MetaEnricher["Enriquecedor de Metadatos Normativos\n- Jurisdicción (Federal / Estatal / CDMX)\n- Materia (Amparo, Civil, Mercantil, Penal, etc.)\n- Autoridad (SCJN Pleno/Salas, TCC, TFJA)\n- Época del SJF y Registro Digital\n- Vigencia y Ámbito Temporal"]
    MetaEnricher --> Embedder["Generador de Embeddings\n(bge-m3:latest en Ollama Local)"]
    Embedder --> VectorDB["PostgreSQL 16 + pgvector\n(Tabla: mexican_legal_corpus)"]
    
    subgraph RetrievalLoop ["Ciclo de Recuperación Estricta"]
        UserQuery["Pregunta / Cláusula a Revisar"] --> QueryEmbed["Embedding de Consulta"]
        QueryEmbed --> HybridSearch["Búsqueda Híbrida:\n1. Similaridad Vectorial Coseno (HNSW)\n2. Búsqueda Textual Full-Text en Español (tsvector / BM25)"]
        HybridSearch --> ContextFilter["Filtrado por Metadato:\nVigente = TRUE & Materia = Requerida"]
        ContextFilter --> PromptEngine["Prompt Guard:\n- Prohibición de responder sin contexto\n- Obligación de citar Registro Digital / Artículo exacto\n- Formato estructurado JSON"]
        PromptEngine --> LocalLLM["Ollama Local: qwen3.5:4b / qwen2.5-coder:7b"]
        LocalLLM --> HITLValidation["Bandeja de Validación de Abogado (HITL)"]
    end
    
    VectorDB <--> HybridSearch
```

---

## 7. Principio de Inmutabilidad Documental y Human-in-the-Loop (HITL)

```mermaid
stateDiagram-v2
    [*] --> Recibido: Carga de Archivo (PDF/DOCX)
    Recibido --> AlmacenadoInmutable: Cálculo SHA-256 + Guardado WORM
    AlmacenadoInmutable --> EnProcesamientoOCR: Disparo Tarea Asíncrona
    EnProcesamientoOCR --> TextoNormalizado: Extracción Completada
    TextoNormalizado --> AnalisisIAGenerado: Inferencia Ollama Local
    AnalisisIAGenerado --> PendienteRevisionHumana: Estado HITL Obligatorio
    
    state PendienteRevisionHumana {
        [*] --> EnRevisionPorAbogado
        EnRevisionPorAbogado --> ObservacionesAgregadas: Abogado agrega notas/ajustes
        EnRevisionPorAbogado --> ModificacionesRequeridas: Abogado corrige redacción
    }
    
    PendienteRevisionHumana --> AprobadoDefinitivo: Firma y Cédula de Abogado Senior
    PendienteRevisionHumana --> Rechazado: Descartado por Abogado
    
    AprobadoDefinitivo --> NuevaVersionGenerada: Se crea DocumentVersion (v2)
    NuevaVersionGenerada --> [*]
    Rechazado --> [*]
```

### Reglas Criptográficas y de Auditoría:
1. El archivo binario original se almacena bajo su hash `SHA-256`. Su registro en base de datos es inmutable (`is_original = true`, `is_locked = true`).
2. Cualquier sugerencia de cambio generada por la IA se guarda en la tabla `ai_suggestions` con un campo diff (formato JSON RFC 6902 / diff visual unificado).
3. La tabla `legal_validations` registra:
   * `validator_user_id`: ID del abogado.
   * `professional_license`: Cédula profesional del abogado.
   * `validation_status`: `APPROVED_AS_IS`, `APPROVED_WITH_MODIFICATIONS`, `REJECTED`.
   * `timestamp`: Fecha y hora UTC con zona horaria de México (America/Mexico_City).
   * `audit_hash`: Firma criptográfica del dictamen.
