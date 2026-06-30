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

# NAO distribuimos secret.key: cada maquina GERA a sua na 1a vez (cada usuario
# usa a propria conta UniFi; as credenciais ficam em creds.enc local).

Write-Host "`nOK -> dist\GestaoMAC.exe (SILENT, sem console; logs em logs\)"
Write-Host "Multiusuario: aponte o DB_PATH (.env) para a pasta de rede compartilhada."
Write-Host "Cada usuario faz login com a PROPRIA conta UniFi (creds locais por PC)."
