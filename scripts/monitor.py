"""monitor.py — 보유 포지션 thesis-break 감시 (루프의 '나가는 문').

발굴→결정→사이징→추적은 *진입*을 본다. 이건 *청산*을 본다: 보유 중인 종목이
(a) **손절 이탈**(현재가 ≤ 손절), (b) **새 위험공시**(DART 부도/영업정지/회생/채권관리·
감사의견 비적정·자본잠식), (c) **깊은 손실**에 빠졌나를 재점검해 알림한다. 들어가는 문만
강박적으로 보고 나가는 문을 무방비로 두던 갭을 메운다. track.py의 파싱·가격조회를 재사용.

  python scripts/monitor.py                      # 콘솔 알림 (보유 포지션)
  DART_API_KEY=... python scripts/monitor.py     # KR 위험공시 재점검 포함
  python scripts/monitor.py --telegram           # 알림 있으면 텔레그램 전송
  python scripts/monitor.py --loss-alert 25      # -25%↓ 손실도 경고(기본 30)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import track  # reuse _records_from / _current_price / _fmt / DECISIONS path  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

try:  # local runs: pick up TELEGRAM_*/DART_API_KEY from the project .env
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except Exception:
    pass


def _held_positions() -> list[dict]:
    """보유 상태의 DECISIONS 포지션만 (워치리스트 관심행은 제외)."""
    recs = track._records_from(track.DECISIONS, "decision")
    return [r for r in recs if "보유" in (r.get("status") or "")]


def _distress(market: str, ticker: str) -> list[str] | None:
    """보유 종목의 현재 치명 신호 재점검(DART/yfinance).

    반환 3-상태: 사유 리스트(치명 있음) / 빈 리스트(점검 수행·깨끗) /
    **None(점검 미수행 — 조회 실패·데이터 없음)**. 예전엔 미수행도 빈 리스트라
    "검사 안 됨"이 "깨끗함"으로 둔갑했다(서비스 감사 2026-07-19 [상-3]) —
    호출자는 None을 반드시 '미수행'으로 표기해야 한다.
    """
    try:
        from screener import fundamentals as fund
        fb = fund.get_fundamentals(market, ticker, use_cache=False)
    except Exception:  # noqa: BLE001 — distress check is best-effort
        return None
    if fb is None or not getattr(fb, "available", False):
        return None
    flags = []
    if getattr(fb, "capital_impairment", False):
        flags.append("자본잠식")
    if getattr(fb, "audit_qualified", False):
        flags.append("감사의견 비적정")
    if getattr(fb, "risk_event", None):
        flags.append(f"위험공시:{fb.risk_event}")
    if getattr(fb, "four_quarters_all_loss", False):
        flags.append("4분기 연속적자")
    return flags


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--telegram", action="store_true", help="알림이 있으면 텔레그램 전송")
    ap.add_argument("--loss-alert", type=float, default=30.0, help="이 %% 이상 손실이면 경고(기본 30)")
    ap.add_argument("--no-distress", action="store_true", help="DART/펀더 위험 재점검 생략(빠름)")
    args = ap.parse_args()

    held = _held_positions()
    if not held:
        print("보유 포지션이 없습니다 (DECISIONS.md 「📌 포지션」에 상태 '보유'인 행 필요). "
              "decide.py로 매수 결정을 기록하면 여기서 감시됩니다.")
        return 0

    print(f"보유 {len(held)}종목 감시 — 현재가/위험 재점검 중...", flush=True)
    alerts: list[str] = []        # 종목별 치명/경고 한 줄
    lines: list[str] = []          # 콘솔 상태표
    for it in held:
        mkt, tkr = it["market"], it["ticker"]
        cur = track._current_price(mkt, tkr)
        ret = ((cur - it["ref_price"]) / it["ref_price"] * 100.0) if cur else None
        stop = it.get("stop")
        flags: list[str] = []
        soft: list[str] = []  # 상태표엔 보이되 텔레그램 알림은 안 타는 경고
        if cur is None:
            # fail-closed: 이 유니버스의 파국(거래정지→상폐)은 정확히 가격 피드가
            # 죽는 사건이다 — 예전엔 이때 "가격없음 ✅"로 침묵했다(감사 [상-2]).
            flags.append("🔴 가격조회 실패 — 손절 감시 불능(거래정지·상폐·데이터 장애 확인)")
        if cur is not None and stop and cur <= stop:
            flags.append(f"🔴 손절이탈(현재 {track._fmt(mkt, cur)} ≤ 손절 {track._fmt(mkt, stop)})")
        if ret is not None and ret <= -abs(args.loss_alert):
            flags.append(f"🟠 손실 {ret:+.0f}%")
        if not args.no_distress:
            d = _distress(mkt, tkr)
            if d is None:
                soft.append("⚪ 위험 재점검 미수행(펀더 조회 실패 — 수동 확인)")
            else:
                for x in d:
                    flags.append(f"🔴 {x}")
        vs_stop = ((cur - stop) / cur * 100.0) if (cur and stop) else None
        status = (f"{track._fmt(mkt, cur)} · {ret:+.1f}%" if ret is not None else "가격없음")
        vs = f" · 손절여유 {vs_stop:+.0f}%" if vs_stop is not None else ""
        shown = flags + soft
        lines.append(f"  {tkr:<8}{mkt:<4} {status}{vs}"
                     + (f"  → {' | '.join(shown)}" if shown else "  ✅"))
        if flags:
            alerts.append(f"[{mkt}] {tkr} {ret:+.0f}% — {' | '.join(flags)}" if ret is not None
                          else f"[{mkt}] {tkr} — {' | '.join(flags)}")

    print("\n보유 포지션 상태:")
    for ln in lines:
        print(ln)

    if alerts:
        print(f"\n⚠️ thesis-break 알림 {len(alerts)}건 — 청산/재검토 후보:")
        for a in alerts:
            print("  " + a)
        if args.telegram:
            try:
                from screener.notify.telegram import send_message
                ok = send_message("🚨 보유종목 thesis-break\n" + "\n".join(alerts))
                print("  (텔레그램 전송됨)" if ok else "  (⚠️ 텔레그램 전송 실패 — 위 알림을 직접 확인하세요)")
            except Exception as e:  # noqa: BLE001
                print(f"  (텔레그램 전송 실패: {e})")
    else:
        print("\n✅ 보유종목 전부 정상 — 손절/위험공시 이상 없음.")
        # Monday heartbeat: '알림 없음'과 '감시가 죽어 있음'을 폰에서 구분할 수
        # 있게 주 1회 생존 신호를 보낸다 (dead-man 원칙 — 침묵은 성공이 아니다).
        if args.telegram:
            import datetime as _dt
            if _dt.date.today().weekday() == 0:  # Monday
                try:
                    from screener.notify.telegram import send_message
                    send_message("🩺 보유종목 감시 작동 중 — 이번 점검 알림 0건 (주간 하트비트)")
                except Exception:  # noqa: BLE001
                    pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
