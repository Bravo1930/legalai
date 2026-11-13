# DOCUMENTACIÓN TÉCNICA DE ARQUITECTURA
## Plataforma de Inteligencia Artificial Jurídica Documental LegalAI México

---

### 1. ARQUITECTURA GENERAL DEL SISTEMA

La plataforma LegalAI México adopta una arquitectura modular en capas diseñada para alta disponibilidad, aislamiento multi-tenant y estricto cumplimiento del secreto profesional.

```
                      [ NAVEGADOR WEB (USUARIO / ABOGADO) ]
                                       │
                                       ▼ HTTPS (TLS 1.3 / HSTS)
                           [ NGINX REVERSE PROXY ]
                         (Rate Limiting: 5 r/m en /auth)
                                       │
                ┌──────────────────────┴──────────────────────┐
                ▼                                             ▼
     [ FRONTEND NEXT.JS 14 ]                      [ BACKEND FASTAPI ]
      - TypeScript / Tailwind                     - Python 3.11 / AsyncIO
      - Visualizador Documental                   - ORM SQLAlchemy 2.0
      - Dashboard & Redline Viewer                - Inyección de Dependencias
                │                                             │
                │                                ┌────────────┴────────────┐
                ▼                                ▼                         ▼
     [ API Client (Bearer JWT) ]       [ POSTGRESQL 16 + PGVECTOR ]   [ REDIS BROKER ]
                                       - Bóveda Metadatos Relacional  - Tareas Celery
                                       - Búsqueda Semántica Vector    - Caché Sesiones
                                                 │
                                                 ▼
                                     [ SERVICIOS ESPECIALIZADOS ]
                                     ├── StorageService (WORM / S3)
                                     ├── ExtractionService (PyMuPDF/OCR)
                                     ├── Deterministic RuleEngine
                                     ├── ApprovalService (Cédula / HITL)
                                     └── Ollama Client (Zero-Cloud-Egress)
                                                 │
                                                 ▼
                                      [ MOTOR DE IA PRIVADO ]
                                      - Ollama en Red Interna
                                      - Inferencia Local / GPU On-Premise
                                      - 7 Agentes Jurídicos Autónomos
```

---

### 2. MODELO DE DATOS Y ENTIDADES (POSTGRESQL 16)

La base de datos relacional modela integralmente el ciclo de vida de los despachos jurídicos, expedientes, documentos inmutables y aprobaciones:

#### 2.1. Despachos y Usuarios
- **`tenants`:** Entidad raíz del esquema multi-inquilino. Almacena `id` (UUID), `name`, `slug`, `rfc`, `contact_email` y estatus de suscripción.
- **`users`:** Abogados y personal del despacho. Campos clave: `tenant_id`, `email`, `hashed_password` (bcrypt), `full_name`, `role` (Enum `LegalRoles`), `professional_license` (Cédula Profesional obligatoria para aprobaciones) y `is_active`.

#### 2.2. Clientes y Expedientes
- **`clients`:** Clientes patrocinados por el despacho. Almacena razón social/nombre, RFC, teléfono y `tenant_id`.
- **`cases`:** Expedientes judiciales o corporativos. Almacena `case_number`, juzgado/autoridad competente, materia jurídica, estado procesal y abogado asignado.

#### 2.3. Bóveda Documental Inmutable (WORM)
- **`documents`:** Registro principal del documento original inmutable. Almacena `tenant_id`, `case_id`, `client_id`, `sha256_hash`, `storage_path`, `file_size_bytes`, `mime_type`, `doc_type` (Enum `DocumentClassification`), `is_original` (booleano) y `page_count`.
- **`document_versions`:** Versiones derivadas o corregidas. Conserva el documento original intacto y almacena `version_number`, nuevo `sha256_hash`, `change_summary` y usuario autor.
- **`document_metadata`:** Metadatos extraídos por el pipeline automatizado: partes contratantes, fechas clave, obligaciones principales, montos económicos, plazos, comparecientes/firmantes, jurisdicción pactada y texto plano extraído (`raw_text`).

