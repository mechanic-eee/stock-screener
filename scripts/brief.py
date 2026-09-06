"""brief.py — 정해진 시각에 Claude를 **읽기 전용**으로 돌려 서술형 브리핑을 만들고 텔레그램으로 배달.

"때 되면 알려줘, 내가 안 물어봐도 되게"(2026-09-06)의 서술 파트. 결정론적 판정(2차 트랜치·재랭킹)은
review.py 워치가 처리하고, 판단문이 필요한 것(8주 평가 등)은 이 스크립트가 처리한다.

설계 원칙 — 사실은 스크립트가, 판단은 Claude가, 쓰기·전송은 다시 스크립트가:
  1) 자료팩: compliance 표 · TRACKING · CONTROL · DECISIONS 포지션 표 · 계좌 상태 등을 data/brief/<kind>-<date>/에 모은다.
  2) `claude -p` 를 --allowedTools Read 로 실행(파일 쓰기·Bash 권한 없음). 프롬프트는 자료팩 경로만 가리킨다.
  3) 결과를 stock-investing/reviews/에 저장하고 텔레그램으로 보낸다. 실패하면 실패 사실을 보낸다(침묵 금지).
  4) 성공 시 계획이벤트(compliance)를 done 처리.

  python scripts/brief.py --kind paper8w              # 페이퍼 8주 중간평가
  python scripts/brief.py --kind paper8w --dry-run    # 자료팩·프롬프트만 생성(Claude·텔레그램 생략)
  python scripts/brief.py --kind paper8w --no-telegram
예약: scripts/register-brief-task.ps1 -Kind paper8w -At "2026-09-12 09:00"
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVESTING = ROOT.parent / "stock-investing"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except Exception:
    pass

MODEL = os.getenv("BRIEF_MODEL", "claude-fable-5-1")
MAX_TURNS = "14"
TIMEOUT_S = 1200


def _claude_exe() -> str | None:
    cand = [shutil.which("claude"), str(Path.home() / ".local" / "bin" / "claude.exe"),
            str(Path.home() / "AppData" / "Roaming" / "npm" / "claude.cmd")]
    for c in cand:
        if c and Path(c).exists():
            return c
    return None


def _send(text: str) -> bool:
    try:
        from screener.notify.telegram import send_message
        return bool(send_message(text))
    except Exception as e:  # noqa: BLE001
        print(f"telegram fail: {e}")
        return False


def _section(md: str, header_contains: str) -> str:
    """Return one '## ...' section (header line containing the marker) of a markdown text."""
    lines = md.splitlines()
    out, on = [], False
    for ln in lines:
        if ln.startswith("## "):
            if on:
                break
            on = header_contains in ln
        if on:
            out.append(ln)
    return "\n".join(out)


# --------------------------------------------------------------------------- kinds
def build_pack_paper8w(pack: Path, today: date) -> tuple[list[Path], str, Path, str]:
    """Returns (files, prompt, out_path, done_event_id)."""
    import compliance
    files: list[Path] = []

    def put(name: str, text: str):
        f = pack / name
        f.write_text(text, encoding="utf-8")
        files.append(f)

    evs = compliance.load()
    put("01-계획이벤트-준수율.txt", compliance.render(evs, today))
    tr = INVESTING / "TRACKING.md"
    put("02-TRACKING-코호트-판정별-포지션.md", tr.read_text(encoding="utf-8") if tr.exists() else "(TRACKING.md 없음)")
    ctl = INVESTING / "CONTROL.md"
    put("03-CONTROL-대조군.md", ctl.read_text(encoding="utf-8") if ctl.exists() else "(CONTROL.md 없음)")
    dec = INVESTING / "DECISIONS.md"
    dtxt = dec.read_text(encoding="utf-8") if dec.exists() else ""
    put("04-DECISIONS-포지션표.md", _section(dtxt, "📌 포지션") or "(포지션 표 없음)")
    # 결정 로그 최근 40개 불릿(최신 위) — 규칙 위반·재량의 증거
    bullets = [ln for ln in dtxt.splitlines() if ln.startswith("- [2026")][:40]
    put("05-DECISIONS-최근결정로그-40.md", "\n".join(bullets))
    acct = ROOT / "data" / "account_state.json"
    put("06-계좌상태.json", acct.read_text(encoding="utf-8") if acct.exists() else "{}")
    design = ROOT / "docs" / "recommendation-design-2026-07-17.md"
    dtext = design.read_text(encoding="utf-8") if design.exists() else ""
    put("07-설계-§3-forward검증목표.md", _section(dtext, "§3") or "(설계 §3 없음)")
    hyg = ROOT / "docs" / "experiment-holding-rotation-2026-09-06.md"
    if hyg.exists():
        put("08-실험-바스켓폭-패널위생-결론.md", _section(hyg.read_text(encoding="utf-8"), "결론") + "\n\n" +
            _section(hyg.read_text(encoding="utf-8"), "H2"))
    listing = "\n".join(f"- {f}" for f in files)
    prompt = f"""당신은 개인 투자자의 규칙 기반 '폭락주 회복' 시스템을 함께 만든 엔지니어이자 분석가다. 오늘은 {today.isoformat()}.
