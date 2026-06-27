# Gestão de MAC — Rede Mobile UniFi (multi-site)

Sistema web para **monitorar e gerenciar os MACs das redes "mobile" (Wi-Fi)** de
um controller **UniFi OS** (multi-site). Coleta o estado, mantém histórico e
**auditoria durável**, faz backup e identifica MACs sem uso; ações de escrita
(adicionar/remover/troca) são **manuais e unitárias**, com confirmação e registro
de quem fez. Cada WLAN mobile tem uma allow-list limitada a **512** MACs.

> Host, credenciais e nomes de sites vêm do ambiente (`.env`/login) e **não
> ficam no código**. Veja `MANUAL_TECNICO.md`.

## Por que existe
Quando uma allow-list chega ao limite (512/512), o software identifica os MACs
**parados** (não vistos há muito tempo ou nunca vistos) e os apresenta como
**candidatos** a liberar — respeitando a regra dos **35 dias** (à prova de férias).

## Componentes
- `unifi/client.py` — cliente da API UniFi OS (multi-site, login/CSRF). Permite
  **leitura** e a **edição da allow-list** (PUT) usada pelas ações unitárias;
  demais escritas (block-sta, etc.) ficam bloqueadas.
- `unifi/inventory.py` — classifica cada MAC: `online / recent / idle / stale /
  abandoned / never`. "Sem uso" = parado >30d ou nunca visto (limiar ajustável).
- `app.py` + `templates/` + `static/` — aplicação web (Flask).
- `cli.py` — CLI auxiliar (list/block/unblock/rename) de dispositivos.
- `explore.py` — script de diagnóstico read-only (sites, WLANs, buckets de uso).

## Instalação
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # preencha credenciais (conta LOCAL do controller)
```

## Aplicativo de desktop (.exe)
A mesma interface roda numa **janela nativa** (sem navegador), empacotada num
único `.exe` com PyInstaller + pywebview.

```powershell
.\build_exe.ps1          # gera dist\GestaoMAC.exe
```
- Coloque o **`.env`** ao lado do `.exe` (credenciais + config). O banco
  `data\history.db` é criado/atualizado nessa mesma pasta.
- **Duplo clique** em `GestaoMAC.exe` → abre a janela. Ele **coleta ao abrir**.
- Coleta agendada (histórico contínuo mesmo fechado), via Agendador de Tarefas:
  ```powershell
  schtasks /Create /TN "UnifiMacCollect" /SC HOURLY /MO 6 `
    /TR "'C:\caminho\dist\GestaoMAC.exe' --collect"
  ```
- Requer o **WebView2 Runtime** (já presente no Windows 10/11 atuais).

`desktop.py` é o ponto de entrada do `.exe` (modos: janela, `--collect`, `HEADLESS=1`).

## Rodar a aplicação web
```powershell
.\.venv\Scripts\python.exe app.py
# abra http://127.0.0.1:5000
```

### Fluxo de uso (somente leitura)
1. **Selecione o site** (os 13 são descobertos automaticamente).
2. **Dashboard**: barra de ocupação (ex.: 512/512), quantos em uso x sem uso,
   e a tabela com o status de cada MAC. Filtros: Todos / Sem uso / Online.
3. **↻ Atualizar status**: força uma coleta (leitura) do controller.
4. **⬇ Backup**: baixa um CSV completo de todos os aparelhos já vistos na mobile
   (e salva uma cópia em `backups/`). Por site há também **Exportar CSV**.
5. Os "sem uso" são **sugestões** para uma pessoa avaliar e remover **na UniFi**.

> 🔒 O sistema **não escreve** no controller. Adicionar/remover MAC é feito por
> uma pessoa responsável, diretamente na interface da UniFi.

## Histórico em SQLite + regra dos 35 dias
Cada coleta é **mesclada** num banco SQLite (`data/history.db`), guardando o
**maior `last_seen` já observado** por (site, MAC). Um MAC só é considerado
**disponível** (liberável) após **35 dias sem logar** — assim quem está de
**férias** não é marcado por engano.

- `unifi/db.py` — schema, merge e classificação (`AVAILABLE_DAYS = 35`).
- `collect.py` — roda uma coleta e grava no banco. Quanto mais coletas, mais
  confiável o histórico.
- Quem **nunca conectou** (`NEVER_MODE=grace`, padrão) só vira disponível 35
  dias após a 1ª coleta — protege cadastro novo que ainda não conectou. Use
  `NEVER_MODE=immediate` para contar nunca-logados como disponíveis na hora.

### Agendar a coleta (Windows)
```powershell
# a cada 6 horas
schtasks /Create /TN "UnifiMacCollect" /SC HOURLY /MO 6 /TR `
  "'C:\Temp\_Projeto_Gerenciamento_MAC_Unifi\.venv\Scripts\python.exe' `
   'C:\Temp\_Projeto_Gerenciamento_MAC_Unifi\collect.py'"
```
A aplicação web também grava uma coleta a cada acesso (no máximo 1x/120s).

## Cadastro de Cliente (menu "Clientes")
Cada MAC vira uma ficha de cliente, unindo **dados da UniFi** (nome do aparelho,
hostname, fabricante, 1º/último acesso, online, sites) com **dados de negócio**
editáveis: **nome, setor, unidade, função, líder, chamado** e observações.

- `/clientes` — lista os ativos (com busca por qualquer campo).
- `/clientes/removidos` — MACs que saíram da allow-list (troca/remoção). Os
  **dados são preservados** aqui para consulta ou restauração.
- `/cliente/<mac>` — ficha: infos da UniFi + formulário de cadastro.
  - **Troca de aparelho**: na ficha do MAC novo, há um seletor para **copiar os
    dados** de um usuário removido (mantém nome/setor/etc. do aparelho antigo).

"Ativo" x "removido" é **derivado da allow-list**: tirar o MAC do UniFi move a
ficha para *removidos* automaticamente, sem perder o cadastro. Os dados de
cliente ficam no SQLite local (`client_info`), separados do controller.

## CLI (opcional, somente leitura)
```powershell
.\.venv\Scripts\python.exe cli.py sites
.\.venv\Scripts\python.exe cli.py list --site <id-do-site>
```
