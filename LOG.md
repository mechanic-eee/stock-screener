# LOG — stock-screener

## [2026-05-23] stock-screener | start | 폭락주 스크리너 프로젝트 생성 (Streamlit, KR+US, 플러그인 필터)
## [2026-05-23] stock-screener | work | 코어 구현: models/indicators/filters(6종)/data/news/engine/app.py/scan.py + 문서·requirements
## [2026-05-23] stock-screener | fix | macd shift fillna 다운캐스트 경고 제거, scan.py stdout UTF-8 강제(Windows cp949 대응)
## [2026-05-23] stock-screener | work | venv(py3.14) 설치+스모크: 합성데이터 필터 로직 OK, yfinance 실데이터 8종 스캔 end-to-end OK. git 2커밋.
## [2026-05-23] stock-screener | work | [통합] 기존 OneDrive 프로젝트 분석(PRD+코드) → 데이터계층·점수모델·백테스트·텔레그램 흡수
## [2026-05-23] stock-screener | work | [통합①④] 실 유니버스(NASDAQ Trader US 8.3K→5.6K활성, pykrx KR)+견고한 시세수집, pickle→SQLite(screener.db) 전환, 엔진 무변경
## [2026-05-23] stock-screener | work | [통합②] 점수모델: scoring.py 곡선 + FilterOutcome.score + 가중합성점수/순위 + UI 가중치. 검증: AAPG -56%+MACD당일 85.2점 최상위, -97% 상폐위험 40점
## [2026-05-23] stock-screener | work | [통합③] calibrate_gates.py 이관+export_prices.py, 합성데이터 13변형 OFAT 검증
## [2026-05-23] stock-screener | fix | calibrate make_report 상위폴더 생성, db get_connection 스키마 자동초기화
