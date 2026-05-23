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
## [2026-05-23] stock-screener | fix | adj_close NaN으로 인한 NOT NULL 위반이 스캔 전체를 죽이던 버그: fetch에서 adj_close←close 보강+빈행 제거, save를 종목별 try로 격리. 200종목 무중단 검증.
## [2026-05-23] stock-screener | work | 종목 유형 분류/필터 추가: security_type(common/etf/etn/spac/preferred/warrant_unit/fund) 분류·저장(tickers 컬럼+마이그레이션), build_universe(include_types) 기본=보통주, UI 멀티셀렉트+scan --types. US 분류 검증: 보통주5108/ETF1285/유닛1236/펀드405/SPAC205/우선주130. ADS는 보통주 유지(우선주 오분류 수정).
## [2026-05-23] stock-screener | fix | 유니버스 캐시가 시장 구분 없이 전역 신선도만 봐서 KR 요청시 빈 목록(0종목) 반환하던 버그 → 시장별 신선도(universe_built_at:<market>)+시장별 저장으로 수정
## [2026-05-23] stock-screener | fix | pykrx 1.2.8이 KRX 로그인(KRX_ID/PW) 요구해 KR 목록·시세 실패 → KR 데이터소스를 FinanceDataReader로 교체(로그인불요, 수정주가, StockListing+DataReader). KR 보통주 1,448종목 확인.
## [2026-05-23] stock-screener | work | KR 전종목 스캔: 보통주 1,448 중 -80%↓ 98종목. 점수순(하락 종곡선) 상위 보고.
## [2026-05-23] stock-screener | work | [클라우드 배포] 풀클라우드 스캐폴딩: snapshot.py(후보 parquet), scripts/daily_scan.py, 앱 호스팅모드(스냅샷)+비번게이트, GitHub Actions 일일워크플로우(→data 브랜치), DEPLOY.md. 스냅샷 왕복·AppTest·전스크립트 파싱 검증. gh 미설치라 repo push는 사용자 작업.
## [2026-05-23] stock-screener | handoff | GitHub repo 생성·배포(mechanic-eee/stock-screener, main), gh CLI 설치, Actions 첫 KR 실행 성공(24분)→data 브랜치 스냅샷, Streamlit Cloud 연결 완료(사용자). raw URL 로드 검증.
## [2026-05-23] stock-screener | work | 스케줄 스캔 설정 변경: 평일만(cron 0 22 * * 1-5), KR+US, 전 종목유형(ETF/ETN 등 포함), 임계 -50%. daily_scan에 --types 추가. -50%에서 KR 보통주 564종목 확인.
