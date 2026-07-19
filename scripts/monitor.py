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
import datetime as dt
import re
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
    """보유 상태의 DECISIONS 포지션만 (워치리스트 관심행은 제외).

    같은 티커의 트랜치 행들은 track._merge_tranches로 합성 — 감시는 포지션당
    한 번, 손절은 가장 최근 결정의 값으로 본다."""
    from collections import defaultdict

    by: dict[str, list[dict]] = defaultdict(list)
    for r in track._records_from(track.DECISIONS, "decision"):
        if "보유" in (r.get("status") or ""):
            by[r["ticker"]].append(r)
    return [track._merge_tranches(v) for v in by.values()]


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


ROOT = Path(__file__).resolve().parents[1]
EDGAR_UA = "stock-screener-research yoobg1234@gmail.com"  # EDGAR 필수 식별 UA
_EDGAR_SEEN_PATH = ROOT / "data" / "edgar_seen.json"      # 로컬 상태 (gitignore)
_CIK_MAP_PATH = ROOT / "exports" / "edgar_cache" / "_cik_map.json"  # edgar_pit와 공유


def _classify_filing(form: str) -> str | None:
    """보유 중 US 공시의 위험 등급 — SMCI 교훈($7B 증자를 점수가 못 봄)의 커버.
    🔴=희석·상폐·지연(424B/S-1/S-3/25/NT 10-*), 🟠=중요 이벤트(8-K, 내용 확인)."""
    f = str(form).upper()
    if f.startswith(("424B", "S-1", "S-3", "25", "NT 10")):
        return "🔴"
    if f.startswith("8-K"):
        return "🟠"
    return None


def _filter_new_filings(forms, dates, accessions, seen: set,
                        lookback_days: int = 30, today: dt.date | None = None):
    """(순수 함수 — 테스트 대상) 신규 위험 공시 [(등급, form, date, accession)]."""
    today = today or dt.date.today()
    out = []
    for form, dstr, acc in zip(forms, dates, accessions):
        sev = _classify_filing(form)
        if not sev or acc in seen:
            continue
        try:
            fdate = dt.date.fromisoformat(str(dstr))
        except ValueError:
            continue
        if (today - fdate).days > lookback_days:
            continue
        out.append((sev, str(form), fdate, acc))
    return out


def _edgar_filings(ticker: str):
    """EDGAR submissions → (forms, dates, accessions) 최근 60건. None=조회 실패."""
    import json
    import urllib.request

    try:
        cik = None
        if _CIK_MAP_PATH.exists():
            cik = json.loads(_CIK_MAP_PATH.read_text(encoding="utf-8")).get(ticker.upper())
        if cik is None:
            req = urllib.request.Request("https://www.sec.gov/files/company_tickers.json",
                                         headers={"User-Agent": EDGAR_UA})
            raw = json.loads(urllib.request.urlopen(req, timeout=15).read())
            m = {str(r["ticker"]).upper(): f"{int(r['cik_str']):010d}" for r in raw.values()}
            _CIK_MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
            _CIK_MAP_PATH.write_text(json.dumps(m), encoding="utf-8")
            cik = m.get(ticker.upper())
        if cik is None:
            return None
        req = urllib.request.Request(f"https://data.sec.gov/submissions/CIK{cik}.json",
                                     headers={"User-Agent": EDGAR_UA})
        sub = json.loads(urllib.request.urlopen(req, timeout=15).read())
        rec = sub.get("filings", {}).get("recent", {})
        n = 60
        return (rec.get("form", [])[:n], rec.get("filingDate", [])[:n],
                rec.get("accessionNumber", [])[:n])
    except Exception:  # noqa: BLE001 — 3-상태: 실패는 None(미수행)
        return None


def _tracking_cohort_lines() -> list[str]:
    """직전 track.py가 쓴 TRACKING.md의 코호트 불릿 — 주간 성적표 재료."""
    try:
        txt = (track.INVESTING / "TRACKING.md").read_text(encoding="utf-8")
    except Exception:  # noqa: BLE001
        return []
    out, grab = [], False
    for ln in txt.splitlines():
        if ln.startswith("**코호트별**"):
            grab = True
            continue
        if grab:
            if ln.startswith("- "):
                out.append(ln[2:])
            elif out:
                break
    return out


