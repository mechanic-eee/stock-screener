"""review.py — 개인 보유종목 '규율 대시보드' (매일 줏을 거·버릴 거를 *규칙으로* 판정).

핵심 철학: 없는 타이밍 신호를 지어내지 않는다(백테스트서 타이밍은 기각 —
off_lows t-5.5). 대신 **내가 이미 정해둔 규칙이 오늘 걸렸는지**를 본다:
손절거리·손절선 미설정·점수랭킹 강등·위험공시(DART/EDGAR)·손실·테마 집중·
계획된 추가(2차 트랜치 등). '추가(줏기)'는 매일 딥 추격이 아니라 *미리 계획된
추가*만 알린다 — 데일리 반응매매(처분효과)를 자동화하지 않기 위해서.

  python scripts/review.py                 # 콘솔 대시보드
  python scripts/review.py --telegram      # 요약을 텔레그램으로 (daily.ps1 08:10)
  python scripts/review.py --no-rank       # 스냅샷 랭킹 조회 생략(빠름)

데이터: data/holdings.json (gitignore — 개인 재무데이터). monitor/track 헬퍼 재사용.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
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


def _verdict(h: dict, price, rank, distress, edgar_new, today: dt.date,
             loss_alert: float = 35.0, stop_near_pct: float = 8.0) -> dict:
    """(순수 함수 — 테스트 대상) 한 종목의 규율 판정.

    입력은 이미 조회된 값(가격/랭킹/위험/EDGAR)만 받아 IO와 분리. 반환:
      tag   : 🟢 유지 / 🟠 축소·재평가 / 🔴 청산검토 / ⚪ 정보없음
      flags : 조치가 필요한 규칙 위반 (텔레그램 알림 대상)
      adds  : 계획된 추가(🔵) — 매일 딥 추격이 아님
      soft  : 참고 정보(미수행·랭킹 등, 알림 아님)
      ret / vs_stop : 수익률 / 손절여유(%)
    rank=(rk,n,score)|None, distress=list|None, edgar_new=list[(sev,form,date)]|None."""
    cost = h.get("cost")
    stop = h.get("stop")
    flags: list[str] = []
    soft: list[str] = []
    adds: list[str] = []

    if price is None:
        return {"tag": "⚪ 정보없음", "flags": ["가격조회 실패 — 거래정지·상폐·데이터장애 확인"],
                "adds": [], "soft": [], "ret": None, "vs_stop": None}

    ret = ((price - cost) / cost * 100.0) if cost else None
    vs_stop = ((price - stop) / price * 100.0) if stop else None

    # --- 손절 규율 ---
    if stop is None:
        # 규율 갭: 손절선 없는 포지션 = 나가는 문 없이 들고 있는 것. 이 대시보드의
        # 존재 이유 중 하나가 이 갭을 매일 표면에 올리는 것.
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

    # --- 계획된 추가(줏기) — 미리 정한 것만 ---
    pa = h.get("planned_add")
    if pa and pa.get("date"):
        try:
            pad = dt.date.fromisoformat(pa["date"])
            dleft = (pad - today).days
            if -3 <= dleft <= 7:
                note = pa.get("note", "")
                adds.append(f"🔵 계획된 추가 {'D-'+str(dleft) if dleft>=0 else '지남'} ({pad.strftime('%m/%d')}): {note}")
        except ValueError:
            pass

    # --- 태그 = 최악 심각도 ---
    has_red = any(f.startswith("🔴") for f in flags)
    has_amber = any(f.startswith(("🟠", "⚠️")) for f in flags)
    tag = "🔴 청산검토" if has_red else ("🟠 축소·재평가" if has_amber else "🟢 유지")
    return {"tag": tag, "flags": flags, "adds": adds, "soft": soft,
            "ret": ret, "vs_stop": vs_stop}


def _rank_map(holdings: list[dict]):
    """보유 종목의 현 스냅샷 enrichment 랭킹 {ticker: (rank|None, n, score|None)}.
    스냅샷 원격 로드 — 실패나 유니버스 밖(ETF·낙폭<50%)이면 (None,n,None). None=전체 미수행."""
    try:
        import recommend as rec

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
                    sc = lst[i].get("score") or lst[i].get("total_score")
                    out[h["ticker"]] = (i + 1, len(lst), sc)
                else:
                    out[h["ticker"]] = (None, len(lst), None)
        return out
    except Exception:  # noqa: BLE001
        return None


def _theme_concentration(rows: list[dict], themes: dict, fx: float) -> list[str]:
    """테마별 평가액 비중 vs comfort_max_pct — 낸드 47% 같은 집중을 매일 표면에.
    KR은 원화라 fx로 USD 환산해 합산."""
    tot = 0.0
    by_theme: dict[str, float] = {}
    for r in rows:
        val = r["value_usd"]
        if val is None:
            continue
        tot += val
        th = r["h"].get("theme", "기타")
        by_theme[th] = by_theme.get(th, 0.0) + val
    out = []
    if tot <= 0:
        return out
    for th, v in sorted(by_theme.items(), key=lambda x: -x[1]):
        pct = v / tot * 100
        cfg = themes.get(th, {})
        cap = cfg.get("comfort_max_pct")
        label = cfg.get("label", th)
        over = (cap is not None and pct > cap)
        mark = f" ⚠️ 초과(한도 {cap}%)" if over else ""
        out.append((over, f"{label}: {pct:.0f}%{mark}"))
    return out


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

    path = Path(args.holdings)
    if not path.exists():
        print(f"보유 파일이 없습니다: {path}\n"
              "data/holdings.json에 실보유 종목을 기록하면 매일 여기서 규율 점검됩니다.")
        return 0
    data = json.loads(path.read_text(encoding="utf-8"))
    holdings = data.get("holdings", [])
    themes = data.get("themes", {})
    fx = float(data.get("usdkrw", 1460))
    if not holdings:
        print("holdings.json에 종목이 없습니다.")
        return 0

    print(f"보유 {len(holdings)}종목 규율 점검 — 현재가/위험/랭킹 조회 중...", flush=True)
    today = dt.date.today()
    ranks = None if args.no_rank else _rank_map(holdings)

    edgar_seen: dict[str, list] = {}
    if not args.no_edgar and monitor._EDGAR_SEEN_PATH.exists():
        try:
            edgar_seen = json.loads(monitor._EDGAR_SEEN_PATH.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            edgar_seen = {}

    rows = []
    for h in holdings:
        mkt, tkr = h["market"], h["ticker"]
        price = track._current_price(mkt, tkr)
        distress = None if args.no_distress else monitor._distress(mkt, tkr)
        edgar_new = None
        if mkt == "US" and not args.no_edgar:
            got = monitor._edgar_filings(tkr)
            if got is not None:
                forms, dates, accs = got
                prev = set(edgar_seen.get(tkr, []))
                if prev:  # 첫 실행은 기준선만(소급 알림 안 함)
                    edgar_new = [(sev, form, fdate) for sev, form, fdate, _ in
                                 monitor._filter_new_filings(forms, dates, accs, prev)]
                else:
                    edgar_new = []
                edgar_seen[tkr] = (list(prev) + [a for a in accs if a not in prev])[-80:]
        rk = ranks.get(tkr) if ranks else None
        v = _verdict(h, price, rk, distress, edgar_new, today,
                     loss_alert=args.loss_alert, stop_near_pct=args.stop_near)
        val_native = (price * h["shares"]) if price else None
        val_usd = None
        if val_native is not None:
            val_usd = val_native / fx if mkt == "KR" else val_native
        rows.append({"h": h, "price": price, "value_usd": val_usd, **v})

    # 콘솔 대시보드
    print("\n📋 보유종목 규율 점검")
    order = {"🔴 청산검토": 0, "🟠 축소·재평가": 1, "🟢 유지": 2, "⚪ 정보없음": 3}
    for r in sorted(rows, key=lambda x: order.get(x["tag"], 9)):
        h = r["h"]
        ps = (f"{track._fmt(h['market'], r['price'])} · {r['ret']:+.1f}%"
              if r["ret"] is not None else "가격없음")
        vs = f" · 손절여유 {r['vs_stop']:+.0f}%" if r["vs_stop"] is not None else ""
        print(f"  {r['tag']}  {h['name']}({h['ticker']})  {ps}{vs}")
        for f in r["flags"]:
            print(f"       └ {f}")
        for a in r["adds"]:
            print(f"       └ {a}")

    # 테마 집중도
    tconc = _theme_concentration(rows, themes, fx)
    if tconc:
        print("\n🎯 테마 집중도:")
        for _over, line in tconc:
            print("  · " + line)

    # 텔레그램 요약: 조치 필요(🔴/🟠) + 계획된 추가 + 테마 초과만 — 유지(🟢)는 생략
    if args.telegram:
        act = [r for r in rows if r["tag"].startswith(("🔴", "🟠", "⚪"))]
        adds = [a for r in rows for a in r["adds"]]
        over = [line for over, line in tconc if over]
        msg = [f"📋 보유 규율 점검 ({today.isoformat()})"]
        if act:
            for r in sorted(act, key=lambda x: order.get(x["tag"], 9)):
                h = r["h"]
                msg.append(f"{r['tag']} {h['name']}({h['ticker']}) — " + " · ".join(r["flags"]))
        if adds:
            msg.append("── 계획된 추가 ──")
            msg += adds
        if over:
            msg.append("⚠️ 테마 초과: " + " · ".join(over))
        if not act and not adds and not over:
            msg.append("🟢 전 종목 규칙 이상 없음 · 조치 불필요")
        try:
            from screener.notify.telegram import send_message
            ok = send_message("\n".join(msg))
            print("\n(텔레그램 전송됨)" if ok else "\n(⚠️ 텔레그램 전송 실패)")
        except Exception as e:  # noqa: BLE001
            print(f"\n(텔레그램 전송 실패: {e})")

    if not args.no_edgar:
        try:
            monitor._EDGAR_SEEN_PATH.parent.mkdir(exist_ok=True)
            monitor._EDGAR_SEEN_PATH.write_text(json.dumps(edgar_seen), encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
