"""compliance.py — 계획이벤트 표 → 준수율(정시율·집행률) + 기한 경과/임박 알림.

12주 페이퍼 국면의 공식 목표는 "엣지 판독"이 아니라 **규칙 준수율 검증**인데, 지금까지 아무도
세지 않았다(위반 증거는 산문에만: 2차 8/10→8/17 지연, 사이클 #2·#3 미실행, MNSO 6거래일 지연).
이 표가 9/12 8주 평가와 10/10 분기 리뷰 Q1의 유일한 근거다(시스템-평가 2026-09-05 P1).

  python scripts/compliance.py                       # 표 + 준수율 + 기한 경과/임박
  python scripts/compliance.py --add --ticker NVO --action "2차 트랜치 판정" --planned 2026-09-08 [--due 2026-09-10] [--note ...]
  python scripts/compliance.py --done nvo-t2 [--date 2026-09-08] [--note ...]   # 기한 내면 done, 지나면 late
  python scripts/compliance.py --miss ID / --waive ID --note "사용자 결정으로 면제"
  python scripts/compliance.py --json                # 요약 JSON(review/평가 스크립트용)

상태: pending(예정) · done(정시) · late(지연 집행) · missed(미집행) · waived(면제 — 사용자 결정, 분모 제외) · cancelled
정시율 = done / (done+late+missed) · 집행률 = (done+late) / (done+late+missed). 기한(due) 기본 = 예정일 + 2일.
데이터: ../stock-investing/planned_events.json (append 위주, 손편집 가능).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
INVESTING = ROOT.parent / "stock-investing"
PLANNED = INVESTING / "planned_events.json"
DEFAULT_GRACE_DAYS = 2
STATUSES = ("pending", "done", "late", "missed", "waived", "cancelled")


def load(path: Path = PLANNED) -> list[dict]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"⚠️ planned_events.json 파싱 실패: {e}", file=sys.stderr)
        return []
    return data.get("events", data) if isinstance(data, dict) else data


def save(events: list[dict], path: Path = PLANNED) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"_note": "계획이벤트 표 — compliance.py가 읽고 쓴다. 상태: pending/done/late/missed/waived/cancelled",
                   "events": events}, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def _d(s):
    try:
        return date.fromisoformat(str(s)[:10]) if s else None
    except ValueError:
        return None


def due_of(ev: dict) -> date | None:
    d = _d(ev.get("due"))
    if d:
        return d
    p = _d(ev.get("planned"))
    return (p + timedelta(days=int(ev.get("grace_days", DEFAULT_GRACE_DAYS)))) if p else None


def judge(ev: dict, executed: date) -> str:
    """집행일이 기한 내면 done, 지나면 late."""
    due = due_of(ev)
    return "done" if (due is None or executed <= due) else "late"


def summarize(events: list[dict], today: date | None = None) -> dict:
    today = today or date.today()
    c = {s: 0 for s in STATUSES}
    overdue, upcoming, late_days = [], [], []
    for ev in events:
        st = ev.get("status", "pending")
        c[st] = c.get(st, 0) + 1
        if st == "pending":
            due = due_of(ev)
            if due and due < today:
                overdue.append(ev)
            elif due and (due - today).days <= 3:
                upcoming.append(ev)
        if st == "late":
            p, x = _d(ev.get("planned")), _d(ev.get("executed"))
            if p and x:
                late_days.append((x - p).days)
    denom = c["done"] + c["late"] + c["missed"]
    return {"counts": c, "denominator": denom,
            "on_time_rate": (c["done"] / denom) if denom else None,
            "execution_rate": ((c["done"] + c["late"]) / denom) if denom else None,
            "avg_late_days": (sum(late_days) / len(late_days)) if late_days else None,
            "overdue": overdue, "upcoming": upcoming}


def _fmt_ev(ev: dict) -> str:
    t = f"{ev.get('ticker')} " if ev.get("ticker") and ev.get("ticker") != "—" else ""
    return f"{t}{ev.get('action')} (예정 {ev.get('planned')}, 기한 {due_of(ev)})"


def alert_lines(today: date | None = None, events: list[dict] | None = None) -> tuple[list[str], list[str]]:
    """(기한 경과, 임박 D-3) 텔레그램용 줄 — review.py가 매일 붙인다."""
    today = today or date.today()
    s = summarize(load() if events is None else events, today)
    od = [f"⏰ 기한 경과 {(today - due_of(ev)).days}일: {_fmt_ev(ev)}" for ev in s["overdue"]]
    up = [f"📅 D-{(due_of(ev) - today).days}: {_fmt_ev(ev)}" for ev in s["upcoming"]]
    return od, up


def render(events: list[dict], today: date | None = None) -> str:
    today = today or date.today()
    s = summarize(events, today)
    c = s["counts"]
    out = [f"📋 계획이벤트 {len(events)}건 — 정시 {c['done']} · 지연 {c['late']} · 미집행 {c['missed']} · "
           f"면제 {c['waived']} · 예정 {c['pending']}"]
    if s["denominator"]:
        out.append(f"   정시율 {s['on_time_rate']:.0%} · 집행률 {s['execution_rate']:.0%}"
                   + (f" · 평균 지연 {s['avg_late_days']:.1f}일" if s["avg_late_days"] is not None else "")
                   + f"  (분모 {s['denominator']}, 면제 제외)")
    for ev in s["overdue"]:
        out.append("   ⏰ 기한 경과: " + _fmt_ev(ev))
    for ev in s["upcoming"]:
        out.append("   📅 임박: " + _fmt_ev(ev))
    out.append("")
    out.append(f"{'id':<16}{'티커':<8}{'행동':<28}{'예정':<12}{'기한':<12}{'집행':<12}{'상태':<8}코드/메모")
    for ev in sorted(events, key=lambda e: (e.get("planned") or "", e.get("id") or "")):
        act = str(ev.get("action", ""))
        act = act[:26] + ("…" if len(act) > 26 else "")
        out.append(f"{str(ev.get('id','')):<16}{str(ev.get('ticker') or '—'):<8}{act:<28}"
                   f"{str(ev.get('planned') or ''):<12}{str(due_of(ev) or ''):<12}{str(ev.get('executed') or '—'):<12}"
                   f"{str(ev.get('status','')):<8}{ev.get('code') or ''}{(' · ' + ev['note']) if ev.get('note') else ''}")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--add", action="store_true")
    ap.add_argument("--ticker", default="—")
    ap.add_argument("--action")
    ap.add_argument("--planned")
    ap.add_argument("--due")
    ap.add_argument("--id")
    ap.add_argument("--done")
    ap.add_argument("--miss")
    ap.add_argument("--waive")
    ap.add_argument("--date", default=date.today().isoformat())
    ap.add_argument("--code")
    ap.add_argument("--note", default="")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    events = load()

    if args.add:
        if not (args.action and args.planned):
            print("❌ --action, --planned 필요"); return 1
        eid = args.id or f"{(args.ticker or 'ev').lower().replace(' ', '')}-{args.planned}"
        if any(e.get("id") == eid for e in events):
            print(f"❌ id 중복: {eid}"); return 1
        ev = {"id": eid, "ticker": args.ticker, "action": args.action, "planned": args.planned,
              "status": "pending", "code": args.code, "note": args.note}
        if args.due:
            ev["due"] = args.due
        events.append(ev)
        save(events)
        print(f"✅ 추가: {eid} — {_fmt_ev(ev)}")
        return 0
    for flag, new_status in ((args.done, None), (args.miss, "missed"), (args.waive, "waived")):
        if not flag:
            continue
        ev = next((e for e in events if e.get("id") == flag), None)
        if ev is None:
            print(f"❌ id 없음: {flag}"); return 1
        if new_status is None:
            x = _d(args.date)
            ev["executed"] = x.isoformat()
            ev["status"] = judge(ev, x)
        else:
            ev["status"] = new_status
        if args.note:
            ev["note"] = (ev.get("note") + " / " if ev.get("note") else "") + args.note
        if args.code:
            ev["code"] = args.code
        save(events)
        print(f"✅ {flag} → {ev['status']}")
        return 0
    if args.json:
        s = summarize(events)
        s["overdue"] = [e.get("id") for e in s["overdue"]]
        s["upcoming"] = [e.get("id") for e in s["upcoming"]]
        print(json.dumps(s, ensure_ascii=False, indent=1))
        return 0
    print(render(events))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
