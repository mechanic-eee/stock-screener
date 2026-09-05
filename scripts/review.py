"""review.py — 개인 보유종목 '규율 대시보드' (매일 줏을 거·버릴 거를 *규칙으로* 판정).

핵심 철학: 없는 타이밍 신호를 지어내지 않는다(백테스트서 타이밍은 기각 —
off_lows t-5.5). 대신 **내가 이미 정해둔 규칙이 오늘 걸렸는지**를 본다:
손절거리·손절선 미설정·점수랭킹 강등·위험공시(DART/EDGAR)·손실·테마 집중·
계획된 추가(2차 트랜치 등). '추가(줏기)'는 매일 딥 추격이 아니라 *미리 계획된
추가*만 알리며, 청산검토(🔴) 플래그가 있으면 **억제**한다(물타기 방지).

  python scripts/review.py                 # 콘솔 대시보드
  python scripts/review.py --telegram      # 요약을 텔레그램으로 (daily.ps1 08:10)
  python scripts/review.py --no-rank       # 스냅샷 랭킹 조회 생략(빠름)

데이터: data/holdings.json (gitignore — 개인 재무데이터). monitor/track 헬퍼 재사용.
견고성(멀티에이전트 감사 2026-07-22 반영): 종목별 오류 격리·손상 입력에도
--telegram이면 반드시 하트비트 1회 전송(monitor는 --no-heartbeat라 review가 유일한 맥박).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import monitor  # reuse _distress / _edgar_filings / _filter_new_filings  # noqa: E402
import track  # reuse _current_price / _fmt  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
HOLDINGS = ROOT / "data" / "holdings.json"
# review 전용 EDGAR seen — monitor와 파일을 공유하면 먼저 도는 monitor가 신규
# accession을 소비해 review가 '이미 본 것'으로 걸러버린다(감사 finding 1/22).
_SEEN_PATH = ROOT / "data" / "review_edgar_seen.json"


def _send(text: str) -> bool:
    """텔레그램 전송(best-effort). review가 유일한 일일 맥박이라 실패해도 죽지 않는다."""
    try:
        from screener.notify.telegram import send_message
        return bool(send_message(text))
    except Exception:  # noqa: BLE001
        return False


def _atomic_write_json(path: Path, obj) -> None:
    """temp+os.replace 원자 교체 — read-modify-write 중단 시 파일 절단 방지(finding 13)."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj), encoding="utf-8")
    os.replace(tmp, path)


