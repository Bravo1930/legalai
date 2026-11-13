# PLAN DE RECUPERACIÓN ANTE DESASTRES Y CONTINUIDAD DEL NEGOCIO (DRP)
## Plataforma de Inteligencia Artificial Jurídica Documental LegalAI México

---

### 1. OBJETIVOS Y MÉTRICAS DE RECUPERACIÓN (SLA / RTO / RPO)

En el ámbito jurídico mexicano, la disponibilidad continua de expedientes, contratos y escritos judiciales con plazos perentorios procesales (términos fatales ante tribunales y autoridades) exige estándares estrictos de resiliencia técnica:

| Métrica | Objetivo Comprometido | Justificación Jurídica y Operativa |
| :--- | :--- | :--- |
| **RPO (Recovery Point Objective)** | **< 15 minutos** | Pérdida máxima admisible de datos. Salvaguardado mediante réplica continua y respaldos automatizados periódicos de transacciones y documentos recién cargados. |
| **RTO (Recovery Time Objective)** | **< 60 minutos** | Tiempo máximo admisible para restablecer la plataforma y permitir que los abogados continúen redactando, revisando y aprobando documentos procesales. |
| **MTTR (Mean Time to Repair)** | **< 30 minutos** | Detección automática y reinicio supervisado de servicios contenerizados (Docker / ECS). |
| **Retención Legal Mínima** | **10 Años** | Art. 49 del Código de Comercio de México y NOM-151-SCFI-2016 para mensajes de datos y contratos mercantiles. |

---

### 2. POLÍTICA Y MATRIZ DE RESPALDOS

El sistema implementa una estrategia de respaldos en tres capas (3-2-1): 3 copias de los datos, en 2 medios diferentes, con 1 copia fuera del sitio primario (offsite / cold storage).

```
   ┌────────────────────────────────────────────────────────┐
   │                Base de Datos y WORM                    │
   └──────────────────────────┬─────────────────────────────┘
                              │
            ┌─────────────────┴─────────────────┐
            ▼                                   ▼
    [Diario: Incremental]               [Semanal: Full]
   Retención: 30 Días                  Retención: 12 Meses
   Cifrado AES-256                     Cifrado AES-256 + SHA256
            │                                   │
            └─────────────────┬─────────────────┘
                              ▼
                   [Archivo Mensual / Anual]
                     Retención: 10 Años
               (Cumplimiento CCom Art. 49)
```

#### Calendario de Ejecución

1. **Respaldos de Base de Datos (PostgreSQL 16 + pgvector):**
   - **Frecuencia:** Diario a las 02:00 UTC (ejecutado por contenedor `db_backup` o cron del host).
   - **Formato:** Dump binario comprimido (`pg_dump -F c`), comprimido con `gzip` y cifrado simétricamente con `AES-256-CBC` (PBKDF2 100,000 iteraciones).
   - **Checksum:** Cálculo obligatorio de `SHA-256` registrado en archivo homónimo (`.sha256`) previo y posterior al cifrado.
   - **Rotación:** Retención automática de 30 días en disco local o bucket S3 con política de ciclo de vida (Glacier para archivos históricos).

2. **Respaldos de Almacenamiento Documental (WORM / S3):**
   - **Almacenamiento Local Privado:** Sincronización diaria unidireccional con flag de inmutabilidad (`chattr +i` o permisos de solo lectura a nivel sistema de archivos).
   - **Almacenamiento S3 / MinIO:** Object Lock en modo `COMPLIANCE` con retención legal y cifrado del lado del servidor `SSE-KMS` o `SSE-S3`.

---

### 3. GESTIÓN CRIPTOGRÁFICA Y CUSTODIA DE CLAVES (KEY ESCROW)

1. **Algoritmo de Cifrado:**
   - Cifrado en reposo: AES-256-CBC con derivación de clave mediante PBKDF2 y 100,000 rondas de hashing HMAC-SHA256.
2. **Custodia de Claves (Dual-Control Escrow):**
   - La variable `BACKUP_ENCRYPTION_KEY` nunca debe almacenarse en el mismo servidor donde residen los datos primarios ni en los archivos de respaldo.
   - En despliegues AWS, la clave se gestiona vía **AWS KMS** con clave gestionada por el cliente (CMK) con política de acceso restringida exclusivamente al rol IAM de restauración.
   - En despliegues en servidor privado on-premise, la clave maestra se divide mediante el esquema de Shamir o se almacena en bóveda de contraseñas de hardware (HSM / YubiKey) bajo custodia conjunta del Administrador de Seguridad y el Socio Director del despacho.

---

### 4. ESCENARIOS DE CONTINGENCIA Y RECUPERACIÓN

#### Escenario A: Caída o Falla de Estación Local de Trabajo (PC Developer / Single Node)
- **Impacto:** Interrupción en el equipo personal del abogado o desarrollador.
- **Acciones:**
  1. Clonar el repositorio en equipo de reemplazo:
     ```bash
     git clone <repositorio-legal-ai>
     cd "proyecto legal agy"
     ```
  2. Restaurar variables de entorno desde el almacén seguro de secretos.
  3. Ejecutar `./scripts/restore_db.ps1` o restaurar último dump con checksum verificado:
     ```powershell
     .\scripts\restore_db.ps1 -BackupFile .\backups\legal_ai_db_latest.dump -DbName legal_ai_db
     ```
  4. Iniciar servicios y verificar que Ollama detecte los modelos locales (`qwen3.5`, `bge-m3`).

