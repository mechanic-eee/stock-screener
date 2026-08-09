"""ledger.py — 실현손익 원장: 연간 통산 + 해외주식 양도세 공제 거리.

"올해 실현 얼마?"를 손으로 합산하던 것의 자동화(고도화 ③, 2026-08-09).
연말 절세 결정(이익 실현을 올해 할까 내년 할까 / 손실 통산 여유)이 직결 소비처.

  python scripts/ledger.py             # 연간 리포트
  python scripts/ledger.py --fx 1460   # 환율 덮어쓰기
  python scripts/ledger.py --year 2026

데이터: data/realized_ledger.json (gitignore — 개인 재무데이터). 매도 시 trades에 추가.
세제 단순화(정확 신고는 증권사 계산 기준):
- 해외(US) 주식: 연간 손익 통산 → 기본공제 250만원 → 초과분 22% (지방세 포함).
  손실 이월 불가 — 이익 있는 해에 같이 실현해야 통산 가치가 있다.
- 국내(KR) 주식: 소액주주 상장주식 양도차익 비과세 — 통산·과세 계산에서 제외(정보만 표시).
- 환율: 원칙은 결제일 환율이나 여기선 단일 환율 근사(--fx) — 리포트에 명시.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "realized_ledger.json"
EXEMPTION_KRW = 2_500_000
TAX_RATE = 0.22


def _summary(trades: list[dict], fx: float, year: int) -> dict:
    """(순수 함수 — 테스트 대상) 연도별 통산 요약.

    반환: rows(per-trade), us_total_usd, us_total_krw, kr_total_krw,
    taxable_krw(공제 후 과세표준, 음수면 0), est_tax_krw, exemption_left_krw
    (공제까지 남은 이익 여유 — 통산이 음수면 '공제 전액 + |손실|' 만큼 여유)."""
    rows = []
    us_usd = 0.0
    kr_krw = 0.0
    for t in trades:
        d = str(t.get("date", ""))
        if not d.startswith(str(year)):
            continue
        qty = float(t.get("qty") or 0)
        buy = float(t.get("buy") or 0)
        sell = float(t.get("sell") or 0)
        pnl_native = (sell - buy) * qty
        mkt = t.get("market", "US")
        pnl_krw = pnl_native * fx if mkt == "US" else pnl_native
        if mkt == "US":
            us_usd += pnl_native
        else:
            kr_krw += pnl_native
        pct = ((sell / buy - 1) * 100.0) if buy else None
        rows.append({"date": d, "ticker": t.get("ticker", "?"), "name": t.get("name", ""),
                     "market": mkt, "qty": qty, "pnl_native": pnl_native,
                     "pnl_krw": pnl_krw, "pct": pct, "note": t.get("note", "")})
    us_krw = us_usd * fx
    taxable = max(0.0, us_krw - EXEMPTION_KRW)
    return {
        "rows": rows,
        "us_total_usd": us_usd,
        "us_total_krw": us_krw,
        "kr_total_krw": kr_krw,
        "taxable_krw": taxable,
        "est_tax_krw": taxable * TAX_RATE,
        "exemption_left_krw": EXEMPTION_KRW - us_krw,  # 음수면 공제 소진(과세 구간)
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fx", type=float, default=None, help="USD/KRW 환율 (기본: holdings.json usdkrw → 1460)")
    ap.add_argument("--year", type=int, default=None, help="대상 연도 (기본: 최신 거래 연도)")
    ap.add_argument("--ledger", default=str(LEDGER))
    args = ap.parse_args()

    path = Path(args.ledger)
    if not path.exists():
        print(f"원장이 없습니다: {path}\ndata/realized_ledger.json에 매도 기록을 추가하면 여기서 통산됩니다.")
        return 0
    data = json.loads(path.read_text(encoding="utf-8"))
    trades = data.get("trades", [])
    if not trades:
        print("원장에 거래가 없습니다.")
        return 0

    fx = args.fx
    if fx is None:
        try:
            hold = json.loads((ROOT / "data" / "holdings.json").read_text(encoding="utf-8"))
            fx = float(hold.get("usdkrw") or 1460)
        except Exception:  # noqa: BLE001
            fx = 1460.0
    year = args.year or max(int(str(t.get("date", "0"))[:4]) for t in trades)

    s = _summary(trades, fx, year)
    print(f"📒 실현손익 원장 — {year}년 (환율 {fx:,.0f}원 단일 근사 — 정확 신고는 결제일 환율)")
    print(f"{'날짜':<11}{'티커':<7}{'수량':>6}  {'손익':>14}  {'수익률':>8}  비고")
    for r in s["rows"]:
        pnl = (f"${r['pnl_native']:+,.2f}" if r["market"] == "US" else f"{r['pnl_native']:+,.0f}원")
        pct = f"{r['pct']:+.1f}%" if r["pct"] is not None else "—"
        print(f"{r['date']:<11}{r['ticker']:<7}{r['qty']:>6.0f}  {pnl:>14}  {pct:>8}  {r['note']}")
    print()
    print(f"해외(US) 통산: ${s['us_total_usd']:+,.2f} ≈ ₩{s['us_total_krw']:+,.0f}")
    if s["kr_total_krw"]:
        print(f"국내(KR) 실현: ₩{s['kr_total_krw']:+,.0f} (소액주주 비과세 — 통산 제외)")
    if s["exemption_left_krw"] >= 0:
        print(f"기본공제(250만) 여유: ₩{s['exemption_left_krw']:,.0f} 남음 → 예상 양도세 0")
        print(f"→ 올해 안에 추가로 ₩{s['exemption_left_krw']:,.0f}(≈${s['exemption_left_krw']/fx:,.0f}) 이익 실현까지 무세")
    else:
        print(f"기본공제 소진 — 과세표준 ₩{s['taxable_krw']:,.0f} × 22% = 예상 세금 ₩{s['est_tax_krw']:,.0f}")
        print("→ 미실현 손실 포지션을 연내 실현하면 통산으로 줄일 수 있음 (이월 불가)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
