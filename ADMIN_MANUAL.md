# MANUAL DE ADMINISTRACIÓN Y OPERACIONES
## Plataforma de Inteligencia Artificial LegalAI México

---

### 1. INTRODUCCIÓN Y RESPONSABILIDADES DEL ADMINISTRADOR

Este manual está dirigido a los Administradores de Sistemas y Oficiales de Cumplimiento Técnico de despachos jurídicos. Sus facultades abarcan la gestión de la infraestructura, administración de usuarios y permisos, gobernanza de modelos de inteligencia artificial y ejecución de los planes de respaldo y recuperación ante desastres (DRP).

---

### 2. GESTIÓN DE DESPACHOS (TENANTS) Y AISLAMIENTO

#### 2.1. Creación de un Nuevo Despacho (Plano de Control)
Únicamente el usuario con rol `SUPER_ADMIN` tiene facultades para provisionar nuevas organizaciones mediante el endpoint `/api/v1/tenants`:
```bash
curl -X POST "http://localhost:8000/api/v1/tenants" \
     -H "Authorization: Bearer <SUPER_ADMIN_JWT>" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Bufete Jurídico González & Pérez S.C.",
       "slug": "gonzalez-perez",
       "rfc": "BGP180512KL9",
       "contact_email": "administracion@gonzalezperez.mx"
     }'
```

#### 2.2. Aislamiento de Almacenamiento en Disco
Cada despacho cuenta con su propia bóveda física aislada en `/storage/vault/{tenant_id}/documents/`. El administrador de sistemas debe asegurarse de que el usuario de ejecución (`appuser` UID 10001) cuente con permisos exclusivos de lectura/escritura (`chmod 0750`).

---

### 3. GESTIÓN DE USUARIOS Y ROLES (RBAC)

#### 3.1. Matriz de Roles y Facultades
| Rol | Ámbito de Acción | ¿Puede Aprobar Definitivamente? | ¿Ve Contratos Privados? |
| :--- | :--- | :---: | :---: |
| `SUPER_ADMIN` | Configuración de plataforma, alta de despachos y logs globales. | NO | **NO (Bloqueado por código)** |
| `MANAGING_PARTNER` | Socio Director del despacho. Todo el contenido y reglas de su despacho. | SÍ (Con Cédula) | SÍ |
| `SENIOR_LAWYER` | Abogado Senior. Casos, documentos, propuestas y dictámenes. | SÍ (Con Cédula) | SÍ |
| `ASSOCIATE_LAWYER`| Abogado Asociado. Análisis, redacción y revisiones asignadas. | SÍ (Con Cédula) | SÍ |
| `LEGAL_ASSISTANT` | Asistente Jurídico. Carga y etiquetado documental. | NO (Salvo dispensa expresa) | SÍ |

#### 3.2. Alta de Abogados y Cédulas Profesionales
Al crear o editar usuarios, es imperativo registrar la Cédula Profesional del abogado:
```bash
curl -X POST "http://localhost:8000/api/v1/users" \
     -H "Authorization: Bearer <MANAGING_PARTNER_JWT>" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "lic.valeria@despacho.com",
       "full_name": "Lic. Valeria Treviño Garza",
       "role": "SENIOR_LAWYER",
       "professional_license": "98765432",
       "password": "PasswordFuerte2026!"
     }'
```

---

### 4. GESTIÓN Y GOBERNANZA DEL MOTOR DE IA (OLLAMA LOCAL)

#### 4.1. Verificación de Modelos Instalados
El administrador debe comprobar los modelos disponibles en el servidor local o GPU autorizada:
```bash
# Consultar modelos en Ollama
ollama list

# Modelos mínimos recomendados para la plataforma:
# 1. Razonamiento jurídico: qwen3.5:4b o qwen2.5:7b / deepseek-r1:8b
# 2. Embeddings semánticos: bge-m3:latest
```

#### 4.2. Descarga de Nuevos Modelos
Para instalar un nuevo modelo sin exponer la plataforma:
```bash
ollama pull qwen3.5:4b
ollama pull bge-m3:latest
```

#### 4.3. Supervisión de la Política Zero-Cloud-Egress
El archivo de configuración `.env` en producción debe mantener estrictamente:
```env
OLLAMA_ALLOW_PUBLIC_IPS=False
OLLAMA_BASE_URL=http://ollama:11434
```
Si se detecta en los logs de la aplicación el error `Violación de política de soberanía de datos`, verifique que ninguna variable intente apuntar a proveedores comerciales de IA en la nube.

---

### 5. MOTOR DE REGLAS DETERMINISTAS

1. Acceda a la sección **"Reglas Internas"** en la interfaz administrativa.
2. Podrá crear reglas contractuales estándar para todos los contratos del despacho o asociarlas a un cliente específico.
3. Tipos de Operadores Soportados:
   - `CONTAINS_ALL_KEYWORDS`: Exige que todas las palabras clave estén presentes en el contrato (p. ej. "sumisión expresa", "tribunales de la ciudad de méxico").
   - `PROHIBITS_KEYWORDS`: Alerta si se detecta texto prohibido (p. ej. "renuncia a derechos laborales").
   - `REGEX_MATCH`: Evalúa expresiones regulares complejas para plazos de entrega, porcentajes de interés moratorio o límites de responsabilidad civil.
4. Cada modificación genera una nueva versión inmutable de la regla con firma del usuario autor.

---

### 6. EJECUCIÓN DE RESPALDOS Y RECUPERACIÓN ANTE DESASTRES

#### 6.1. Ejecución Manual de Respaldo Cifrado (Linux / Docker)
```bash
docker exec -it legal_ai_db_backup /scripts/backup_db.sh
```
El archivo resultante se almacenará en `./backups/legal_ai_db_YYYYMMDD_HHMMSS.sql.gz.enc` acompañado de su respectivo archivo de comprobación `.sha256`.

#### 6.2. Ejecución Manual de Respaldo en Servidor Windows (PowerShell)
```powershell
.\scripts\backup_db.ps1 -DbName "legal_ai_db" -DbUser "postgres" -BackupDir "C:\Backups\LegalAI"
```

#### 6.3. Protocolo de Restauración de Emergencia
Consulte el documento exhaustivo [DISASTER_RECOVERY.md](file:///C:/Users/Asus/proyecto%20legal%20agy/DISASTER_RECOVERY.md) para ejecutar la recuperación paso a paso validando previamente la suma de comprobación SHA-256.

---

### 7. AUDITORÍA FORENSE Y MONITOREO DE SEGURIDAD

1. Toda petición HTTP que ingresa a la plataforma se etiqueta con un identificador único `X-Request-ID`.
2. Las acciones críticas (inicio de sesión, descarga de documentos, emisión de aprobaciones y cambios de versión) se escriben en la tabla `audit_logs`.
3. Revise periódicamente la sección **"Auditoría"** en el panel administrativo o consulte los registros directamente:
```sql
SELECT created_at, action, resource_type, details 
FROM audit_logs 
ORDER BY created_at DESC 
LIMIT 50;
```
