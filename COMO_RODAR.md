# Como rodar o sistema (guia rápido)

Tudo roda a partir da pasta do projeto:
`C:\Temp\_Projeto_Gerenciamento_MAC_Unifi`

O Python já está instalado num ambiente isolado (`.venv`). **Sempre** chame o
Python por: `.\.venv\Scripts\python.exe`

> Pré-requisito: o arquivo **`.env`** (na pasta) com as credenciais do controller.
> Já está configurado. Se precisar, copie de `.env.example`.

---

## 1) Rodar a aplicação WEB (mais fácil para aprender)
```powershell
cd C:\Temp\_Projeto_Gerenciamento_MAC_Unifi
.\.venv\Scripts\python.exe app.py
```
Depois abra no navegador: **http://127.0.0.1:5000**
Para **parar**: tecle `Ctrl + C` na janela do PowerShell.

> **Primeiro acesso:** a tela pede para **criar um administrador** (usuário e
> senha do sistema). Depois você faz **login**. As credenciais do **UniFi** se
> configuram na tela **⚙ Configuração** (a senha fica criptografada no banco —
> pode então remover `UNIFI_PASSWORD` do `.env`). Sair: botão **⏻ Sair**.

Menus: **Sites · Visão geral · Clientes · Auditoria · Backup · Atualizar status**.

## 2) Rodar como JANELA (desktop, sem navegador)
```powershell
.\.venv\Scripts\python.exe desktop.py
```
Abre uma janela própria com a mesma interface.

### Gerar o executável .exe (opcional)
```powershell
.\build_exe.ps1
```
Gera `dist\GestaoMAC.exe`. Coloque o `.env` ao lado do `.exe`.
Duplo clique abre a janela. (Requer WebView2, que já vem no Windows 10/11.)

## 3) Coletar dados / atualizar histórico
A web coleta sozinha ao abrir (máx. 1x a cada 2 min). Para coletar manualmente:
```powershell
.\.venv\Scripts\python.exe collect.py
```
Para **histórico contínuo** (mesmo com o app fechado), agende no Windows:
```powershell
schtasks /Create /TN "UnifiMacCollect" /SC HOURLY /MO 6 `
  /TR "'C:\Temp\_Projeto_Gerenciamento_MAC_Unifi\.venv\Scripts\python.exe' `
       'C:\Temp\_Projeto_Gerenciamento_MAC_Unifi\collect.py'"
```

## 4) Importar uma planilha de cadastros (.xlsx)
```powershell
# SIMULAR (não grava nada) — sempre faça isso primeiro:
.\.venv\Scripts\python.exe importar.py "Wifi (1).xlsx"

# GRAVAR de fato:
.\.venv\Scripts\python.exe importar.py "Wifi (1).xlsx" --apply
```
- Mapeia **aba por aba**; o **MAC é detectado pelo padrão** (resolve colunas trocadas).
- **Unidade vem do nome da aba** (mapeada em `sites_map.json`, arquivo local).
- Colunas que não encaixam vão para **observações**.
- Quem não está na rede entra como **removido**, com os dados guardados.
- **Mescla** com o que já existe (não apaga).

> Pode importar **outras planilhas** depois — é só trocar o nome do arquivo.

## 5) Onde ficam os dados
- Banco: `data\history.db` (SQLite — histórico, cadastros, auditoria).
- Backups: pasta `backups\` (gerados pelo botão **Backup** ou export).

## Regra importante
🔒 O sistema é **SOMENTE LEITURA** no controller: ele coleta, registra e sugere,
mas **NUNCA adiciona/remove/bloqueia** MAC na UniFi. Essas ações são feitas por
uma pessoa, direto na UniFi.
