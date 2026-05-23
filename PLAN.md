# PLAN — stock-screener

## 현재 목표
종가 기준 5년 고가 대비 폭락주를 기본 후보로 잡고, 보조지표(MACD·RSI·거래량·MA·볼린저·뉴스)를 토글+파라미터 조정으로 얹어 매수 후보를 좁히는 Streamlit 도구. 한국+미국 동시.
**현재 상태: 클라우드 배포 완료** — GitHub(mechanic-eee/stock-screener) + Actions 일일 스캔(평일 22:00 UTC → data 브랜치 스냅샷) + Streamlit Cloud 호스팅(비번 보호). 로컬은 run_app.bat / 바탕화면 아이콘.

## 다음 할 일
- [x] 아키텍처 결정 (수집/필터링 분리, 플러그인 필터, 뉴스 마지막)
- [x] 필터 레지스트리 + 기본 하락 필터 / 기술지표 5종 / 뉴스 필터
- [x] 엔진 + Streamlit 앱 + CLI(scan.py)
- [x] venv 설치 + 스모크 테스트 (Python 3.14 호환 OK)
- [x] **[통합①]** 실 유니버스: US=NASDAQ Trader 전종목(8.3K, 제외후 5.6K 활성), KR=pykrx+시총필터 + 견고한 시세수집(재시도/백오프/adj_close)
- [x] **[통합④]** SQLite 영속화 (pickle→`data/screener.db`, 인터페이스 유지로 엔진 무변경)
- [x] **[통합②]** 점수 모델: FilterOutcome에 score(0~100), PRD 점수곡선(scoring.py), 가중 합성점수+순위, UI 가중치 슬라이더
- [x] **[통합③]** 캘리브레이션 백테스트 이관(backtest/) + SQLite→parquet 추출기, 합성데이터 검증
- [x] **[통합]** 텔레그램 알림 이관, PRD/방법론 문서 docs/로 이관
- [x] **종목 유형 분류/필터**: security_type(보통주/ETF/ETN/SPAC/우선주/워런트유닛/펀드) 분류·저장 + 스캔 시 포함유형 선택(기본=보통주). UI 멀티셀렉트 + CLI --types.
- [x] 종목유형 분류 정밀도 개선(US): "Trust" 운영사/REIT→보통주(fund 오분류 해결), 채권성(Senior/Subordinated Notes)→fund 분리, 클래스주(BRK.A) 보통주 유지(티커 '.' 규칙 제거), UiPath etn 오탐 수정(브랜드명 단어경계). 단 US ETN은 NASDAQ 심볼파일이 식별정보 미제공으로 여전히 탐지 거의 0(오탐은 없음) — 정밀 ETN 분류는 별도 데이터소스 필요(백로그).
- [ ] 감성 스코어러 모델 교체 검토 (KR-FinBERT 등)
- [ ] PRD 미구현분 통합 후보: 펀더멘털 자동제외(DART/yfinance) · LLM 뉴스분류 · 주봉MACD · 카탈리스트(실적일정) · 쿨다운
- [ ] 결과를 stock-investing 워치리스트로 보내는 연결(수동/CSV)
- [x] **[클라우드 배포 완료]** GitHub repo(mechanic-eee/stock-screener, public, main) push, gh CLI 설치, Actions 일일 워크플로우, Streamlit Cloud 연결(사용자, Python 3.12, SNAPSHOT_URL/APP_PASSWORD). 첫 KR 실행 성공(24분)→data 브랜치 스냅샷, raw URL 로드 검증.
- [x] **스케줄 설정**: 평일만(cron 0 22 * * 1-5 = 화~토 07:00 KST), KR+US, 전 종목유형, 임계 −50%, 텔레그램 상위 15.
- [x] **시장·종목유형 표시 필터** + 사이드바 재배치(데이터소스↔보조지표 사이). security_type을 스냅샷까지 실어나름.
- [ ] **[다음] 뉴스 필터 실사용화** — 현재 NewsAPI 무료는 (a)배포서버 차단=로컬전용, (b)영어전용→KR 종목 매칭 안됨, (c)100req/일, (d)앱에 캐시 없어 재실행마다 재요청. 할 일: ① 일일 뉴스 캐시 추가(무료 한도 여유), ② 네이버 검색 API 연동(KR 한글 종목 뉴스), ③ 감성 모델 교체(KR-FinBERT 등). 미국+로컬+마지막필터로 쓰면 무료로도 충분(요청=뉴스단계 도달 종목수).
- [ ] 전종목 일일 스캔 런타임/비용 튜닝: 전 유형 KR+US ≈ 1만 종목 → 1.5~2.5h(첫 실행). public이라 분 무제한이나 길면 워런트/유닛 제외 또는 US 주1회 등 고려.

