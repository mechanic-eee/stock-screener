# 배포 가이드 — 풀 클라우드 (GitHub + Actions + Streamlit Cloud)

목표: **어디서든 URL로 접속**하고, **매일 자동 스캔**된 결과를 기다림 없이 본다.

```
[GitHub Actions 매일 22:00 UTC]  --스캔-->  candidates.parquet
        |                                        |
        | force-push                             | (텔레그램 상위 알림)
        v                                        v
   data 브랜치  <-----raw URL 읽기-----  [Streamlit Cloud 앱]  <-- 당신(브라우저, 어디서나)
```

- **git/GitHub:** 코드 보관 + 매일 스캔(Actions). 앱을 직접 서빙하진 않음.
- **Streamlit Community Cloud:** 그 코드를 받아 앱을 띄우고 공개 URL 제공(무료).
- 무거운 스캔은 Actions에서 미리 → 앱은 작은 스냅샷만 읽어 **즉시** 표시. 보조지표·가중치 토글은 그대로 인터랙티브.

---

## 0. 준비
- GitHub 계정 (있음)
- (권장) **public 저장소** — Actions 분이 무제한, Streamlit Cloud 무료 연결이 쉬움. **코드엔 비밀이 없습니다**(키는 전부 Secrets). 회사 민감 정보가 아니면 public이 가장 편함.
- private도 가능하나 Actions 무료 한도(월 2000분)에 유의 — 전종목 일일 스캔이 길면 한도에 닿을 수 있음(아래 §5 참고).

## 1. GitHub 저장소 만들고 코드 올리기
로컬 저장소(`C:\Users\yoobg\Claude_work\projects\stock-screener`)를 그대로 올린다.

```powershell
# (한 번만) GitHub CLI 로그인
gh auth login

# public 저장소 생성 + 현재 폴더 푸시
gh repo create stock-screener --public --source=. --remote=origin --push
```
GitHub CLI가 없으면: github.com에서 빈 저장소 생성 후
```powershell
git remote add origin https://github.com/<당신아이디>/stock-screener.git
git push -u origin main
```

## 2. 일일 스캔 워크플로우 활성화
- 코드를 올리면 `.github/workflows/daily-scan.yml`이 자동 등록됨.
- 저장소 **Settings → Actions → General → Workflow permissions**를 **Read and write**로(데이터 브랜치 푸시용). 보통 기본 OK.
- 첫 실행은 수동으로: **Actions 탭 → Daily scan → Run workflow**. 완료되면 `data` 브랜치에 `candidates.parquet`이 생긴다.
- 이후 매일 22:00 UTC(=한국 07:00)에 자동 실행.

## 3. (선택) Secrets 등록 — 텔레그램·뉴스
저장소 **Settings → Secrets and variables → Actions → New repository secret**:

| 이름 | 용도 | 필수? |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | 매일 상위 후보 알림 | 선택 |
| `TELEGRAM_CHAT_ID` | 알림 수신 | 선택 |
| `NEWSAPI_KEY` | 뉴스 감성 필터 | 선택 |

텔레그램 봇: @BotFather에서 `/newbot` → 토큰 발급, **봇과 대화 시작(/start)** 후
`https://api.telegram.org/bot<토큰>/getUpdates`에서 `chat.id`(숫자) 확인.

> ⚠️ **둘 다 등록해야 발송된다.** 미등록이면 스캔은 성공해도 알림이 Actions 로그에
> `[telegram-stub]`로만 찍히고 폰으로는 안 온다 — **실패 알림(dead-man-switch)도 침묵**한다.
> CLI 한 줄: `gh secret set TELEGRAM_BOT_TOKEN -R mechanic-eee/stock-screener` (CHAT_ID 동일).
> `TELEGRAM_CHAT_ID`는 **숫자**여야 함(getUpdates의 `chat.id`). 봇 사용자명이 아니다.

추가로 **repository variable** `APP_URL`(Settings → Secrets and variables → Actions → Variables)에
호스팅 앱 주소를 넣으면 일일 알림 맨 아래 `🔗 <앱주소>` 링크가 붙어 폰에서 바로 열 수 있다.

## 4. Streamlit Community Cloud에 앱 띄우기
1. https://share.streamlit.io 접속 → GitHub로 로그인 → **Create app**.
2. 저장소 `mechanic-eee/stock-screener`, 브랜치 `main`, 파일 `app.py` 선택.
3. **Advanced settings → Python version = 3.12** (3.14는 아직 미지원).
4. **Secrets** (앱 설정의 Secrets, TOML 형식)에 입력:
   ```toml
   SNAPSHOT_URL = "https://raw.githubusercontent.com/mechanic-eee/stock-screener/data/candidates.parquet"
   APP_PASSWORD = "원하는_비밀번호"   # 설정하면 접속 시 비번 요구. 빼면 공개. 길고 랜덤하게.
   HOSTED = "1"                      # 호스팅 표시 — 라이브 스캔 버튼 비활성(차단 환경 안내)
   # NEWSAPI_KEY = "..."             # 앱에서 뉴스 필터 쓸 거면
   ```
5. Deploy. 앱 URL이 나온다 → **어디서든 접속**. 비번을 걸었으면 입력해야 들어감.

> 앱은 시작 시 `SNAPSHOT_URL`에서 최신 스냅샷을 읽는다(data 브랜치). §2의 첫 실행을 먼저 끝내야 데이터가 있다.

## 5. 운영 메모 (비용·주기)
- **Actions 분:** 전종목(KR≈1.4K + US≈5K) 일일 스캔은 수십 분이 걸릴 수 있음. public이면 무제한. private면 월 2000분 한도 — 길면 KR/US 격일 실행이나 US 주1회로 조정(워크플로우 cron/입력 수정).
- **시세 캐시:** Actions 캐시(`screener-db`)로 점진 수집. 첫 실행만 느리고 이후는 변경분 위주.
- **데이터 신선도:** 일일 스냅샷 = 하루 1회. 더 자주 원하면 cron 추가.
- **갱신 주기 조절:** 코드의 `max_age_days`(시세 1일/유니버스 7일)에서 변경.

## 로컬은 그대로
로컬에서는 바탕화면 아이콘(`run_app.bat`)으로 계속 실행 가능하고, 사이드바 "데이터 소스 → 라이브 스캔"으로 즉석 스캔도 된다. 클라우드 앱은 "스냅샷" 모드로 동작.

## (선택) 보유종목 감시 자동화 — 로컬 스케줄러
포지션(DECISIONS.md)은 로컬 전용이라 Actions로 감시할 수 없다. 대신:
```powershell
pwsh scripts/register-daily-task.ps1        # 평일 08:10, track+monitor(-Telegram) 자동 실행
pwsh scripts/register-daily-task.ps1 -Unregister   # 해제
```
노트북이 꺼져 있던 시간대면 **깨어난 직후 따라잡아 실행**(StartWhenAvailable)되고, 로그는
`stock-investing/monitor-log.txt`. 월요일마다 "감시 작동 중" 하트비트가 텔레그램으로 온다
(침묵=고장과 침묵=이상없음을 구분).