def _verdict(h: dict, price, rank, distress, edgar_new, today: dt.date,
             loss_alert: float = 35.0, stop_near_pct: float = 8.0,
             price_note: "str | None" = None) -> dict:
    """(순수 함수 — 테스트 대상) 한 종목의 규율 판정.

    입력은 이미 조회된 값(가격/랭킹/위험/EDGAR)만 받아 IO와 분리. 반환:
      tag   : 🟢 유지 / 🟠 축소·재평가 / 🔴 청산검토 / ⚪ 정보없음
      flags : 조치가 필요한 규칙 위반, adds : 계획된 추가(🔵, 🔴 있으면 억제),
      soft  : 참고 정보, ret / vs_stop : 수익률 / 손절여유(%)
    rank=(rk,n,score)|None, distress=list|None, edgar_new=list[(sev,form,date)]|None."""
    cost = h.get("cost")
    stop = h.get("stop")
    if stop is not None and stop <= 0:   # 0/음수 = 미설정으로 정규화(finding 10)
        stop = None
    flags: list[str] = []
    soft: list[str] = []
    adds: list[str] = []

    if price is None:
        # price_note: track._current_quote의 사유('시세 정지 N영업일…' 등) — 조회 실패와
        # '피드는 살았는데 봉이 멈춤'을 구분해 보여준다(P0-2).
        return {"tag": "⚪ 정보없음",
                "flags": [f"{price_note or '가격조회 실패'} — 거래정지·상폐·데이터장애 확인"],
                "adds": [], "soft": [], "ret": None, "vs_stop": None}

    ret = ((price - cost) / cost * 100.0) if cost else None
    vs_stop = ((price - stop) / price * 100.0) if (stop and price) else None  # price 0 방어(finding 18)

    # --- 손절 규율 ---
    if stop is None:
        flags.append("⚠️ 손절선 미설정 — 출구 규칙 없음(지금 정하기)")
    elif price <= stop:
        flags.append(f"🔴 손절이탈(현재 {track._fmt(h['market'], price)} ≤ 손절 {track._fmt(h['market'], stop)})")
    elif vs_stop is not None and vs_stop <= stop_near_pct:
        flags.append(f"🟠 손절근접(여유 {vs_stop:+.0f}%)")

    # --- 위험공시(DART/펀더) ---
    if distress is None:
        soft.append("⚪ 위험 재점검 미수행")
    else:
        for x in distress:
            flags.append(f"🔴 {x}")

    # --- EDGAR 신규공시(US) ---
    if edgar_new is not None:
        for sev, form, fdate in edgar_new:
            flags.append(f"{sev} EDGAR 신규 {form} ({fdate.strftime('%m/%d')}) — 내용 확인")

    # --- 스크리너 랭킹 강등(참고) ---
    if rank is not None:
        rk, n, _score = rank
        if rk is not None and n and rk > n * 0.5:
            flags.append(f"🟠 스크리너 랭킹 하위 50% 강등({rk}/{n}) — thesis 재평가")

    # --- 깊은 손실(재평가 신호, 청산 신호는 아님) ---
    if ret is not None and ret <= -abs(loss_alert):
        flags.append(f"🟠 손실 {ret:+.0f}% — thesis 재평가")

    has_red = any(f.startswith("🔴") for f in flags)

    # --- 계획된 추가(줏기) — 미리 정한 것만, 그리고 🔴 있으면 억제(물타기 방지, finding 4) ---
    pa = h.get("planned_add")
    if isinstance(pa, dict) and pa.get("date"):
        try:
            pad = dt.date.fromisoformat(str(pa["date"]))
            dleft = (pad - today).days
            if -3 <= dleft <= 7:
                note = pa.get("note", "")
                if has_red:
                    soft.append(f"⏸ 계획된 추가 보류 — 청산검토 플래그 활성({note})")
                else:
                    lbl = f"D-{dleft}" if dleft >= 0 else "지남"
                    adds.append(f"🔵 계획된 추가 {lbl} ({pad.strftime('%m/%d')}): {note}")
        except (ValueError, TypeError):   # 숫자/형식 오류 표면화(finding 7)
            flags.append("⚠️ planned_add 날짜 형식 오류 — 확인")

    has_amber = any(f.startswith(("🟠", "⚠️")) for f in flags)
    tag = "🔴 청산검토" if has_red else ("🟠 축소·재평가" if has_amber else "🟢 유지")
    return {"tag": tag, "flags": flags, "adds": adds, "soft": soft,
            "ret": ret, "vs_stop": vs_stop}


def _watch_verdict(w: dict, price, today: dt.date):
    """(순수 함수 — 테스트 대상) 워치 항목 1건 판정.

    상방 트리거·재상정일은 손절과 달리 아무 코드도 감시하지 않던 갭(NVO $47.06
    재탈환, 브이티 8/12 재상정 등 — 사람 기억에만 존재)의 자동화. 반환:
    None(미발동) / 문자열(발동 메시지 — 항목을 watch에서 지울 때까지 매일 표시).
    type: price_above | price_below | date."""
    if not isinstance(w, dict):
        return f"⚠️ 워치 항목 형식 오류({w!r}) — 확인"
    t = w.get("type")
    label = w.get("note") or w.get("ticker", "?")
    if t in ("price_above", "price_below"):
        # level 검증 — 결측·비숫자면 무장된 듯 보이나 영구 미발동(블라인드)이므로 표면화(감사 F8)
        if w.get("level") is None:
            return f"⚠️ 워치 level 미설정({w.get('ticker','?')}) — 확인"
        try:
            lvl = float(w["level"])
        except (TypeError, ValueError):
            return f"⚠️ 워치 level 형식 오류({w.get('ticker','?')}: {w.get('level')!r}) — 확인"
        if price is None:
            return None  # 조회 실패 표면화는 _run이 담당(미도달과 구분)
        if t == "price_above" and price >= lvl:
            return f"🔔 {w.get('ticker')} {price:,.2f} ≥ {lvl:,.2f} 도달 — {label}"
        if t == "price_below" and price <= lvl:
            return f"🔔 {w.get('ticker')} {price:,.2f} ≤ {lvl:,.2f} 도달 — {label}"
        return None
    if t == "date":
        try:
            d = dt.date.fromisoformat(str(w.get("date")))
        except (ValueError, TypeError):
            return f"⚠️ 워치 날짜 형식 오류({w.get('ticker','?')}: {w.get('date')!r}) — 확인"
        if today >= d:
            tag = "D-DAY" if today == d else f"D+{(today - d).days}"
            return f"🗓 {tag} {w.get('ticker','')} — {label}"
        return None
    return f"⚠️ 워치 type 미상({t!r}) — 확인"


