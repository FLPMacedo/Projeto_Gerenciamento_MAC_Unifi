"""Resolve as credenciais do UniFi a partir do banco (settings).

A senha fica CRIPTOGRAFADA no banco (data/history.db), com a chave em
data/secret.key -- nunca no codigo. Na primeira vez, se houver um .env com
credenciais, elas sao SEMEADAS no banco (compatibilidade) e podem ser
removidas do .env depois.
"""
from __future__ import annotations

import os

from . import db, secret


def _truthy(v: str) -> bool:
    return (v or "").strip().lower() in {"1", "true", "yes", "on", "sim"}


def resolve(db_path: str | None, key_path: str) -> dict | None:
    conn = db.connect(db_path)
    try:
        host = db.get_setting(conn, "unifi_host")
        if not host and os.getenv("UNIFI_HOST"):
            db.set_setting(conn, "unifi_host", os.environ["UNIFI_HOST"])
            db.set_setting(conn, "unifi_site", os.getenv("UNIFI_SITE", "default"))
            db.set_setting(conn, "unifi_username", os.getenv("UNIFI_USERNAME", ""))
            db.set_setting(conn, "unifi_verify",
                           "1" if _truthy(os.getenv("UNIFI_VERIFY_SSL", "")) else "0")
            if os.getenv("UNIFI_PASSWORD"):
                db.set_setting(conn, "unifi_password_enc",
                               secret.encrypt(key_path, os.environ["UNIFI_PASSWORD"]))
            host = os.environ["UNIFI_HOST"]
        if not host:
            return None
        return {
            "host": host,
            "site": db.get_setting(conn, "unifi_site", "default"),
            "username": db.get_setting(conn, "unifi_username", ""),
            "password": secret.decrypt(key_path,
                                       db.get_setting(conn, "unifi_password_enc", "")),
            "verify": db.get_setting(conn, "unifi_verify", "0") == "1",
        }
    finally:
        conn.close()
