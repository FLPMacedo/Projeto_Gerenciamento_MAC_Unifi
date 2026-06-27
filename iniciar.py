"""Inicia o sistema, abre o navegador e encerra quando o navegador fecha (v4).

- Abre http://127.0.0.1:<porta> no navegador padrao (modo silent, sem console).
- Coleta ao abrir.
- "Watchdog": se a pagina parar de mandar heartbeat (usuario fechou o navegador),
  faz a coleta final e encerra o processo. Assim: abriu -> sessao; fechou -> fecha.
"""
from __future__ import annotations

import os
import socket
import sys
import threading
import time
import webbrowser

import app as webapp

IDLE_SHUTDOWN = 90      # s sem heartbeat -> encerra (usuario fechou o navegador)
FIRST_GRACE = 120       # s de tolerancia ate o 1o heartbeat chegar


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


def _wait_up(port: int, timeout: float = 20.0) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        try:
            with socket.create_connection(("127.0.0.1", port), 0.5):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def _run_server(port: int) -> None:
    webapp.app.run(host="127.0.0.1", port=port, threaded=True, use_reloader=False)


def _watchdog(started_at: float) -> None:
    """Encerra o app quando o navegador some (sem heartbeat)."""
    while True:
        time.sleep(10)
        age = webapp.seconds_since_ping()
        # so encerra depois que ja houve heartbeat (pagina abriu) OU passou a graca
        if webapp.was_pinged():
            if age > IDLE_SHUTDOWN:
                webapp.final_shutdown_collect()
                webapp.log.info("navegador fechado -> encerrando o app")
                os._exit(0)
        elif time.time() - started_at > FIRST_GRACE:
            webapp.log.info("nenhum acesso (graca expirou) -> encerrando")
            os._exit(0)


def main() -> None:
    if "--collect" in sys.argv:
        webapp.maybe_collect(force=True)
        return

    port = _free_port(5000)
    url = f"http://127.0.0.1:{port}/"
    started = time.time()

    threading.Thread(target=_run_server, args=(port,), daemon=True).start()
    _wait_up(port)
    webapp.log.info("app iniciado em %s", url)

    # coleta ao abrir (em background, pra janela abrir rapido)
    threading.Thread(target=lambda: webapp.maybe_collect(force=True), daemon=True).start()

    if os.getenv("HEADLESS") == "1":
        print(f"HEADLESS: {url}")
        while True:
            time.sleep(3600)
        return

    threading.Thread(target=_watchdog, args=(started,), daemon=True).start()
    try:
        webbrowser.open(url)
    except Exception:
        pass

    # mantem o processo vivo (o watchdog encerra quando o navegador fechar)
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
