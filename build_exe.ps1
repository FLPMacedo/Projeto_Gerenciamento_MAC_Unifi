# Gera o executavel v1 (dist\GestaoMAC.exe) que ABRE O NAVEGADOR.
# Uso:  .\build_exe.ps1
$ErrorActionPreference = "Stop"
$py = ".\.venv\Scripts\python.exe"

& $py -m pip install -q pyinstaller openpyxl cryptography

# Limpa só artefatos de build; PRESERVA dist\data (banco em uso).
Remove-Item -Recurse -Force build, GestaoMAC.spec -ErrorAction SilentlyContinue
Remove-Item -Force "dist\GestaoMAC.exe" -ErrorAction SilentlyContinue

# --windowed = SILENT (sem janela preta/console). Logs vao para a pasta logs\.
& $py -m PyInstaller --noconfirm --onefile --windowed --name GestaoMAC `
  --icon "static\unifi.ico" `
  --add-data "templates;templates" `
  --add-data "static;static" `
  --collect-all openpyxl `
  iniciar.py

# secret.key fica na RAIZ do exe (mesma chave em todos os PCs). Copia 1x.
if (-not (Test-Path "dist\secret.key") -and (Test-Path "secret.key")) {
  Copy-Item "secret.key" "dist\secret.key" -Force
}
if (-not (Test-Path "dist\secret.key") -and (Test-Path "data\secret.key")) {
  Copy-Item "data\secret.key" "dist\secret.key" -Force
}

Write-Host "`nOK -> dist\GestaoMAC.exe (SILENT, sem console; logs em logs\)"
Write-Host "Multiusuario: aponte o DB_PATH (.env) para a pasta de rede e"
Write-Host "distribua a MESMA secret.key para a raiz de cada PC."
