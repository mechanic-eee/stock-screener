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


# Telegram hard limit is 4096 chars/message; an oversized send is HTTP 400 and
# the WHOLE alert silently vanishes (green job, dead alert). Split on line
# boundaries with headroom.
_CHUNK = 3800


def _chunks(text: str) -> list[str]:
    if len(text) <= _CHUNK:
        return [text]
    out, cur = [], ""
    for line in text.split("\n"):
        if cur and len(cur) + 1 + len(line) > _CHUNK:
            out.append(cur)
            cur = line
        else:
            cur = f"{cur}\n{line}" if cur else line
        while len(cur) > _CHUNK:  # single pathological line
            out.append(cur[:_CHUNK])
            cur = cur[_CHUNK:]
    if cur:
        out.append(cur)
    return out


def send_message(text: str, parse_mode: Optional[str] = None) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        log.warning("TELEGRAM_BOT_TOKEN/CHAT_ID not set; printing instead")
        print(f"[telegram-stub]\n{text}")
        return False
    parts = _chunks(text)
    if len(parts) > 1:
        return all(_send_one(token, chat_id, p, parse_mode) for p in parts)
    return _send_one(token, chat_id, parts[0], parse_mode)


def _send_one(token: str, chat_id: str, text: str, parse_mode: Optional[str] = None) -> bool:
    try:
        resp = requests.post(
            f"{API_BASE}/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, **({"parse_mode": parse_mode} if parse_mode else {})},
            timeout=15,
        )
        if not resp.ok:
            # Never log the request URL: it embeds the bot token, and Actions
            # logs on this public repo are world-readable. API error details
            # (e.g. "chat not found") are token-free and safe.
            detail = ""
            try:
                detail = str(resp.json().get("description", ""))
            except Exception:  # noqa: BLE001
                pass
            log.error("Telegram send failed: HTTP %s %s", resp.status_code, detail)
            return False
        return True
    except Exception as e:  # noqa: BLE001
        log.error("Telegram send failed: %s", str(e).replace(token, "***"))
        return False
