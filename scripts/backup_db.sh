#!/bin/sh
# ==============================================================================
# LEGALAI MÉXICO - SCRIPT AUTOMATIZADO DE RESPALDO CIFRADO DE POSTGRESQL
# ==============================================================================
# - Dump integral de PostgreSQL con pg_dump
# - Compresión gzip
# - Cifrado simétrico AES-256-CBC con OpenSSL
# - Generación de checksum SHA-256
# - Rotación automática de respaldos (retención de 30 días)
# ==============================================================================

set -e

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR=${BACKUP_DIR:-"/backups"}
DB_HOST=${POSTGRES_HOST:-"db"}
DB_USER=${POSTGRES_USER:-"postgres"}
DB_NAME=${POSTGRES_DB:-"legal_ai_db"}
ENC_KEY=${BACKUP_ENCRYPTION_KEY:-"default_aes_key_change_in_production"}
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

mkdir -p "$BACKUP_DIR"

RAW_DUMP="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql.gz"
ENCRYPTED_BACKUP="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql.gz.enc"
CHECKSUM_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sha256"

echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Iniciando respaldo de base de datos '${DB_NAME}'..."

# 1. Ejecución de pg_dump con compresión
pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" --format=custom | gzip > "$RAW_DUMP"

# 2. Cifrado simétrico AES-256-CBC
openssl enc -aes-256-cbc -salt -pbkdf2 -iter 100000 -in "$RAW_DUMP" -out "$ENCRYPTED_BACKUP" -k "$ENC_KEY"

# 3. Eliminar dump sin cifrar inmediatamente
rm -f "$RAW_DUMP"

# 4. Cálculo de Checksum SHA-256 sobre el archivo cifrado
sha256sum "$ENCRYPTED_BACKUP" > "$CHECKSUM_FILE"

echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Respaldo cifrado exitoso: $ENCRYPTED_BACKUP"
echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Checksum SHA-256 registrado en: $CHECKSUM_FILE"

# 5. Rotación de respaldos antiguos
find "$BACKUP_DIR" -type f -name "${DB_NAME}_*.enc" -mtime +$RETENTION_DAYS -exec rm -f {} \;
find "$BACKUP_DIR" -type f -name "${DB_NAME}_*.sha256" -mtime +$RETENTION_DAYS -exec rm -f {} \;

echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Rotación completada. Respaldos mayores a $RETENTION_DAYS días depurados."