def _rank_map(holdings: list[dict]):
    """보유 종목의 현 스냅샷 enrichment 랭킹 {ticker: (rank|None, n, score|None)}.
    스냅샷 원격 로드 — 실패나 유니버스 밖(ETF·낙폭<50%)이면 (None,n,None). None=전체 미수행."""
    try:
        import recommend as rec
        from screener.cooldown import SCORE_KEY  # 엔진은 점수를 '점수' 키로 저장(finding 9)

        rows, _ = rec._load_rows(rec.twl.DEFAULT_SNAPSHOT, 50, 5)
        out = {}
        for mk in {h["market"] for h in holdings}:
            lst = [r for r in rows if r.get("market") == mk
                   and r.get("_security_type", "common") in ("common", "preferred")]
            tickers = [r["ticker"] for r in lst]
            for h in holdings:
                if h["market"] != mk:
                    continue
                if h["ticker"] in tickers:
                    i = tickers.index(h["ticker"])
                    out[h["ticker"]] = (i + 1, len(lst), lst[i].get(SCORE_KEY))
                else:
                    out[h["ticker"]] = (None, len(lst), None)
        return out
    except Exception:  # noqa: BLE001
        return None


def _theme_concentration(rows: list[dict], themes: dict) -> list[tuple[bool, str]]:
    """테마별 평가액 비중 vs comfort_max_pct — 낸드 47% 같은 집중을 매일 표면에.
    rows의 value_usd는 이미 USD 환산됨(main에서). 반환 [(over, 라인)]."""
    tot = 0.0
    by_theme: dict[str, float] = {}
    for r in rows:
        val = r["value_usd"]
        if val is None:
            continue
        tot += val
        th = r["h"].get("theme", "기타")
        by_theme[th] = by_theme.get(th, 0.0) + val
    out: list[tuple[bool, str]] = []
    if tot <= 0:
        return out
    for th, v in sorted(by_theme.items(), key=lambda x: -x[1]):
        pct = v / tot * 100
        cfg = themes.get(th, {})
        cap = cfg.get("comfort_max_pct")
        label = cfg.get("label", th)
        over = (cap is not None and pct > cap)
        out.append((over, f"{label}: {pct:.0f}%" + (f" ⚠️ 초과(한도 {cap}%)" if over else "")))
    return out