def _upcoming_events(held_tickers: set[str]) -> list[tuple[dt.date, str]]:
    """(날짜, 라벨) — 보유 종목의 WATCHLIST 촉매 셀(M/D)과 DECISIONS 로그의
    2차 트랜치·리뷰 날짜를 파싱. 날짜 약속이 마크다운에만 적혀 있고 아무 코드도
    그날 알려주지 않던 갭(감사 M5)의 자동화. M/D는 가까운 미래로 연도 추론."""
    today = dt.date.today()

    def _md(m: str, d: str) -> dt.date | None:
        try:
            ev = dt.date(today.year, int(m), int(d))
        except ValueError:
            return None
        return ev if (today - ev).days <= 30 else dt.date(today.year + 1, int(m), int(d))

    events: list[tuple[dt.date, str]] = []
    try:
        for header, data in track._tables(track.WATCHLIST.read_text(encoding="utf-8")):
            ci_t, ci_cat = track._col(header, "티커", "종목"), track._col(header, "촉매")
            if ci_t is None or ci_cat is None:
                continue
            for cells in data:
                if len(cells) <= max(ci_t, ci_cat):
                    continue
                mt = (track._TICKER.search(cells[ci_t])
                      or re.search(r"\b(\d{6})\b", cells[ci_t]))
                tkr = mt.group(1) if mt else cells[ci_t].strip().upper()
                if tkr not in held_tickers:
                    continue
                for m, d in re.findall(r"(\d{1,2})/(\d{1,2})", cells[ci_cat]):
                    ev = _md(m, d)
                    if ev:
                        label = cells[ci_cat].split("(")[0].strip() or "이벤트"
                        events.append((ev, f"{tkr} {label}"))
    except Exception:  # noqa: BLE001 — 리마인더는 감시 본체를 깨지 않는다
        pass
    try:
        dtext = track.DECISIONS.read_text(encoding="utf-8")
        m2 = re.search(r"2차 트랜치[^\d]{0,10}(\d{1,2})/(\d{1,2})", dtext)
        if m2:
            ev = _md(m2.group(1), m2.group(2))
            if ev:
                events.append((ev, "2차 트랜치 결정"))
        for iso in re.findall(r"리뷰\s*(20\d{2}-\d{2}-\d{2})", dtext):
            try:
                events.append((dt.date.fromisoformat(iso), "120d 리뷰"))
            except ValueError:
                pass
    except Exception:  # noqa: BLE001
        pass
    seen: set = set()
    out = []
    for ev, lbl in sorted(events):
        if ev >= today and (ev, lbl) not in seen:
            seen.add((ev, lbl))
            out.append((ev, lbl))
    return out


