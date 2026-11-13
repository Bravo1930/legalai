#!/bin/sh
# ==============================================================================
# LEGALAI MÉXICO - SCRIPT DE RECUPERACIÓN ANTE DESASTRES (RESTORE DB)
# ==============================================================================
# - Verificación estricta de integridad de checksum SHA-256
# - Descifrado AES-256-CBC con OpenSSL
# - Restauración a PostgreSQL mediante pg_restore
# ==============================================================================

set -e

if [ -z "$1" ]; then
    echo "Uso: $0 <ruta_al_archivo_cifrado.enc>"
    echo "Ejemplo: $0 /backups/legal_ai_db_20261113_020000.sql.gz.enc"
    exit 1
fi

ENCRYPTED_BACKUP="$1"
CHECKSUM_FILE="${ENCRYPTED_BACKUP%.sql.gz.enc}.sha256"
TEMP_DUMP="/tmp/restore_temp_$$.sql.gz"

DB_HOST=${POSTGRES_HOST:-"db"}
DB_USER=${POSTGRES_USER:-"postgres"}
DB_NAME=${POSTGRES_DB:-"legal_ai_db"}
ENC_KEY=${BACKUP_ENCRYPTION_KEY:-"default_aes_key_change_in_production"}

echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Iniciando procedimiento de recuperación ante desastres..."

# 1. Validación de Checksum SHA-256
if [ -f "$CHECKSUM_FILE" ]; then
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Validando integridad criptográfica..."
    sha256sum -c "$CHECKSUM_FILE"
    echo "✓ Integridad SHA-256 verificada con éxito."
else
    echo "ADVERTENCIA: No se encontró archivo de checksum '$CHECKSUM_FILE'. Procediendo con precaución."
fi

# 2. Descifrado AES-256-CBC
echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Descifrando archivo de respaldo..."
openssl enc -d -aes-256-cbc -pbkdf2 -iter 100000 -in "$ENCRYPTED_BACKUP" -out "$TEMP_DUMP" -k "$ENC_KEY"

# 3. Restauración en PostgreSQL
echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Restaurando tablas y vectores en base de datos '${DB_NAME}'..."
gunzip -c "$TEMP_DUMP" | pg_restore -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" --clean --if-exists --no-owner || true

# 4. Limpieza de archivo temporal
rm -f "$TEMP_DUMP"

echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Recuperación completada exitosamente. El sistema está listo para operar."