#### 2.4. Motor de Reglas y Análisis Avanzado
- **`legal_rules`:** Reglas deterministas configuradas por el despacho o cliente. Contiene `rule_code`, `name`, `category`, `severity`, `condition_definition` (JSON con operadores y parámetros), `scope` y `legal_foundation`.
- **`advanced_document_analyses`:** Sesión de análisis jurídico exhaustivo que agrupa las cláusulas descompuestas y los hallazgos.
- **`analysis_findings`:** Observación estructurada individual. Contiene `finding_type`, `severity` (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`), `clause_reference`, `verbatim_quote`, `statutory_foundation` y `human_review_status` (`PENDING`, `ACCEPTED`, `REJECTED`).

#### 2.5. Propuestas y Redlines
- **`modification_proposals`:** Propuesta de redacción alternativa sugerida por la IA o el revisor. Almacena texto original, texto propuesto, explicación del beneficio jurídico, estado (`PENDING`, `ACCEPTED`, `REJECTED`) y comentarios del abogado.

#### 2.6. Workflows y Aprobaciones
- **`document_workflows`:** Estado procesal del documento en la máquina de 11 estados (`current_state`, abogado asignado, revisor asignado, fecha límite).
- **`workflow_transitions`:** Historial de transiciones con fecha, usuario causante y motivo.
- **`workflow_approval_records`:** Certificación formal de aprobación legal. Almacena `version_number`, `document_hash` (SHA-256), `scope` (`DEFINITIVE_APPROVAL`), `reviewer_license` (Cédula Profesional), `status` (`VALID` o `INVALIDATED_BY_CONTENT_CHANGE`) y fecha.
- **`workflow_comments`:** Observaciones internas y solicitudes de corrección.
- **`workflow_notifications`:** Alertas operativas dirigidas a los integrantes del equipo jurídico.

#### 2.7. Trazabilidad Forense
- **`audit_logs`:** Registro inmutable de eventos. Almacena `tenant_id`, `user_id`, `action`, `resource_type`, `resource_id`, `details` (JSON) y `created_at`.

---

### 3. CATÁLOGO DE APIS Y ENDPOINTS (`/api/v1`)

| Prefijo | Módulo | Responsabilidad Principal |
| :--- | :--- | :--- |
| `/health` | Diagnóstico | Estado del sistema, versión, conexión a PostgreSQL 16 y motor Ollama. |
| `/auth` | Autenticación | Inicio de sesión OAuth2, emisión de JWT y perfil de usuario (`/me`). |
| `/tenants` | Despachos | Administración del plano de control de despachos (exclusivo SuperAdmin). |
| `/users` | Usuarios | Registro, consulta y asignación de roles y cédulas de abogados. |
| `/tasks` | Tareas Asíncronas | Consulta de estado y progreso de tareas encoladas en Celery. |
| `/clients` | Clientes | CRUD de clientes del despacho con aislamiento multi-tenant. |
| `/cases` | Expedientes | Gestión de asuntos y expedientes judiciales. |
| `/documents` | Gestor Documental | Carga WORM, validación binaria, descarga autorizada y versionado. |
| `/ai` | Agentes Ollama | Catálogo de modelos locales, inferencia con agentes y streaming. |
| `/rules` | Motor de Reglas | Creación, versionado y evaluación determinista de reglas por despacho. |
| `/advanced-analysis` | Análisis Avanzado | Descomposición de cláusulas, detección de riesgos y revisión HITL. |
| `/modifications` | Propuestas | Generación de cláusulas alternativas, redlines y exportación DOCX/PDF. |
| `/workflow` | Flujos Jurídicos | Máquina de estados, asignación de equipo, comentarios y aprobaciones. |
| `/analytics` | Dashboard | Métricas de carga por abogado, tiempos de ciclo y resumen de riesgos. |
| `/audit` | Auditoría Forense | Consulta de bitácora de actividad inmutable para cumplimiento. |

---

### 4. PIPELINE DE EXTRACCIÓN Y BLINDAJE DE IA

El procesamiento de documentos sigue un flujo determinista y seguro:

1. **Ingesta y Validación Binaria (`StorageService`):**
   - Comprobación de tamaño máximo (50 MB).
   - Detección de tipo MIME mediante *Magic Bytes* (firmas binarias `%PDF-`, `PK\x03\x04`, etc.) para impedir evasión por cambio de extensión.
   - Cálculo criptográfico de la suma de comprobación SHA-256.
   - Persistencia inmutable en almacenamiento local o S3.

2. **Extracción y Neutralización de Inyecciones (`ExtractionService`):**
   - Extracción de texto estructurado página por página con PyMuPDF.
   - Si la densidad de texto es inferior a 50 caracteres por página, se invoca automáticamente el motor Tesseract OCR en español (`spa`).
   - El texto extraído se procesa con `sanitize_untrusted_text` para redactar cualquier instrucción maliciosa de Indirect Prompt Injection (`ignore instructions`, `developer mode`, etc.).

3. **Inferencia Asistida y Delimitación de Contexto (`BaseLegalAgent`):**
   - El texto sanitizado se encapsula dentro del bloque `<DOCUMENT_CONTENT>` indicando al LLM que es información de solo lectura.
   - Parámetros de inferencia: `temperature=0.1`, formato forzado en JSON Schema estricto.
   - Invocación al endpoint privado de Ollama validado por la política *Zero-Cloud-Egress*.

4. **Validación Normativa (`MexicanLawVerifier`):**
   - Toda cita legal generada se coteja contra el catálogo oficial de leyes mexicanas (Código Civil, Código de Comercio, LFT, LFPDPPP).
   - Se comprueba la vigencia y la existencia real del número de artículo en la ley citada.
