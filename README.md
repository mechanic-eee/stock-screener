# stock-screener — 5년 고가 대비 폭락주 스크리너

> 관련: 리서치/결정은 `..\stock-investing\` (워치리스트·결정 로그). 이 레포는 **후보를 자동으로 찾는 도구**다. 여기서 나온 후보를 stock-investing 워치리스트로 옮겨 추적한다.

## 무엇을 / 왜
종가 기준 **최근 N년(기본 5년) 최고가 대비 일정 비율(기본 −80%) 이상 폭락**한 종목을 기본 후보로 잡고, **보조지표 필터를 켜고/끄고 파라미터를 조정**하며 후보를 좁혀 "매수할 만한 바닥주"를 찾는다. 단순 하락이 아니라 MACD 전환·거래량 급증·긍정 뉴스 같은 신호를 더해 가능성을 높이는 게 목적.

## 스택
- Python 3.x / pandas (지표는 순수 pandas 계산 — 외부 TA 의존성 없음)
- 시세: `pykrx`(한국) · `yfinance`(미국)
- 뉴스: NewsAPI(키 있을 때) + 경량 감성 사전 — **플러그인 구조라 교체 가능**
- UI: Streamlit 대시보드

## 구조
```
app.py                 Streamlit 대시보드 (필터 토글·파라미터 자동 렌더)
scan.py                CLI 배치 스캔 / 스모크 테스트
config/                us_universe.csv (선택), 설정
src/screener/
  models.py            TickerData / Filter / Param / FilterOutcome
  indicators.py        MACD·RSI·볼린저·MA·하락률 (pure pandas)
  engine.py            build_candidates(무거움) + apply_filters(빠름)
  data/                universe·prices·cache (pickle 캐시)
  filters/             base(레지스트리) + 각 지표 필터 1파일씩
  news/                provider(추상화) + sentiment + 집계
data/                  시세/유니버스 캐시 (gitignore)
```

## 설계 핵심
- **수집(배치)과 필터링(인터랙티브) 분리:** 전종목 5년 시세를 매번 라이브로 못 긁으니, `build_candidates`가 시세를 캐시하고 기본 −80% 필터로 후보를 수십~수백으로 압축 → Streamlit은 그 위에서 보조지표를 즉시 재적용.
- **필터 = 플러그인:** `src/screener/filters/`에 파일 하나 추가하고 `@register`만 하면 엔진·UI에 자동 노출. 각 필터가 자기 `Param`(기본값·범위)을 선언 → UI 컨트롤 자동 생성.
- **뉴스는 마지막에:** 네트워크 I/O라 기술필터 통과 종목에만 적용. 키 없으면 자동 비활성.

## 실행
```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # NewsAPI 키 쓸 거면 채우기 (선택)

# 빠른 동작 확인 (UI 없이)
python scan.py --markets US --limit 15
python scan.py --markets US --limit 50 --macd

# 대시보드
streamlit run app.py
```

## 미국 전종목 확장
`config/us_universe.csv` (`ticker,name`) 를 두면 그 목록을 쓴다. 없으면 시드(대형주 15개)만 스캔. 전체 목록은 NASDAQ Trader의 상장 파일(nasdaqlisted.txt / otherlisted.txt)을 받아 ticker,name 두 컬럼으로 변환해 넣으면 된다.

## 알려진 한계 / 다음
- 감성 사전은 placeholder — KR-FinBERT 등 모델 스코어러로 교체 여지 (`news/sentiment.py`의 `score_text`만 바꾸면 됨).
- 한국 전종목 스캔은 pykrx 호출이 많아 느림 → 야간 배치로 캐시 워밍 권장.
- yfinance/pykrx의 Python 3.14 호환성은 설치 시 확인 필요(미지원이면 3.12 권장).
