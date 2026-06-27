r"""Coleta um snapshot de todos os sites e grava/mescla no SQLite.

Rode periodicamente (ex.: a cada 6h) no Agendador de Tarefas do Windows:
    .\.venv\Scripts\python.exe collect.py

Quanto mais coletas, mais confiavel fica o historico de last_seen.
"""
from __future__ import annotations

import io
import os
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from dotenv import load_dotenv

from unifi import UnifiClient, db
from unifi import config as unifi_config_mod
from unifi.inventory import snapshot_all

load_dotenv()


def main() -> None:
    t0 = time.time()
    db_path = os.getenv("DB_PATH") or db.default_path()
    key_path = os.path.join(os.path.dirname(db_path), "secret.key")
    cfg = unifi_config_mod.resolve(db_path, key_path)
    if not cfg or not cfg["username"] or not cfg["password"]:
        sys.exit("UniFi nao configurado. Abra o app e configure em Configuracao (/config).")
    client = UnifiClient(
        host=cfg["host"], username=cfg["username"], password=cfg["password"],
        site=cfg["site"], verify_ssl=cfg["verify"],
    )
    client.login()
    rows, ts = snapshot_all(client)
    client.logout()

    conn = db.connect(os.getenv("DB_PATH"))
    res = db.record_snapshot(conn, rows, ts)
    summ = db.overview_summary(conn)
    t = summ["totals"]

    when = time.strftime("%d/%m/%Y %H:%M", time.localtime(ts))
    print(f"[{when}] coleta #{res['collection_id']} gravada em {time.time()-t0:.1f}s")
    print(f"  linhas: {res['rows']} | marcados como removidos: {res['marked_removed']}")
    print(f"  cadastrados: {t['total']} | em uso: {t['in_use']} | "
          f"disponiveis (>{summ['days']}d): {t['reclaimable']} "
          f"(parados {t['over_x']} + nunca {t['never']})")
    print(f"  total de coletas no historico: {summ['collections']}")


if __name__ == "__main__":
    main()