def _run(holdings, themes, fx, today, args, watch=None) -> None:
    """본체 — main()의 try 안에서 호출(예외는 main이 폴백 핑으로 처리)."""
    watch = watch or []
    ranks = None if args.no_rank else _rank_map(holdings)
    edgar_seen: dict[str, list] = {}
    if not args.no_edgar and _SEEN_PATH.exists():
        try:
            edgar_seen = json.loads(_SEEN_PATH.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            edgar_seen = {}

    rows = []
    for h in holdings:
        try:
            mkt, tkr = h["market"], h["ticker"]
            price, _bar, price_note = track._current_quote(mkt, tkr)  # 캐시 수명·정지 판정은 track 단일 소스(P0-2)
            distress = None if args.no_distress else monitor._distress(mkt, tkr)
            edgar_new = None
            # ETN/ETP 티커는 CIK가 발행 은행으로 매핑돼(예: GDXU→Bank of Montreal)
            # 은행의 일상 424B2 홍수가 전부 🔴로 유입된다 — holdings의 "edgar": false로 차단.
            if mkt == "US" and not args.no_edgar and h.get("edgar", True):
                got = monitor._edgar_filings(tkr)
                if got is not None:
                    forms, dates, accs = got
                    prev = set(edgar_seen.get(tkr, []))
                    edgar_new = ([(s, f, d) for s, f, d, _ in
                                  monitor._filter_new_filings(forms, dates, accs, prev)] if prev else [])
                    edgar_seen[tkr] = (list(prev) + [a for a in accs if a not in prev])[-80:]
            rk = ranks.get(tkr) if ranks else None
            v = _verdict(h, price, rk, distress, edgar_new, today,
                         loss_alert=args.loss_alert, stop_near_pct=args.stop_near,
                         price_note=price_note)
            sh = h.get("shares") or 0
            val_native = (price * sh) if (price and sh > 0) else None
            val_usd = None if val_native is None else (val_native / fx if mkt == "KR" else val_native)
            rows.append({"h": h, "price": price, "value_usd": val_usd, **v})
        except Exception as e:  # noqa: BLE001 — 한 종목 오류가 전체·하트비트를 죽이지 않게(finding 5/17)
            rows.append({"h": h, "price": None, "value_usd": None, "tag": "⚪ 정보없음",
                         "flags": [f"처리 오류: {e}"], "adds": [], "soft": [], "ret": None, "vs_stop": None})

    # 콘솔 대시보드
    print("\n📋 보유종목 규율 점검")
    order = {"🔴 청산검토": 0, "🟠 축소·재평가": 1, "🟢 유지": 2, "⚪ 정보없음": 3}
    for r in sorted(rows, key=lambda x: order.get(x["tag"], 9)):
        h = r["h"]
        nm = h.get("name") or h.get("ticker", "?")
        ps = (f"{track._fmt(h['market'], r['price'])} · {r['ret']:+.1f}%"
              if r["ret"] is not None else "가격없음")
        vs = f" · 손절여유 {r['vs_stop']:+.0f}%" if r["vs_stop"] is not None else ""
        sysmk = " [시스템]" if h.get("system") else ""
        print(f"  {r['tag']}  {nm}({h.get('ticker','?')}){sysmk}  {ps}{vs}")
        for f in r["flags"]:
            print(f"       └ {f}")
        for a in r["adds"]:
            print(f"       └ {a}")

    tconc = _theme_concentration(rows, themes)
    if tconc:
        print("\n🎯 테마 집중도:")
        for _over, line in tconc:
            print("  · " + line)

    # 워치(재진입 트리거·재상정일) — 보유 아님, 조건 도달 시에만 알림.
    # 가격은 보유 조회분 재사용, 비보유 티커(예: 청산 후 NVO)는 별도 조회.
    price_by_tkr = {r["h"]["ticker"]: r["price"] for r in rows}
    hits: list[str] = []
    for w in watch:
        try:  # 항목별 격리 — 손상 워치 1건이 요약·하트비트를 죽이지 않게(감사 F2/F7)
            px = None
            fetch_failed = False
            if isinstance(w, dict) and w.get("type") in ("price_above", "price_below"):
                tkr = w.get("ticker")
                px = price_by_tkr.get(tkr)
                if px is None and tkr:
                    try:
                        px = track._current_price(w.get("market", "US"), tkr)
                    except Exception:  # noqa: BLE001
                        px = None
                    fetch_failed = px is None
            msg = _watch_verdict(w, px, today)
            if msg:
                hits.append(msg)
            elif fetch_failed:
                # 미도달이 아니라 '판정 불능' — 무장된 듯 보이는 블라인드 상태 표면화(감사 F8)
                hits.append(f"⚪ 워치 가격조회 실패({w.get('ticker','?')}) — 판정 불능")
        except Exception as e:  # noqa: BLE001
            hits.append(f"⚠️ 워치 처리 오류({(w or {}).get('ticker','?') if isinstance(w, dict) else '?'}: {e})")
    if hits:
        print("\n🔔 워치 조건 도달:")
        for m in hits:
            print("  · " + m)

    # 텔레그램 요약: 조치 필요(🔴/🟠/⚪) + 계획된 추가 + 테마 초과.
    # system:true(NVO 등)는 monitor가 알림 소유 → 이중 전송 방지 위해 제외(finding 3).
    if args.telegram:
        act = [r for r in rows if r["tag"].startswith(("🔴", "🟠", "⚪")) and not r["h"].get("system")]
        adds = [a for r in rows if not r["h"].get("system") for a in r["adds"]]
        over = [line for o, line in tconc if o]
        msg = [f"📋 보유 규율 점검 ({today.isoformat()}) · {len(holdings)}종목"]
        if act:
            for r in sorted(act, key=lambda x: order.get(x["tag"], 9)):
                h = r["h"]
                nm = h.get("name") or h.get("ticker", "?")
                msg.append(f"{r['tag']} {nm}({h.get('ticker','?')}) — " + " · ".join(r["flags"]))
        if adds:
            msg.append("── 계획된 추가 ──")
            msg += adds
        if hits:
            msg.append("── 🔔 워치 도달 ──")
            msg += hits
        if over:
            msg.append("⚠️ 테마 초과: " + " · ".join(over))
        if not act and not adds and not over and not hits:
            msg.append("🟢 개인 보유 규칙 이상 없음 · 조치 불필요")
        print("\n(텔레그램 전송됨)" if _send("\n".join(msg)) else "\n(⚠️ 텔레그램 전송 실패)")

    if not args.no_edgar:
        try:
            _SEEN_PATH.parent.mkdir(exist_ok=True)
            _atomic_write_json(_SEEN_PATH, edgar_seen)
        except Exception:  # noqa: BLE001
            pass


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--telegram", action="store_true", help="요약을 텔레그램으로 전송")
    ap.add_argument("--no-distress", action="store_true", help="DART/펀더 위험 재점검 생략")
    ap.add_argument("--no-edgar", action="store_true", help="EDGAR 신규공시 감시 생략")
    ap.add_argument("--no-rank", action="store_true", help="스냅샷 랭킹 조회 생략(빠름)")
    ap.add_argument("--loss-alert", type=float, default=35.0, help="이 %% 이상 손실이면 재평가 플래그(기본 35)")
    ap.add_argument("--stop-near", type=float, default=8.0, help="손절여유 이 %% 이하면 근접 경고(기본 8)")
    ap.add_argument("--holdings", default=str(HOLDINGS), help="holdings.json 경로")
    args = ap.parse_args()
    today = dt.date.today()

    # 하트비트 보장: monitor가 --no-heartbeat라 review가 유일한 일일 맥박 →
    # 파일 부재·공백·손상·예외에도 --telegram이면 반드시 한 번은 신호를 보낸다(finding 2).
    path = Path(args.holdings)
    if not path.exists():
        msg = f"⚪ 규율 점검 스킵 — holdings.json 없음 ({path.name})"
        print(msg)
        if args.telegram:
            _send(msg)
        return 0
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        msg = f"⚠️ 규율 점검 실패 — holdings.json 파싱 오류: {e}"
        print(msg)
        if args.telegram:
            _send(msg)
        return 1
    holdings = data.get("holdings", [])
    if not holdings:
        msg = "⚪ 규율 점검 — holdings.json에 종목 없음"
        print(msg)
        if args.telegram:
            _send(msg)
        return 0

    raw = data.get("usdkrw")   # null/0/비숫자 방어(finding 6)
    try:
        fx = float(raw) if raw is not None else 1460.0
    except (TypeError, ValueError):
        fx = 1460.0
    if fx <= 0:
        fx = 1460.0
    themes = data.get("themes", {})

    print(f"보유 {len(holdings)}종목 규율 점검 — 현재가/위험/랭킹 조회 중...", flush=True)
    try:
        _run(holdings, themes, fx, today, args, watch=data.get("watch", []))
    except Exception as e:  # noqa: BLE001 — 어떤 예외에도 하트비트는 나간다
        msg = f"⚠️ review 실패: {e}"
        print(msg)
        if args.telegram:
            _send(msg)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