아래 자료팩 파일을 **전부 Read로 읽고**, 페이퍼 사이클 개시(2026-07-18) 후 8주 중간평가를 한국어로 작성하라.
파일 외의 정보를 지어내지 말고, 숫자는 파일에 있는 것만 인용하라(없으면 '자료 없음'이라고 써라).

자료팩:
{listing}

반드시 지킬 규칙:
- 이 평가의 목적은 **규칙 준수율과 파이프라인 작동 검증**이지 엣지 판독이 아니다(설계 §3). 표본 n<20이면 성과로 규칙을 바꾸자고 제안하지 마라. 규칙 변경은 10/10 분기 리뷰의 몫이다.
- 페이퍼와 실계좌를 절대 섞어 집계하지 마라. 수익률은 비용·세금·환율 미반영임을 한 번 명시하라.
- 대조군(CONTROL/판정별 성과)은 방향만 읽어라.

출력 형식(텔레그램으로 그대로 전송된다 — 마크다운 표·헤더 기호 없이, 짧은 줄, 전체 1,800자 이내):
1) 한 줄 판정: 8주간 시스템이 '규칙대로 굴러갔는가' (예/조건부/아니오 + 근거 한 문장)
2) 준수율: 정시율·집행률·평균 지연, 지연·미집행의 원인 상위 3개
3) 성과: 코호트별 페이퍼 수익률 vs 벤치마크(KOSPI/S&P) 한 줄씩, 판정별(채택 vs 대조군) 한 줄, 실계좌 시스템 픽(NVO·SIRI) 한 줄
4) 규칙 위반·프로세스 결함 3건 (날짜·종목·무엇이 어긋났나)
5) 다음 4주 권고 3개 — 측정·운영 개선만(규칙 변경 금지)
6) 10/10 분기 리뷰로 넘길 질문 3개
마지막 줄: "— 자동 생성(brief.py paper8w). 판정문에 이견이 있으면 세션에서 말해줘."
"""
    out = INVESTING / "reviews" / f"페이퍼-8주-중간평가-{today.isoformat()}.md"
    return files, prompt, out, "paper-8w"


KINDS = {"paper8w": build_pack_paper8w}


# --------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kind", required=True, choices=sorted(KINDS))
    ap.add_argument("--dry-run", action="store_true", help="자료팩·프롬프트만 생성")
    ap.add_argument("--no-telegram", action="store_true")
    ap.add_argument("--model", default=MODEL)
    args = ap.parse_args()
    today = date.today()
    pack = ROOT / "data" / "brief" / f"{args.kind}-{today.isoformat()}"
    pack.mkdir(parents=True, exist_ok=True)
    files, prompt, out_path, done_id = KINDS[args.kind](pack, today)
    (pack / "prompt.txt").write_text(prompt, encoding="utf-8")
    print(f"자료팩 {len(files)}개: {pack}")
    if args.dry_run:
        print(prompt[:600] + "\n...")
        return 0

    exe = _claude_exe()
    title = f"📝 {args.kind} 자동 브리핑 ({today.isoformat()})"
    if exe is None:
        msg = f"⚠️ {title} 실패 — claude CLI를 찾지 못함. 자료팩: {pack}. 세션에서 직접 요청 필요"
        print(msg)
        if not args.no_telegram:
            _send(msg)
        return 2
    cmd = [exe, "-p", prompt, "--allowedTools", "Read", "--max-turns", MAX_TURNS,
           "--output-format", "text", "--model", args.model]
    print(f"claude 실행: {exe} (model {args.model}, max-turns {MAX_TURNS})", flush=True)
    t0 = datetime.now()
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                             timeout=TIMEOUT_S, cwd=str(ROOT))
        text = (res.stdout or "").strip()
        err = (res.stderr or "").strip()
        rc = res.returncode
    except subprocess.TimeoutExpired:
        text, err, rc = "", f"timeout {TIMEOUT_S}s", 124
    secs = int((datetime.now() - t0).total_seconds())
    if rc != 0 or len(text) < 200:
        msg = (f"⚠️ {title} 실패 (rc={rc}, {secs}s) — {err[:300] or '출력 부족'}. 자료팩: {pack}. "
               "세션에서 '8주 평가해줘'로 대신 요청")
        print(msg)
        if not args.no_telegram:
            _send(msg)
        return 2
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(f"# {title}\n\n_생성 {datetime.now().isoformat(timespec='minutes')} · model {args.model} · "
                        f"{secs}s · 자료팩 {pack}_\n\n{text}\n", encoding="utf-8")
    print(f"저장: {out_path}")
    print(text)
    ok = True
    if not args.no_telegram:
        ok = _send(f"{title}\n\n{text}")
        print("(텔레그램 전송됨)" if ok else "(⚠️ 텔레그램 전송 실패)")
    try:
        import compliance
        evs = compliance.load()
        ev = next((e for e in evs if e.get("id") == done_id), None)
        if ev and ev.get("status") == "pending":
            ev["executed"] = today.isoformat()
            ev["status"] = compliance.judge(ev, today)
            ev["note"] = (ev.get("note") + " / " if ev.get("note") else "") + f"brief.py 자동 생성 → {out_path.name}"
            compliance.save(evs)
            print(f"계획이벤트 {done_id} → {ev['status']}")
    except Exception as e:  # noqa: BLE001
        print(f"계획이벤트 갱신 실패: {e}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
