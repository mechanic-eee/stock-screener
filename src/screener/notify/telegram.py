"""Telegram bot notifications (ported from predecessor project).

Reads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from the environment. If unset,
prints to stdout so local runs still show what would be sent.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

import requests

log = logging.getLogger(__name__)
API_BASE = "https://api.telegram.org"


def send_message(text: str, parse_mode: Optional[str] = None) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        log.warning("TELEGRAM_BOT_TOKEN/CHAT_ID not set; printing instead")
        print(f"[telegram-stub]\n{text}")
        return False
    try:
        resp = requests.post(
            f"{API_BASE}/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, **({"parse_mode": parse_mode} if parse_mode else {})},
            timeout=15,
        )
        resp.raise_for_status()
        return True
    except Exception as e:  # noqa: BLE001
        log.error("Telegram send failed: %s", e)
        return False


def format_alert(row: dict) -> str:
    """Render one screener result row as a concise alert message."""
    extras = "  ".join(
        f"{k}:{v}" for k, v in row.items()
        if k not in {"ticker", "name", "market", "close", "하락률", "점수"}
    )
    return (
        f"🎯 [{row.get('market')}] {row.get('name')} ({row.get('ticker')})\n"
        f"점수 {row.get('점수')}/100 · 종가 {row.get('close')} · {row.get('하락률'):.0f}%\n"
        f"  {extras}"
    )
