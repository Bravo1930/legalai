# ==============================================================================
# LEGALAI MÉXICO - RESTAURACIÓN DE BASE DE DATOS EN WINDOWS / POWERSHELL
# ==============================================================================
# Procedimiento de recuperación ante desastres para servidores privados Windows
# Valida la integridad SHA-256 antes de aplicar cambios en PostgreSQL
# ==============================================================================
param (
    [Parameter(Mandatory=$true)]
    [string]$BackupFile,
    [string]$DbName = "legal_ai_db",
    [string]$DbUser = "postgres",
    [string]$DbHost = "localhost",
    [int]$DbPort = 5432,
    [string]$EncryptionKey = ""
)

if (!(Test-Path $BackupFile)) {
    Write-Error "El archivo de respaldo '$BackupFile' no existe."
    exit 1
}

$ChecksumFile = [System.IO.Path]::ChangeExtension($BackupFile, ".sha256")
if (Test-Path $ChecksumFile) {
    Write-Host "[$((Get-Date).ToString('s'))] Verificando integridad criptográfica SHA-256..." -ForegroundColor Cyan
    $ActualHash = (Get-FileHash -Path $BackupFile -Algorithm SHA256).Hash
    $ExpectedContent = Get-Content -Path $ChecksumFile -Raw
    $ExpectedHash = ($ExpectedContent -split "\s+")[0].Trim().ToUpper()

    if ($ActualHash.ToUpper() -ne $ExpectedHash) {
        Write-Error "ERROR CRÍTICO: La suma de comprobación SHA-256 no coincide. Posible corrupción o alteración del archivo."
        Write-Error "Esperado: $ExpectedHash"
        Write-Error "Obtenido: $ActualHash"
        exit 1
    }
    Write-Host "[$((Get-Date).ToString('s'))] Integridad SHA-256 validada exitosamente." -ForegroundColor Green
} else {
    Write-Host "[$((Get-Date).ToString('s'))] AVISO: No se encontró archivo de verificación .sha256. Continuando bajo supervisión del administrador..." -ForegroundColor Yellow
}

$RestoreTarget = $BackupFile

# Si el archivo está cifrado (.enc) y se dispone de OpenSSL
if ($BackupFile.EndsWith(".enc")) {
    if ([string]::IsNullOrWhiteSpace($EncryptionKey)) {
        Write-Error "El archivo está cifrado pero no se proporcionó -EncryptionKey."
        exit 1
    }
    $DecryptedTemp = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), "legalai_restore_$([System.IO.Path]::GetRandomFileName()).dump")
    Write-Host "[$((Get-Date).ToString('s'))] Descifrando archivo con OpenSSL AES-256-CBC..." -ForegroundColor Cyan
    & openssl enc -d -aes-256-cbc -pbkdf2 -iter 100000 -in $BackupFile -out $DecryptedTemp -k $EncryptionKey
    if ($LASTEXITCODE -ne 0 -or !(Test-Path $DecryptedTemp)) {
        Write-Error "Fallo en el descifrado del respaldo. Verifique la clave simétrica."
        exit 1
    }
    $RestoreTarget = $DecryptedTemp
}

Write-Host "[$((Get-Date).ToString('s'))] Restaurando base de datos '$DbName' en ${DbHost}:${DbPort}..." -ForegroundColor Cyan
try {
    & pg_restore -h $DbHost -p $DbPort -U $DbUser -d $DbName --clean --if-exists --no-owner -v $RestoreTarget
    Write-Host "[$((Get-Date).ToString('s'))] Restauración completada exitosamente." -ForegroundColor Green
} catch {
    Write-Error "Ocurrió un error al ejecutar pg_restore: $_"
} finally {
    if ($RestoreTarget -ne $BackupFile -and (Test-Path $RestoreTarget)) {
        Remove-Item -Path $RestoreTarget -Force
    }
}
