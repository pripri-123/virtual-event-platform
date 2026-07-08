# Deploy VEHP schema and seed data to Azure SQL Database
# Prerequisites: ODBC Driver 18, pyodbc (pip install -r requirements-azure.txt)
#
# Usage:
#   .\scripts\deploy-azure-sql.ps1
#   .\scripts\deploy-azure-sql.ps1 -SkipSeed

param(
    [switch]$SkipSeed
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "=== VEHP Azure SQL Deployment ===" -ForegroundColor Cyan

# Activate venv
$venvActivate = Join-Path $ProjectRoot "venv\Scripts\Activate.ps1"
if (-not (Test-Path $venvActivate)) {
    Write-Error "Virtual environment not found. Run: python -m venv venv; pip install -r requirements.txt"
}
. $venvActivate

# Verify pyodbc
python -c "import pyodbc; print('pyodbc OK:', pyodbc.version)" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing pyodbc..." -ForegroundColor Yellow
    pip install "pyodbc>=5.3.0"
}

# Verify Azure SQL env vars
python -c @"
from dotenv import load_dotenv
import os, sys
load_dotenv('.env')
required = ['AZURE_SQL_SERVER','AZURE_SQL_DATABASE','AZURE_SQL_USERNAME','AZURE_SQL_PASSWORD']
missing = [k for k in required if not os.getenv(k)]
if missing:
    print('Missing env vars:', ', '.join(missing))
    sys.exit(1)
print('Azure SQL config: OK')
"@

if ($LASTEXITCODE -ne 0) {
    Write-Error "Set AZURE_SQL_* variables in .env before deploying."
}

# Test connection
Write-Host "`nTesting Azure SQL connection..." -ForegroundColor Cyan
flask db-check-azure
if ($LASTEXITCODE -ne 0) { exit 1 }

# Run migrations
Write-Host "`nRunning migrations..." -ForegroundColor Cyan
flask db upgrade
if ($LASTEXITCODE -ne 0) { exit 1 }

if (-not $SkipSeed) {
    Write-Host "`nSeeding roles and demo data..." -ForegroundColor Cyan
    flask seed-roles
    flask seed-demo
}

Write-Host "`n=== Azure SQL deployment complete ===" -ForegroundColor Green
flask init-db