#### Escenario B: Falla de Hardware en Servidor Privado On-Premise
- **Impacto:** El servidor central del despacho queda inoperable (falla de disco, placa base o corte prolongado de energía).
- **Acciones:**
  1. Activar el servidor secundario de reserva (Warm Standby).
  2. Descargar los respaldos cifrados `.sql.gz.enc` desde el almacenamiento off-site seguro.
  3. Ejecutar el script automatizado de restauración:
     ```bash
     ./scripts/restore_db.sh /backups/legal_ai_db_YYYYMMDD_HHMMSS.sql.gz.enc
     ```
  4. Sincronizar el directorio `/storage/documents` desde el respaldo inmutable.
  5. Levantar el stack de producción:
     ```bash
     docker compose -f docker-compose.prod.yml up -d
     ```
  6. Validar el estado del clúster mediante `curl http://localhost/api/v1/health`.

#### Escenario C: Desastre Catastrófico y Failover a Nube Híbrida (AWS)
- **Impacto:** Destrucción de instalaciones físicas locales (sismo, incendio o inundación).
- **Condición Estricta:** Cumplir en todo momento con la prohibición de enviar documentos confidenciales no cifrados a APIs públicas de IA.
- **Acciones:**
  1. Levantar entorno contenerizado en AWS ECS / Fargate o EC2 privada mediante plantilla de infraestructura codificada.
  2. Restaurar la base de datos PostgreSQL en Amazon RDS con extensión `pgvector` activada.
  3. Configurar el bucket S3 con Object Lock y restaurar los documentos cifrados con KMS.
  4. Conectar el backend a una instancia privada EC2 GPU (p. ej. `g5.xlarge`) dentro de la VPC privada ejecutando Ollama de manera estrictamente interna (sin IP pública ni acceso a internet), garantizando soberanía de datos y secreto profesional.
  5. Actualizar registros DNS privados hacia el Application Load Balancer de contingencia.

---

### 5. GUÍA PASO A PASO: PROTOCOLO DE RESTAURACIÓN (RUNBOOK)

A continuación se detalla el procedimiento operativo estandarizado para restaurar la plataforma ante un evento de contingencia:

#### Paso 1: Verificación de Integridad de la Copia de Seguridad
Antes de restaurar cualquier información, se debe comprobar que el archivo no haya sido manipulado o truncado:

En Linux / macOS:
```bash
cd /backups
sha256sum -c legal_ai_db_20261113_020000.sha256
# Debe responder: legal_ai_db_20261113_020000.sql.gz.enc: OK
```

En Windows PowerShell:
```powershell
Get-FileHash -Path .\backups\legal_ai_db_20261113_020000.dump -Algorithm SHA256
# Comparar visualmente o verificar contra el contenido de .sha256
```

#### Paso 2: Ejecución del Script de Restauración

En entornos Linux / Docker:
```bash
export POSTGRES_HOST=127.0.0.1
export POSTGRES_USER=postgres
export POSTGRES_DB=legal_ai_db
export BACKUP_ENCRYPTION_KEY="<CLAVE_AES256_PROVISTA_POR_CUSTODIO>"

./scripts/restore_db.sh /backups/legal_ai_db_20261113_020000.sql.gz.enc
```

En entornos Windows:
```powershell
.\scripts\restore_db.ps1 `
    -BackupFile ".\backups\legal_ai_db_20261113_020000.dump" `
    -DbName "legal_ai_db" `
    -DbUser "postgres" `
    -DbHost "localhost" `
    -DbPort 5432
```

#### Paso 3: Validación de Integridad Post-Restauración (Health Check Forense)

1. **Verificar extensiones y tablas en PostgreSQL:**
   ```sql
   -- Conectarse a psql y verificar extensión pgvector y tablas
   \c legal_ai_db;
   SELECT * FROM pg_extension WHERE extname = 'vector';
   SELECT count(*) FROM users;
   SELECT count(*) FROM documents;
   SELECT count(*) FROM legal_rules;
   SELECT count(*) FROM workflow_instances;
   ```

2. **Verificar servicio Ollama privado:**
   ```bash
   curl -s http://127.0.0.1:11434/api/tags | jq .
   # Confirmar presencia de modelos jurídicos requeridos
   ```

3. **Verificar endpoint de salud integral:**
   ```bash
   curl -s http://127.0.0.1:8000/api/v1/health | jq .
   ```
   Respuesta esperada:
   ```json
   {
     "status": "healthy",
     "version": "1.0.0",
     "database": "connected (PostgreSQL 16.x)",
     "ai_engine": {
       "status": "connected",
       "models_available": 8
     }
   }
   ```

4. **Verificar frontend y autenticación:**
   - Abrir navegador en la URL interna autorizada (`http://localhost:3001` o `https://legalai.despacho.local`).
   - Iniciar sesión con credenciales de Administrador y verificar acceso al dashboard.

---

### 6. SIMULACROS DE RECUPERACIÓN (DRILLS) Y AUDITORÍA

1. **Frecuencia de Simulacros:**
   - **Simulacro Semestral:** Restauración en un ambiente de pruebas sandbox aislado para verificar que los respaldos no presenten fallos de serialización, incompatibilidad de esquemas o claves corruptas.
2. **Registro de Bitácora de Auditoría:**
   - Toda prueba de recuperación debe documentarse en el registro forense con indicación de fecha, hora, RTO alcanzado, SHA-256 verificado y firma digital del responsable técnico.
3. **Revisión de Políticas:**
   - Actualización anual del presente manual ante reformas a las leyes procesales mexicanas, NOM-151 o cambios en la infraestructura de hardware del despacho.
