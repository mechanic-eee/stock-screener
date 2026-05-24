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
- [x] **[지표고도화] 보조지표 4종 추가** — 상대강도(RS, 시장 대비 초과수익) · OBV 누적매집 · VCP 변동성수축(베이스) · 밸류에이션(PER/PBR/ROE/배당). 절대신호 위주였던 셋에 상대성과·매집·바닥구조·저평가 차원 보강. 총 보조지표 13종. (다음 후보: ATR 손절/사이징, ADX 추세강도, 200DMA 회복, 섹터 상대강도)
- [ ] 감성 스코어러 모델 교체 검토 (KR-FinBERT 등)
- [ ] PRD 미구현분 통합 (추천순 진행 중):
  - [x] **주봉MACD(MTF, §5.4.4)** — 일봉→주봉 리샘플 7-상태 점수, 플러그인 필터(weekly_macd, weight 0.15). 순수 pandas, deadband로 미완성주 가짜크로스 방지.
  - [x] **쿨다운(§5.6)** — cooldown.py + alert_history. 14일 캘린더 쿨다운, +20점 시 재알림. daily_scan 연결.
  - [x] **펀더멘털 자동제외(§5.4.3)** — fundamentals.py(US=yfinance/KR=DART), filters/fundamental.py(weight 0.25), engine 확장패스+캐시테이블. **US+KR(DART) 실데이터 검증 완료.** account_id 매칭·전년동분기 YoY·corp_code 디스크캐시. 키는 .env(DART_API_KEY).
  - [x] **카탈리스트(§5.4.5/§5.5.2)** — catalysts.py(yfinance earnings_dates, US+KR), filters/catalyst.py 보너스필터(임박 ⚠️경고 + 실적후 3거래일내 MACD전환 시 +5), is_bonus 메커니즘(정규화 후 가산, 100초과 가능), engine 보너스패스+catalysts 캐시테이블. US+KR 실데이터 검증 완료.
  - [ ] **LLM 뉴스분류(§5.4.2)** — Anthropic 키(유료)+뉴스 파이프라인 실사용화 선행 필요(현재 백로그).
- [x] **[버그수정] enrichment 필터 무음 먹통** — "필터 적용해도 결과 수·순서가 안 바뀜". 원인: RS/밸류/펀더가 호스팅에서 외부데이터 fetch 실패 시 전 종목 중립50→안 걸러지고+순위 불변. ⓐ FilterOutcome.available 플래그 + engine diag 집계 + 앱 경고(투명성). ⓑ 벤치마크를 스냅샷 사이드카(benchmarks.parquet)로 구워 daily_scan 발행·앱 prime→RS가 라이브fetch 없이 작동. 재현/AppTest 검증 완료.
- [x] **[버그수정 후속/B확장] 밸류에이션·펀더멘털도 스냅샷 사전계산** — RS 벤치마크 패턴을 밸류/펀더로 확장. snapshot.export_valuations/export_fundamentals(스레드 fetch, common/preferred만)→`valuations.parquet`·`fundamentals.parquet` 사이드카, app이 로드 시 prime_*로 인메모리 캐시 시드, valuation/fundamentals 모듈에 prime() 추가(benchmark.prime 패턴). daily-scan.yml에 DART_API_KEY 주입 + 사이드카 발행. db busy_timeout(스레드 쓰기 안전). 라운드트립+엔진 e2e(poisoned 라이브 경로 미접촉, diag[0,1]) 검증 완료. **DART 시크릿 등록 완료(2026-05-24), workflow_dispatch run(26363069143) 발행 → KR 밸류 559/612·펀더 561/612·US 펀더 1287/2416 검증.** 후속: US 밸류가 Actions에서 `.info`+`fast_info` 둘 다 차단으로 0/2399 → **US 시총=종가×재무제표 주식수**(재무상태표 엔드포인트는 Actions 작동)로 해결. fundamentals.shares 컬럼+마이그레이션, valuation에 last_price 전달, US 구캐시 자가치유 재페치. 로컬검증(.info+fast_info 둘다 차단 시뮬) PBR=.info와 일치. **재실행(run 26364830729) 확증 완료: US 밸류 0→1894/2399, US 펀더 2058/2399, KR 밸류 565·펀더 567. 4개 enrichment 전부 클라우드 작동. B확장 완료.**
- [x] **결과를 stock-investing 워치리스트로 보내는 연결** — scripts/to_watchlist.py: 최신 클라우드 스냅샷(또는 --csv/--snapshot)에서 점수상위 N(기본10) 또는 --tickers 선택 → stock-investing/WATCHLIST.md에 관심행 병합. KR/US 테이블 자동 분기, 티커 중복 방지(멱등), 논거(낙폭·점수)·진입구간(현재가) 자동초안+손절/촉매 TBD, --market/--min-score/--dry-run. 첫 시드 10종목(KR3·US7) 기록.
  - **(2026-05-25) 지표가중 랭킹 옵션 추가**: `--indicators KEY... | all`로 base+선택지표 합성점수 랭킹(엔진 apply_filters 재사용, 각 지표 기본파라미터=스코어러+게이트), `--weights key=w,...` 가중오버라이드, `--list-indicators`. CSV 소스는 가격없어 차단. 사이드카 prime로 RS/밸류/펀더 오프라인 동작. 검증: base-only=전부 100점 → RS+펀더+밸류 켜니 후보 3215→2848(펀더가 가치함정 게이트), 점수 91~98 분산·종목 변별(NVO·RELY 등).