def _rank_check(held: list[dict]) -> dict | None:
    """보유 종목의 현 스냅샷 enrichment 랭킹 — thesis-break '하위 50% 강등'과
    2차 트랜치 취소 조건('상위 25% 밖')의 자동화(SMCI 수동 적발의 코드화).
    반환 {ticker: (rank|None, n)} 또는 None(미수행 — 스냅샷 로드 실패)."""
    try:
        import recommend as rec

        rows, _ = rec._load_rows(rec.twl.DEFAULT_SNAPSHOT, 50, 5)
        by_mkt: dict[str, list[str]] = {}
        for mk in {r["market"] for r in held}:
            by_mkt[mk] = [r["ticker"] for r in rows if r.get("market") == mk
                          and r.get("_security_type", "common") in ("common", "preferred")]
        out = {}
        for it in held:
            lst = by_mkt.get(it["market"], [])
            rk = (lst.index(it["ticker"]) + 1) if it["ticker"] in lst else None
            out[it["ticker"]] = (rk, len(lst))
        return out
    except Exception:  # noqa: BLE001
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--telegram", action="store_true", help="알림이 있으면 텔레그램 전송")
    ap.add_argument("--loss-alert", type=float, default=30.0, help="이 %% 이상 손실이면 경고(기본 30)")
    ap.add_argument("--no-distress", action="store_true", help="DART/펀더 위험 재점검 생략(빠름)")
    ap.add_argument("--no-rank-check", action="store_true",
                    help="스냅샷 랭킹 강등 체크 생략(스냅샷 다운로드·랭킹 ~1분 절약)")
    ap.add_argument("--no-edgar", action="store_true",
                    help="보유 US 종목 EDGAR 신규공시 감시 생략")
    ap.add_argument("--weekly", action="store_true",
                    help="주간 성적표를 오늘 강제 출력/전송 (기본: 월요일 자동)")
    args = ap.parse_args()

    held = _held_positions()
    if not held:
        print("보유 포지션이 없습니다 (DECISIONS.md 「📌 포지션」에 상태 '보유'인 행 필요). "
              "decide.py로 매수 결정을 기록하면 여기서 감시됩니다.")
        return 0

    print(f"보유 {len(held)}종목 감시 — 현재가/위험 재점검 중...", flush=True)
    events = _upcoming_events({it["ticker"] for it in held})
    ranks = None if args.no_rank_check else _rank_check(held)
    edgar_seen: dict[str, list] = {}
    if not args.no_edgar:
        import json as _json
        try:
            if _EDGAR_SEEN_PATH.exists():
                edgar_seen = _json.loads(_EDGAR_SEEN_PATH.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            edgar_seen = {}
    alerts: list[str] = []        # 종목별 치명/경고 한 줄
    lines: list[str] = []          # 콘솔 상태표
    vs_list: list[tuple[float, str]] = []   # (손절여유, 티커) — 하트비트용
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
        if mkt == "US" and not args.no_edgar:
            got = _edgar_filings(tkr)
            if got is None:
                soft.append("⚪ EDGAR 공시 감시 미수행(조회 실패)")
            else:
                forms, dates, accs = got
                prev = set(edgar_seen.get(tkr, []))
                if not prev:
                    # 첫 실행은 기준선만 — 과거 공시 전체를 소급 알림하지 않는다
                    soft.append("ℹ️ EDGAR 감시 기준선 설정(다음 실행부터 신규 공시 알림)")
                else:
                    for sev, form, fdate, _acc in _filter_new_filings(forms, dates, accs, prev):
                        flags.append(f"{sev} EDGAR 신규 {form} ({fdate.strftime('%m/%d')}) — 내용 확인")
                edgar_seen[tkr] = (list(prev) + [a for a in accs if a not in prev])[-80:]
        if not args.no_rank_check:
            if ranks is None:
                soft.append("⚪ 랭킹 체크 미수행(스냅샷 로드 실패)")
            else:
                rk, n = ranks.get(tkr, (None, 0))
                if rk is None:
                    soft.append("ℹ️ 스냅샷 후보 이탈 — 낙폭 기준 회복(졸업) 가능성, 확인")
                elif n and rk > n * 0.5:
                    flags.append(f"🟠 랭킹 하위 50% 강등({rk}/{n}) — thesis 재평가")
                elif n and rk > n * 0.25:
                    soft.append(f"ℹ️ 랭킹 상위 25% 밖({rk}/{n}) — 2차 트랜치 취소 조건 해당")
        vs_stop = ((cur - stop) / cur * 100.0) if (cur and stop) else None
        if vs_stop is not None:
            vs_list.append((vs_stop, tkr))
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

    if events:
        print("\n다가오는 이벤트:")
        for ev, lbl in events[:5]:
            print(f"  {ev.strftime('%m/%d')} D-{(ev - dt.date.today()).days:<3} {lbl}")
        # D-3 이내는 알림으로 승격 — 캘린더 수동 의존을 백업한다
        for ev, lbl in events:
            d_left = (ev - dt.date.today()).days
            if d_left <= 3:
                alerts.append(f"🗓 {lbl} D-{d_left} ({ev.strftime('%m/%d')})")

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

    # 주간 성적표 (월요일 자동 / --weekly 강제): 코호트 vs 벤치마크(직전 track
    # 산출 재사용)·다음 이벤트·보유 요약을 폰으로 — 성적표가 로컬 파일에만
    # 존재하던 가시성 갭(감사 §2-3)의 해소. 신뢰는 매번 보는 표면에서 유지된다.
    weekly = args.weekly or dt.date.today().weekday() == 0
    if weekly:
        rep = [f"📊 주간 성적표 ({dt.date.today().isoformat()})"]
        rep += [f"· {ln}" for ln in _tracking_cohort_lines()[:6]]
        if events:
            rep.append("· 다음 이벤트: " + " / ".join(
                f"{lbl} {ev.strftime('%m/%d')}" for ev, lbl in events[:3]))
        rep.append(f"· 보유 {len(held)} · 오늘 알림 {len(alerts)}건 · "
                   "(수익률은 비용·세금·환율 미반영)")
        text = "\n".join(rep)
        print("\n" + text)
        if args.telegram:
            try:
                from screener.notify.telegram import send_message
                send_message(text)
            except Exception:  # noqa: BLE001
                pass

    # 일일 하트비트: '알림 없음'과 '감시가 죽어 있음'을 폰에서 구분(감사 M1).
    # 알림이 있는 날은 알림이, 주간 성적표가 나간 날은 성적표가 곧 생존 신호.
    if args.telegram and not alerts and not weekly:
        parts = [f"🩺 보유 {len(held)} 감시 정상 · 알림 0"]
        if vs_list:
            worst_vs, worst_t = min(vs_list)
            parts.append(f"최소 손절여유 {worst_vs:+.0f}%({worst_t})")
        if events:
            ev, lbl = events[0]
            parts.append(f"다음 이벤트 {lbl} {ev.strftime('%m/%d')}"
                         f"(D-{(ev - dt.date.today()).days})")
        try:
            from screener.notify.telegram import send_message
            send_message(" · ".join(parts))
        except Exception:  # noqa: BLE001
            pass

    if not args.no_edgar:
        import json as _json
        try:
            _EDGAR_SEEN_PATH.parent.mkdir(exist_ok=True)
            _EDGAR_SEEN_PATH.write_text(_json.dumps(edgar_seen), encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
