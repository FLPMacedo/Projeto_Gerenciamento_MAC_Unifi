"""Aplicativo de desktop: abre a interface numa janela nativa (sem navegador).

Modos:
  desktop.py            -> abre a janela (e coleta ao abrir)
  desktop.py --collect  -> roda uma coleta e sai (para a tarefa agendada)
  HEADLESS=1 desktop.py -> sobe so o servidor (sem janela) -- uso em testes
"""
from __future__ import annotations

import os
import socket
import sys
import threading
import time

import app as webapp
from unifi import db
from unifi.inventory import snapshot_all


def _free_port(preferred: int = 5000) -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", preferred))
        return preferred
    except OSError:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]
    finally:
        s.close()


def do_collect() -> None:
    """Uma coleta de todos os sites, mesclada no banco (modo --collect)."""
    client = webapp.get_client()
    rows, ts = snapshot_all(client)
    conn = db.connect(webapp.DB_PATH)
    try:
        res = db.record_snapshot(conn, rows, ts)
        summ = db.overview_summary(conn)
    finally:
        conn.close()
    t = summ["totals"]
    print(f"coleta #{res['collection_id']}: {res['rows']} linhas | "
          f"cadastrados {t['total']} | em uso {t['in_use']} | "
          f"disponiveis (>{summ['days']}d) {t['reclaimable']} | "
          f"coletas no historico: {summ['collections']}")


def _run_server(port: int) -> None:
    webapp.app.run(host="127.0.0.1", port=port, threaded=True, use_reloader=False)


def _wait_up(port: int, timeout: float = 15.0) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        try:
            with socket.create_connection(("127.0.0.1", port), 0.5):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def main() -> None:
    if "--collect" in sys.argv:
        do_collect()
        return

    port = _free_port(5000)
    threading.Thread(target=_run_server, args=(port,), daemon=True).start()
    _wait_up(port)

    # coleta ao abrir (em background, pra janela abrir rapido)
    threading.Thread(target=lambda: webapp.maybe_collect(force=True),
                     daemon=True).start()

    url = f"http://127.0.0.1:{port}/overview"

    if os.getenv("HEADLESS") == "1":
        print(f"HEADLESS: servindo em {url}")
        while True:
            time.sleep(3600)
        return

    import webview  # importado so quando vai abrir janela
    webview.create_window("Gestão MAC Mobile · UniFi", url,
                          width=1320, height=880, min_size=(1000, 640))
    webview.start()


if __name__ == "__main__":
    main()