- [x] **[클라우드 배포 완료]** GitHub repo(mechanic-eee/stock-screener, public, main) push, gh CLI 설치, Actions 일일 워크플로우, Streamlit Cloud 연결(사용자, Python 3.12, SNAPSHOT_URL/APP_PASSWORD). 첫 KR 실행 성공(24분)→data 브랜치 스냅샷, raw URL 로드 검증.
- [x] **스케줄 설정**: 평일만(cron 0 22 * * 1-5 = 화~토 07:00 KST), KR+US, 전 종목유형, 임계 −50%, 텔레그램 상위 15.
- [x] **시장·종목유형 표시 필터** + 사이드바 재배치(데이터소스↔보조지표 사이). security_type을 스냅샷까지 실어나름.
- [~] **[다음] 뉴스 필터 실사용화** — 현재 NewsAPI 무료는 (a)배포서버 차단=로컬전용, (b)영어전용→KR 종목 매칭 안됨, (c)100req/일, (d)앱에 캐시 없어 재실행마다 재요청.
  - [x] **① 일일 뉴스 캐시** (2026-05-25): `news_cache` 테이블(source,query,lookback PK) + `news/cache.py`(load/save, 같은 UTC날짜만 유효) + `news.fetch_cached`로 build_bundle 래핑. 같은날 중복쿼리=캐시, None(실패)은 미캐시→재시도. (c)·(d) 해결. 검증: 페이크 프로바이더 네트워크호출 카운트.
  - [ ] **② 네이버 검색 API 연동** (KR 한글 뉴스) — 사용자가 NAVER client ID/secret 발급 예정. 발급 후 NaverNewsProvider 추가 + market별 provider 선택(KR→naver, US→newsapi), title/description HTML 태그 스트립. 무료 25,000req/일.
  - [ ] **③ 감성 모델 교체**(KR-FinBERT 등) — Python 3.14+클라우드에서 torch 휠/모델크기 리스크로 보류. 대안: 사전 보강 또는 외부 감성 API.
  - 미국+로컬+마지막필터로 쓰면 무료로도 충분(요청=뉴스단계 도달 종목수).
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
- (2026-05-23) **PRD 미구현분은 난이도·외부의존성 순으로 진행**(주봉MACD→쿨다운→펀더멘털→카탈리스트→LLM). 이유: 키·비용 없는 것부터 즉시 ROI. 주봉MACD는 기존 필터 플러그인 패턴에 그대로 얹어 UI·스캔에 자동노출, 쿨다운은 이미 비어있던 alert_history 테이블 활용. 외부 키 필요 시점(펀더멘털=DART, LLM=Anthropic)에 멈춰 사용자 확인.
- (2026-05-23) **지표 고도화는 "orthogonal 차원 채우기" 원칙**으로 선정. 기존 셋이 전부 *절대* 신호(낙폭·모멘텀·거래량·추세)라, 빠진 차원을 보강: 상대강도(시장 대비, 모멘텀 문헌 최강 팩터) · OBV(스파이크 아닌 *지속* 매집) · VCP(falling knife 직격: 하락이 끝나고 다지는지) · 밸류에이션('빠진 것'≠'싼 것'). 단순 오실레이터 추가(스토캐스틱·CCI 등)는 RSI와 중복이라 보류. 모두 기존 플러그인 패턴(스코어러+min_score 게이트화)에 그대로 적재. RS 벤치마크/밸류는 enrichment로 survivors만 fetch(비용 계층화).
- (2026-05-23) **카탈리스트 실적일정은 yfinance get_earnings_dates로 US+KR 모두 처리**(KR은 .KS/.KQ 접미사). 대안: 38커뮤니케이션 스크레이핑 → 취약하고 불필요해 폐기. **보너스는 가중평균이 아닌 합산-후-가산(is_bonus 메커니즘)**: PRD §5.5.2가 catalyst_bonus를 점수 합산 후 +5(100 초과 가능)로 정의 → Filter.is_bonus 플래그를 신설해 wsum/sscore에서 제외하고 정규화 점수에 직접 가산. 보너스 조건은 "스크리너가 잡은 최근 MACD 전환이 직전 실적 직후 N거래일 내"로 해석(전환과 실적을 연결), 오래된 실적의 과거 전환은 미인정. app.py는 보너스필터에 가중치 슬라이더 숨김.
- (2026-05-23) **DART 계정 매칭은 IFRS account_id 우선**(한글명 fallback). 이유: fnlttSinglAcntAll의 한글 account_nm은 세그먼트/하위라인이 키워드를 포함해 오매칭 위험 → ifrs-full_Revenue/dart_OperatingIncomeLoss 등 표준 태그가 연결총계 단일라인이라 안전. **YoY는 frmtrm(전년비교) 대신 전년 동분기 보고서를 별도 fetch**(DART IS 라인이 frmtrm 미제공 케이스 多). corp_code 맵은 디스크 캐시(corpCode 엔드포인트가 레이트리밋 시 zip 대신 HTML 반환 → PK매직바이트 검사로 거부). 분기누적 특성상 4Q연속적자는 보고서 2개(현·전년동분기)로 판정불가 → False 유지.
- (2026-05-24) **밸류/펀더 사전계산은 RS 벤치마크 사이드카 패턴을 그대로 재사용.** 대안 검토: ⓐ screener.db(수백MB)를 data 브랜치에 발행 → 너무 무겁고 tickers/fundamentals 테이블 전부 필요. ⓑ 원시 재무행만 발행 → KR 밸류는 market_cap(tickers 테이블)도 필요해 호스트 재계산 불가. 채택: **계산된 Bundle 자체를 ticker별 작은 parquet로 굽고**, valuation/fundamentals 모듈에 `prime()` 인메모리 캐시를 둬 `get_*`가 캐시 우선 반환(라이브 fetch 0). enrichment 대상은 common/preferred만(ETF/SPAC/워런트는 PER·재무 무의미→제외해 런타임 절감). fetch는 네트워크 I/O라 ThreadPoolExecutor(기본 8)로 팬아웃, 각 fundamentals fetch가 SQLite에 쓰므로 db에 busy_timeout=30s 추가(동시쓰기 lock 회피). 순서는 fundamentals→valuation(KR 밸류가 펀더 SQLite 캐시 재사용). fail-soft 유지: 키/데이터 없으면 available=False→중립50. **트레이드오프:** 스캔 런타임 증가(첫 실행, common 생존자 수×fetch). 펀더는 SQLite 80일 캐시라 반복 실행은 저렴, 밸류 US .info는 매 실행 라이브.
- (2026-05-23) **펀더멘털은 enrichment 패스로 survivors만 fetch**(news와 동일 패턴). 이유: yfinance/DART는 비싼 외부호출 → 기술필터 통과 종목에만 지불. 키 없거나 데이터 부재 시 available=False→중립50점·제외안함(PRD fail-soft). YoY는 시장무관하게 "현재기준 ~365일 전" 비교행을 날짜거리로 탐색(US 분기누락·KR 단일 전년치 모두 대응). 4Q연속적자는 분기 4개 필요 → KR(DART 단일보고서)에선 판정불가로 보수적 False. **DART는 키 없어 미검증** — corp_code맵+fnlttSinglAcntAll 코드만 작성, 키 발급 후 실검증 필요. daily_scan 기본 selected={}라 펀더멘털은 UI 토글 시에만 동작(클라우드 대량 비용 회피).
- (2026-05-23) **주봉MACD는 게이트 아닌 스코어러로 기본동작**(min_score=0). 이유: PRD §5.4.4의 MTF는 enrichment 점수항(가중 0.15)이지 hard 게이트가 아님 → 기본은 종목을 제외하지 않고 점수만 기여, min_score를 올리면 게이트로 전환 가능(플러그인 일관성 유지). 미완성 최근주(부분주봉) wobble이 near-zero diff를 가짜 시그널돌파로 만드는 것을 가격 0.1% scale-aware deadband(양변 적용)로 차단.

## 리스크
- yfinance/pykrx의 Python 3.14 호환성 미검증 → 스모크 테스트에서 확인. 실패 시 3.12 venv로 대안.
- 감성 사전은 조잡한 placeholder — 신호 품질 검증 전엔 뉴스 필터 결과를 과신 금지.
- 외부 API(yfinance/NewsAPI) 레이트리밋 → 대량 스캔 시 캐시·배치 필수.