## 결정 로그
- (2026-05-23) 인터페이스=Streamlit, 유니버스=KR+US 동시, 뉴스=처음부터. (사용자 선택)
- (2026-05-23) **수집(배치) vs 필터링(인터랙티브) 분리.** 대안: 매 요청마다 전종목 라이브 조회 → 수천 종목이라 대시보드가 수 분씩 멈춤. 채택: build_candidates가 시세 캐시+기본필터로 후보를 압축, apply_filters는 캐시 후보 위에서 즉시 동작. trade-off: 캐시 신선도 관리 필요(파일 mtime 기반 max_age).
- (2026-05-23) **지표를 순수 pandas로 자체 구현**(pandas-ta/TA-Lib 미사용). 이유: Python 3.14가 매우 최신이라 바이너리 의존성 휠 공백 위험 + MACD/RSI는 구현이 단순 + 확장 용이. trade-off: 지표 정확성 직접 책임.
- (2026-05-23) **필터 = 레지스트리 플러그인 + Param 스펙.** 새 지표는 파일 1개 추가+@register로 끝, UI 컨트롤은 Param에서 자동 생성. 이유: 사용자가 "다양한 보조지표 추가" 요구 → 확장 비용 최소화가 핵심.
- (2026-05-23) **캐시 포맷=pandas pickle**(parquet/pyarrow 대신). 이유: pyarrow의 3.14 휠 불확실. trade-off: 포맷 이식성↓(로컬 캐시라 무관).
- (2026-05-23) **뉴스 필터는 파이프라인 마지막 + 키 없으면 fail-closed.** 이유: 네트워크 I/O 비용을 통과 종목에만 지불, 키 없을 때 에러 대신 "뉴스없음"으로 비활성.
- (2026-05-23) **US 유니버스는 CSV 주입식**(yfinance에 상장목록 API 없음). 시드 15개 기본, config/us_universe.csv로 확장.
- (2026-05-23) **[통합] 기존 OneDrive 프로젝트(`C:\Users\yoobg\OneDrive\project\stock-screener`)에서 자산 흡수.** 그쪽은 데이터인프라(SQLite·전종목 유니버스·견고한 수집)+정량 점수모델(PRD)이 강하고, 우리는 플러그인 구조+Streamlit이 강해 상호보완. 결정: **우리 골격 유지 + 기존의 데이터계층·점수모델·백테스트·텔레그램 흡수**. 작업은 Claude_work 쪽에서 계속.
  - US 유니버스 CSV 주입식 → NASDAQ Trader 공식목록 라이브 빌더로 대체(시드 15 → 전종목). trade-off: 빌드시 다운로드 필요하나 7일 캐시.
  - pickle 캐시 → SQLite. 이유: 수천 종목 확장성·쿼리·향후 enrichment 테이블. 인터페이스(load/save_prices) 유지해 엔진 무변경.
  - 필터를 pass/fail → **게이트=필터+0~100 스코어러**(PRD §5)로 업그레이드. 비선형 점수곡선으로 "적당한 하락+모멘텀"이 극단하락보다 높게 순위.
  - 지표는 계속 순수 pandas(pandas-ta 미도입) — 점수곡선까지 자체 구현.
  - PRD의 enrichment(LLM뉴스분류·펀더멘털·카탈리스트)는 외부API·비용 커서 이번엔 스키마/문서만 이관하고 미구현으로 백로그.
- (2026-05-23) **KR 데이터소스 pykrx → FinanceDataReader.** 이유: pykrx 1.2.8이 KRX 로그인(KRX_ID/PW) 요구해 빈 응답. FDR은 로그인불요+수정주가+빠름(StockListing/DataReader). trade-off: 의존성 추가.
- (2026-05-23) **풀 클라우드 = GitHub Actions(스캔) + data 브랜치(스냅샷) + Streamlit Cloud(UI).** git/GitHub는 앱을 서빙 못함 → 무거운 스캔은 Actions가 미리, 결과 스냅샷(작은 parquet)만 data 브랜치에 force-push(히스토리 thin), 앱은 raw URL로 읽어 즉시 표시+인터랙티브. DB(수백MB)는 git에 안 넣음(Actions 캐시). 비번은 st.secrets APP_PASSWORD(없으면 공개).
- (2026-05-23) **뉴스 필터 실사용화는 다음으로 연기.** 가능성 확인됨(미국+로컬+마지막필터면 무료로 충분), 그러나 무료 NewsAPI 배포서버 차단·영어전용(KR 불가)·캐시없음 → 제대로 쓰려면 캐시+네이버API+감성모델이 필요. 사용자 결정으로 백로그.

## 리스크
- yfinance/pykrx의 Python 3.14 호환성 미검증 → 스모크 테스트에서 확인. 실패 시 3.12 venv로 대안.
- 감성 사전은 조잡한 placeholder — 신호 품질 검증 전엔 뉴스 필터 결과를 과신 금지.
- 외부 API(yfinance/NewsAPI) 레이트리밋 → 대량 스캔 시 캐시·배치 필수.
