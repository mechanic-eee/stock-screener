# stock-screener — 5년 고가 대비 폭락주 스크리너 (점수 모델)

> 관련: 리서치/결정은 `..\stock-investing\` (워치리스트·결정 로그). 이 레포는 **후보를 자동으로 찾고 점수화하는 도구**다. 여기서 나온 후보를 stock-investing 워치리스트로 옮겨 추적한다.
> 설계 참고: `docs/PRD-reference.md`, `docs/calibration-methodology-reference.md` (선행 프로젝트에서 이관한 제품 설계서·캘리브레이션 방법론).
> **사용법: [`docs/indicator-guide.md`](docs/indicator-guide.md) — 보조지표 의미·게이트vs스코어러·실전 조합.**

## 무엇을 / 왜
종가 기준 **최근 N년(기본 5년) 최고가 대비 일정 비율(기본 −80%) 이상 폭락**한 종목을 기본 후보로 잡고, **보조지표 필터를 켜고/끄고 파라미터를 조정**하며 후보를 좁힌다. 각 지표는 단순 통과/탈락이 아니라 **0~100 점수**도 내며(게이트=필터+스코어러), 가중 합성점수로 후보를 **순위화**한다.

## 스택
- Python 3.x / pandas (지표·점수는 순수 pandas 계산 — 외부 TA 의존성 없음)
- 시세: `pykrx`(한국) · `yfinance`(미국, adj_close 보존, 재시도/백오프)
- 유니버스: KR=pykrx(시총필터), US=NASDAQ Trader 공식목록(ETF/SPAC/우선주 제외)
- 영속화: **SQLite** (`data/screener.db`) — 수천 종목 시세·유니버스 캐시
- 뉴스: NewsAPI(키 있을 때) + 경량 감성 사전 — 플러그인 구조라 교체 가능
- 알림: 텔레그램(선택) · UI: Streamlit 대시보드

## 구조
```
app.py                 Streamlit 대시보드 (필터 토글·파라미터·가중치 자동 렌더)
scan.py                CLI 배치 스캔 / 스모크 테스트
backtest/
  calibrate_gates.py   게이트 임계치 캘리브레이션(전향수익률 백테스트)
  export_prices.py     SQLite → parquet 추출 (캘리브레이션 입력)
docs/                  지표 사용 가이드(indicator-guide) · PRD · 캘리브레이션 방법론
src/screener/
  models.py            TickerData / Filter / Param / FilterOutcome(+score)
  indicators.py        MACD·RSI·볼린저·MA·하락률 (pure pandas)
  scoring.py           0~100 점수 곡선 (하락 종곡선·MACD 신선도·거래량 구간)
  engine.py            build_candidates(무거움) + apply_filters(빠름, 가중합성점수)
  data/                db(SQLite 스키마)·universe(KR/US 빌더)·prices(재시도)·cache(SQLite)
  filters/             base(레지스트리) + 지표 필터 1파일씩 (각자 score+weight 선언)
  news/                provider(추상화) + sentiment + 집계
  notify/              telegram
data/screener.db       시세/유니버스 캐시 (gitignore)
```

## 설계 핵심
- **수집(배치) vs 필터링(인터랙티브) 분리:** `build_candidates`가 시세를 SQLite에 캐시하고 기본 −80% 필터로 후보를 압축 → Streamlit은 그 위에서 보조지표·가중치를 즉시 재적용.
- **게이트=필터+스코어러:** 각 필터가 pass/fail과 0~100 점수를 함께 반환. 엔진이 활성 필터들의 점수를 **가중평균(런타임 정규화)**해 합성점수로 순위.
- **점수 곡선(PRD 이관):** 하락률은 종 곡선(65~80% 정점, >95% 상폐위험 0점), MACD는 신선도 감쇠+0선교차 보너스, 거래량은 3~5x 정점·10x↑ 이상치.
- **필터 = 플러그인:** `filters/`에 파일 하나 추가+`@register`만 하면 엔진·UI·점수에 자동 노출. 파라미터·가중치는 `Param`/`weight`에서 UI 컨트롤 자동 생성.
- **뉴스는 마지막에:** 네트워크 I/O라 기술필터 통과 종목에만 적용. 키 없으면 자동 비활성.

## 실행
```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # NewsAPI/텔레그램 키 쓸 거면 채우기 (선택)

# 빠른 동작 확인 (UI 없이) — 점수순 출력
python scan.py --markets US --limit 60 --min-drop 50 --macd

# 대시보드
python -m streamlit run app.py

# 임계치 캘리브레이션 (먼저 스캔으로 시세를 채운 뒤)
python backtest/export_prices.py --market US --out exports/prices_us.parquet
python backtest/calibrate_gates.py --data exports/prices_us.parquet --output exports/calib_us.md
# 데이터 없이 프레임워크만 확인:
python backtest/calibrate_gates.py --synthetic --output exports/calib_demo.md
```
> Windows 콘솔(cp949)에서 한글이 깨지면 `scan.py`는 자동 UTF-8 전환됨. PowerShell에서 직접 파일을 볼 땐 `$env:PYTHONUTF8=1` 또는 UTF-8 지원 뷰어 사용.

## 알려진 한계 / 다음
- 감성 사전은 placeholder — KR-FinBERT 등 모델 스코어러로 교체 여지 (`news/sentiment.py`의 `score_text`만 바꾸면 됨).
- US 워런트/유닛/권리(예: …W, …U, …R 접미사)는 휴리스틱으로 다 못 거름 — 데이터 없으면 자연 탈락.
- PRD가 설계한 **펀더멘털 자동제외·LLM 뉴스분류·주봉 MACD·카탈리스트(실적일정)·쿨다운**은 아직 미구현(스키마/문서는 준비됨). → 다음 통합 후보.
- 전종목 스캔은 외부 API 호출이 많아 느림 → 야간 배치로 SQLite 캐시 워밍 권장.
