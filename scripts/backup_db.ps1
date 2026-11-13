# ==============================================================================
# LEGALAI MÉXICO - RESPALDO DE BASE DE DATOS EN WINDOWS / POWERSHELL
# ==============================================================================
param (
    [string]$DbName = "legal_ai_db",
    [string]$DbUser = "postgres",
    [string]$DbHost = "localhost",
    [int]$DbPort = 5432,
    [string]$BackupDir = "./backups"
)

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
if (!(Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
}

$DumpFile = Join-Path $BackupDir "${DbName}_${Timestamp}.dump"
$ChecksumFile = Join-Path $BackupDir "${DbName}_${Timestamp}.sha256"

Write-Host "[$((Get-Date).ToString('s'))] Generando respaldo de PostgreSQL para '$DbName'..." -ForegroundColor Cyan

# Ejecutar pg_dump si está en el PATH
try {
    & pg_dump -h $DbHost -p $DbPort -U $DbUser -F c -b -v -f $DumpFile $DbName
    
    if (Test-Path $DumpFile) {
        $Hash = (Get-FileHash -Path $DumpFile -Algorithm SHA256).Hash
        "$Hash *$((Get-Item $DumpFile).Name)" | Out-File -FilePath $ChecksumFile -Encoding utf8
        Write-Host "[$((Get-Date).ToString('s'))] Respaldo generado con éxito: $DumpFile" -ForegroundColor Green
        Write-Host "[$((Get-Date).ToString('s'))] SHA-256 Checksum: $Hash" -ForegroundColor Yellow
    }
} catch {
    Write-Error "Error al ejecutar pg_dump: $_"
}
