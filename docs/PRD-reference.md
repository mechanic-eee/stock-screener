# PRD: 다중 시장 가치·모멘텀 주식 스크리너

**Multi-Market Value-Momentum Stock Screener**

---

## 문서 정보

| 항목 | 내용 |
|---|---|
| 버전 | v1.0 |
| 작성일 | 2026-05-05 |
| 작성자 | Yoo Byung-gwan |
| 상태 | 구현 착수 가능 |
| 변경 요약 | v0.2 검증 결과 6개 카테고리(정밀 정의, 수식, 운영·인프라, 엣지 케이스, 일관성, 데이터 무결성)의 누락·모호성을 모두 보완. 모든 점수 공식 명시. 영속화·백필·동시 실행 보호 운영 규약 추가. |

---

## 1. 개요

### 1.1 배경

장기 가치 회복 가능성이 있는 종목을 매일 시장에서 자동으로 발굴하고 싶다. 직접 수백~수천 종목을 매일 차트로 확인하는 것은 비현실적이며, 가격·모멘텀·정성정보를 결합한 시그널을 자동으로 받아 본인의 투자 의사결정에 보조 자료로 활용하고자 한다.

본 시스템은 매수 신호를 자동 실행하는 트레이딩 시스템이 아니다. 사용자가 직접 추가 분석 후 의사결정을 내리는 데 사용하는 **스크리닝 보조 도구**이다.

### 1.2 목적

한국과 미국 주식시장을 매일 종가 기준으로 스캔하여, 다음 조건을 모두 만족하는 종목을 텔레그램으로 알린다.

1. 5년 최고점 대비 일정 비율 이상 하락 (사용자 조정 가능)
2. 일봉 MACD가 최근 N거래일 이내에 음에서 양으로 전환
3. MACD 전환에 거래량 동반
4. 가치 함정 가능성을 줄이는 재무·뉴스 정성 검토 통과

### 1.3 핵심 가치 제안

매일 후보 종목을 받아 의사결정 시간을 분 단위로 단축하고, 가격·모멘텀·거래량의 빠른 게이트로 노이즈를 차단한 뒤 뉴스·재무 정보로 우열을 변별한다. 본인 투자 스타일에 맞춰 임계치를 조정 가능하며, GitHub 기반 무인 운영으로 별도 서버가 필요 없다.

---

## 2. 목표 및 비목표

### 2.1 목표

- 본 PRD에 정의된 모든 기능을 v1.0에 통합 구현 (선택적 적용 없음)
- 매일 KR 장 마감, US 장 마감 후 자동 실행
- KR + US 양 시장의 의미 있는 거래량을 가진 전 종목을 매일 스캔
- 사용자가 임계치(하락률, MACD 윈도우, 거래량 배수, 점수 가중치 등)를 코드 수정 없이 `config.yaml`로 조정 가능
- 텔레그램으로 종목별 컨텍스트(가격, 하락폭, 점수 분해, 뉴스 요약, 카탈리스트, 시장 국면)와 함께 알림
- 룰셋의 과거 성과를 검증할 수 있는 백테스트 환경 제공

### 2.2 비목표

- **자동 매매·주문 실행 기능을 포함하지 않는다.**
- 실시간 또는 분 단위 알림을 목표로 하지 않는다 (일 1회로 충분).
- 다인 서비스가 아니다. UI/멀티테넌시/사용자 관리 미포함.
- 옵션·선물·코인 등 주식 외 자산은 범위 외.
- 매수·매도 추천 자체를 생성하지 않는다 (검토할 후보를 제시할 뿐).

---

## 3. 사용자 및 사용 시나리오

### 3.1 사용자

본인 1인. 한국어 사용. 텔레그램 사용자. 본인이 운영자이자 사용자이며, 코드를 직접 수정·확장한다.

### 3.2 일일 사용 시나리오

KR 시장의 정규장 마감은 15:30 KST이다. 단일가 매매 종료(16:00 KST) 직후의 종가가 확정되므로, 시스템은 16:30 KST에 트리거되어 60분 이내 알림을 발송한다.

US 시장의 정규장 마감은 EST 16:00 (또는 EDT 16:00)이다. KST로는 EST 기준 06:00, EDT 기준 05:00에 해당하므로, 시스템은 KST 06:30(EST 시즌)~07:00(EDT 시즌)에 트리거되도록 cron을 설정한다.

```
KR
  15:30 KST  KR 정규장 마감
  16:00 KST  종가 확정 (단일가 매매 종료)
  16:30 KST  GitHub Actions 트리거
  17:30 KST  KR 시장 알림 텔레그램 수신 (목표)

US
  06:00 KST  US 정규장 마감 (EST 16:00 = KST D+1 06:00)
  06:30 KST  GitHub Actions 트리거 (EDT 시즌은 30분 더 여유)
  07:30 KST  US 시장 알림 텔레그램 수신 (목표)
```

### 3.3 주간/월간 활용

주 1회 누적 알림 종목의 추적 결과를 자체 리뷰하고, 월 1회 룰셋 임계치 점검 및 조정, 분기 1회 백테스트 재실행으로 전략 유효성을 검증한다.

---

## 4. 시스템 아키텍처 및 설계 원칙

### 4.1 funnel 구조 (비용 계층 분리)

본 시스템은 funnel 구조를 채택한다. 캐시된 시세 데이터로 즉시 계산 가능한 **싼 연산을 앞단(게이트)에 배치**하여 후보를 좁히고, 외부 API 호출이 필요한 **비싼 연산(뉴스 수집, LLM 분류, 재무 데이터 조회)은 게이트를 통과한 소수 종목에만 적용**한다.

```
유니버스 (~1,500종목, 시장당)
      │
      ▼  [Cheap Gates — 캐시 시세만 사용]
Gate 1: 가격 하락폭        → ~120종목
Gate 2: MACD 음→양 전환     → ~25종목
Gate 3: 거래량 동반         → ~12종목
      │
      ▼  [Enrichment — 외부 API 호출, 게이트 통과 종목만]
뉴스 수집 + LLM 분류
펀더멘털 데이터 + 가치 함정 판정
주봉 MACD (다중 시간프레임)
카탈리스트 캘린더
시장 컨텍스트
      │
      ▼  [Scoring & Filtering]
점수 산정 → 임계치 통과 → 쿨다운 검사
      │
      ▼
최종 알림 (~3종목)
```

### 4.2 이중 역할 원칙: Gate AND Scorer

게이트 인자(가격 하락폭, MACD, 거래량)는 통과 여부를 결정함과 동시에 통과 종목 사이에서의 우열을 가리는 점수에도 부분적으로 기여한다. 통과 binary 조건은 §5.3에, 점수 공식은 §5.5에 명시한다.

### 4.3 컴포넌트 구성

| 컴포넌트 | 책임 | 주요 라이브러리 |
|---|---|---|
| `data_collector` | 시세·거래량·기본 메타 수집, 캐시 갱신, 분할·배당 처리 | pykrx, FinanceDataReader, yfinance |
| `indicator` | MACD, 이동평균, 거래량 평균, 하락폭 계산 | pandas-ta, pandas |
| `gate_filter` | 3개 게이트(가격·MACD·거래량) 적용 | pandas |
| `news_collector` | 종목별 최근 뉴스 수집, 본문 유사도 기반 중복 제거 | Naver Search API, NewsAPI, GDELT |
| `news_classifier` | LLM 기반 뉴스 호재/악재/주제 분류 | Anthropic API |
| `fundamental` | 재무 데이터 조회 + 가치 함정 판정 | DART OpenAPI, yfinance |
| `mtf_analyzer` | 주봉 MACD 등 다중 시간프레임 분석 | pandas |
| `catalyst` | 실적 발표 등 카탈리스트 일정 조회 | 38커뮤니케이션, yfinance |
| `market_context` | 지수 추세, 시장 국면 산출 | pykrx, yfinance |
| `scorer` | 다인자 점수 계산, 비선형 점수 곡선 | 자체 |
| `cooldown` | 알림 이력 관리, 중복 차단 | sqlite3 |
| `notifier` | 텔레그램 메시지 포맷팅 및 발송 | requests |
| `state_manager` | SQLite 캐시·이력 통합 관리, 영속화·백업 | sqlite3 |
| `lock_manager` | 동시 실행 방지 | filelock + GitHub Actions concurrency |

### 4.4 데이터 흐름

1. 영속화된 SQLite 복원 (§7.3) → 동시 실행 잠금 획득
2. 유니버스 갱신 (제외 필터 적용)
3. 가격 캐시 갱신 (증분 수집, 분할·배당 검사)
4. 게이트 단계 (모든 유니버스 종목 대상, 캐시 데이터만 사용)
5. 확장 단계 (게이트 통과 종목만, 외부 API 호출)
6. 점수 산정 → 쿨다운 검사 → 알림 후보 확정
7. 텔레그램 발송 → SQLite 영속화 → 잠금 해제

### 4.5 정밀 정의 및 규약

다음은 본 PRD 전체에 걸쳐 적용되는 약속이다. 모호한 표현은 모두 이 절에 따라 해석한다.

#### 4.5.1 시간 단위
- "거래일": 해당 시장의 정규장이 열린 날. 휴장일은 카운트하지 않는다.
- "달력일": 휴장 여부와 무관한 일반 날짜.
- "최근 N일", "직전 N일", "N일 이내": **명시 없으면 거래일 기준**. 단, 다음은 예외:
  - 뉴스 수집 lookback (`enrich.news.lookback_days`): 달력일 기준
  - 카탈리스트 임박 판정 (실적 발표 7일 이내): 달력일 기준
  - 쿨다운 (`cooldown.base_days`): 달력일 기준

#### 4.5.2 시점 포함 여부
- "최근 3거래일 이내": 오늘(T)을 제외한 T−1, T−2, T−3 거래일을 의미. 신호일 자체가 T인 경우 (장중 발생) 제외.
- "직전 20거래일 평균": 오늘 이전 20거래일(T−1 ~ T−20)의 평균. 오늘은 포함하지 않음.
- 부등호: "이상" / "이하" = 등호 포함 (≥, ≤). "초과" / "미만" = 등호 미포함 (>, <).

#### 4.5.3 신호일 결정 규칙
- 0선 돌파일: MACD(DIF)가 직전 거래일까지 음수였고 해당일 양수로 전환된 거래일.
- 시그널 라인 돌파일: MACD가 직전 거래일까지 시그널 라인 이하였고 해당일 상회로 전환된 거래일.
- 윈도우 내 두 신호 모두 발생 시: **더 최근(T가 큰) 날짜를 신호일로 채택**. 두 신호가 같은 날 발생 시 0선 돌파를 우선 표기 (더 강한 신호로 간주).
- 거래량 게이트 검사는 위에서 결정된 단일 신호일 T의 거래량을 직전 20거래일 평균과 비교한다.

#### 4.5.4 수치 표기
- 하락률·수익률·비율은 모두 % 단위로 저장. 음수 부호 보존 (drawdown은 항상 음수).
- 점수는 0~100 정수. 가중 합산 결과 소수점은 반올림.
- 시각은 모두 UTC로 SQLite에 저장. 표시 시 KST로 변환.

---

## 5. 기능 요구사항

### 5.1 유니버스 관리

#### 5.1.1 시장 유니버스 갱신 (FR-UNIV)
- KOSPI + KOSDAQ + NYSE + NASDAQ 전 종목을 매일 갱신한다.
- 시가총액, 일평균 거래대금, 상장일, 섹터(GICS 또는 KRX 업종), 주식 분할·배당 이벤트 정보를 함께 저장한다.

#### 5.1.2 종목 제외 (FR-EXCLUDE)
- KR 관리종목, 투자경고종목, 거래정지종목을 자동 제외한다.
- 시가총액 하한 미만 제외 (KR 1000억원, US 5억 달러 기본).
- 일평균 거래대금 하한 미만 제외 (KR 5억원, US 100만 달러 기본).
- SPAC, 우선주, ETF, 상장 1년 미만 종목 제외.
- 사용자 정의 블랙리스트(`config.yaml: exclude_tickers`) 지원.
- 제외 사유는 `tickers.exclude_reason`에 기록한다 (운영 분석용).

### 5.2 데이터 수집 (FR-DATA)

- KR 시세는 pykrx 또는 FinanceDataReader, US 시세는 yfinance로 수집한다.
- **수정주가(adjusted close)를 사용한다.** 분할·배당으로 보정된 종가만이 5년 추세 분석에 일관성을 가지므로.
- 5년치 일봉(시가·고가·저가·종가·수정종가·거래량)을 SQLite에 캐시한다.
- 매 실행 시 마지막 저장일 이후만 증분 수집한다.
- **분할·배당 이벤트 검출**: 매 실행 시 지난 7거래일 동안 split factor나 dividend가 발생한 종목은 5년치 전체를 재수집한다 (수정주가 재계산).
- 시장 휴장일을 자동 감지한다 (KR: KRX 휴장일 캘린더, US: NYSE 휴장일 캘린더). 양 시장 휴장일은 독립 처리된다.
- 종목별 수집 실패 시 로그를 기록하고 다음 종목으로 진행한다 (전체 중단 금지).
- 모든 외부 API 호출은 재시도 로직(최대 3회, 지수 백오프 1s/2s/4s)을 가진다.

### 5.3 게이트 단계 (Cheap Gates)

게이트는 캐시된 시세 데이터만으로 판정한다. **모든 게이트를 통과한 종목만 확장 단계로 진입한다.**

#### 5.3.1 가격 하락폭 게이트 (FR-GATE-PRICE)

**통과 조건**:
```
max_close_5y = max(close[T−5y : T])
drawdown_pct = (close[T] − max_close_5y) / max_close_5y × 100
PASS if drawdown_pct ≤ −min_drawdown_pct  (기본 −50)
```

데이터 처리 규칙:
- 5년치 데이터가 없는 신규 상장주는 상장 이후 최고점을 사용한다.
- 거래일 기준 250일 미만 데이터인 종목은 §5.1.2에 의해 유니버스에서 제외된다.

**점수 기여 (gate_residual의 1/3)**: 비선형 종 모양 곡선. `d = |drawdown_pct|`로 정의:

| 구간 | 점수 |
|---|---|
| d < 50 | 0 (게이트 실패, 도달 불가) |
| 50 ≤ d < 65 | 50 → 100 (선형 보간) |
| 65 ≤ d < 80 | 100 → 70 (선형 보간) |
| 80 ≤ d < 90 | 70 → 20 (선형 보간) |
| 90 ≤ d ≤ 95 | 20 → 0 (선형 보간) |
| d > 95 | 0 (상폐 위험) |

#### 5.3.2 MACD 모멘텀 게이트 (FR-GATE-MACD)

표준 파라미터(EMA 12, 26, Signal 9)로 MACD를 계산한다 (수정주가 기준).

**통과 조건**:
- **0선 돌파**: 직전 N거래일 (`gates.macd.window_days`, 기본 3) 이내에 MACD(DIF)가 음에서 양으로 전환
- **시그널 라인 돌파**: 직전 N거래일 이내에 MACD가 시그널 라인을 상향 돌파
- 둘 중 하나라도 만족하면 통과
- 신호일과 신호 종류는 §4.5.3 규칙으로 결정

**점수 기여 (gate_residual의 1/3)**:

`age = T − 신호일 (거래일 단위)`, `type_bonus = 10 if zero_cross else 0`

| age | 기본 점수 | + type_bonus = 최종 (capped at 100) |
|---|---|---|
| 1 | 90 | 100 (zero) / 90 (signal) |
| 2 | 70 | 80 / 70 |
| 3 | 50 | 60 / 50 |

공식: `score = max(0, 100 − 20×(age−1)) + type_bonus`, capped at 100

#### 5.3.3 거래량 게이트 (FR-GATE-VOLUME)

**통과 조건**:
```
vol_ma20 = mean(volume[T−20 : T−1])     (T 미포함, 20거래일)
volume_ratio = volume[신호일] / vol_ma20
PASS if volume_ratio ≥ multiplier        (기본 1.5)
```

거래량 0인 거래일은 분모·분자에서 제외하고 가용 거래일 평균으로 계산한다.

**점수 기여 (gate_residual의 1/3)**:

| volume_ratio (r) | 점수 | 비고 |
|---|---|---|
| r < 1.5 | 0 (게이트 실패) | — |
| 1.5 ≤ r < 3 | 50 → 100 (선형) | — |
| 3 ≤ r < 5 | 100 | 만점 구간 |
| 5 ≤ r < 10 | 100 → 80 (선형) | 약한 감점 |
| r ≥ 10 | 50 | 작전 의심 플래그 표시 |

`spike_flag = (volume_ratio ≥ 10.0)`인 종목은 알림 메시지에 ⚠️ 마크.

### 5.4 확장 단계 (Enrichment)

확장 단계는 **게이트를 통과한 종목에 대해서만** 외부 API를 호출한다.

#### 5.4.1 뉴스 수집 (FR-ENRICH-NEWS)

- 종목별 최근 N일 (`enrich.news.lookback_days`, 기본 7, 달력일) 동안의 뉴스 수집.
- KR 종목: 네이버 검색 API + 빅카인즈
- US 종목: NewsAPI + GDELT
- 뉴스는 SQLite의 `news` 테이블에 저장 (URL unique).
- **유사 기사 중복 제거**: 같은 종목의 기사 중 제목 유사도(SequenceMatcher ratio) 0.85 이상이면 중복으로 간주, 가장 이른 게시 시각의 기사만 카운트에 포함.
- 종목별 유효 뉴스 건수가 `enrich.news.min_count` (기본 3) 미만이면 점수 감점 (§5.5 참조). 제외하지는 않음.

#### 5.4.2 LLM 뉴스 분류 (FR-ENRICH-LLM)

- 수집된 뉴스 제목 + 첫 단락(최대 500자)을 Anthropic API에 전달.
- 분류 카테고리:
  - **감성**: positive / neutral / negative
  - **주제**: earnings / contract / m_and_a / restructuring / legal_issue / accounting_issue / tech_innovation / industry_trend / other
- 분류 모델: Claude Haiku 4.5 (`enrich.llm.model` 설정).
- Prompt는 `prompts/news_classifier_v{N}.txt`로 버전 관리. 프롬프트 버전이 변경되면 `news.classified_at`이 prompt 파일 mtime보다 이전인 기사를 재분류 대상에 올린다.
- 분류 실패 (API 에러, JSON 파싱 실패) 처리:
  - 재시도 3회 (지수 백오프). 모두 실패 시 해당 기사 분류를 `unknown`으로 저장.
  - 종목 단위로 `unknown` 비율이 50% 초과 시: 해당 종목은 LLM 분류 부재로 간주, 뉴스 점수에 50% 감점 페널티 (제외하지 않음).
- 분류 결과는 SQLite에 영구 저장.
- **자동 제외**: `legal_issue` + `accounting_issue` 합산 비중이 `enrich.llm.auto_exclude_threshold` (기본 0.5) 이상인 종목은 알림 후보에서 제외하고 사유를 `signals.details_json`에 기록.

#### 5.4.3 펀더멘털 (FR-ENRICH-FUND)

- 종목별 최근 4분기 재무 지표 조회 (KR: DART OpenAPI, US: yfinance + SEC EDGAR).
- 분기 보고서 공시일 기준 캐시 (분기 1회 갱신).

**자동 제외 조건** (둘 이상 위반 시):
- 최근 분기 매출 YoY 30% 이상 역성장 (`revenue_yoy < −0.30`)
- 부채비율 300% 초과 (`debt / equity > 3.0`)
- 최근 4분기 모두 적자
- 자본잠식 (`equity ≤ 0`)

**점수 공식**: 3개 부분 점수의 평균.

| 부분 점수 | 입력 | 0~100 매핑 |
|---|---|---|
| `score_revenue_yoy` | revenue_yoy | −30%→0, 0%→50, +20%→100, +20% 이상→100 |
| `score_op_margin` | 영업이익률 | 0%→0, 5%→50, 15%→100, 15% 이상→100 |
| `score_debt` | 부채비율 | 100% 이하→100, 200%→50, 300%→0 |

`score_fundamental = (score_revenue_yoy + score_op_margin + score_debt) / 3`

재무 데이터 부재 시(해외 ADR, 신규 상장 등) 경고 플래그 후 통과시키고 `score_fundamental = 50` (중립값) 부여.

#### 5.4.4 다중 시간프레임 (FR-ENRICH-MTF)

- 일봉 게이트 통과 종목에 대해 주봉 MACD 계산 (캐시된 일봉을 ISO 주차 기준으로 리샘플링, 주의 마지막 거래일 종가 기준).
- 주봉도 표준 MACD 파라미터(12, 26, 9) 사용.

**점수 공식 (`score_mtf`)**:

| 주봉 MACD 상태 | 점수 |
|---|---|
| 직전 4주 이내 시그널 라인 상향 돌파 | 100 |
| 양수이고 우상향 (최근 4주간 증가) | 80 |
| 양수이고 보합 (변화율 ≤ ±5%) | 60 |
| 양수이고 우하향 | 40 |
| 음수이고 우상향 (turnaround 신호) | 50 |
| 음수이고 보합 | 30 |
| 음수이고 우하향 | 0 |

#### 5.4.5 카탈리스트 캘린더 (FR-ENRICH-CATALYST)

- 종목별 다음 실적 발표 예정일 조회 (KR: 38커뮤니케이션, US: yfinance calendar).
- 카탈리스트는 주 1회 갱신 (월요일 첫 실행 시).
- v1.0은 실적(`earnings`)만 추적. 배당락, 무상증자 등은 백로그.
- 실적 발표 7일 이내 (달력일) 예정 종목: 알림 메시지에 경고 표시.
- 실적 발표 직후 3거래일 이내 MACD 전환: §5.5.2 카탈리스트 보너스 적용 대상.

#### 5.4.6 시장 컨텍스트 (FR-ENRICH-MARKET)

- KOSPI, KOSDAQ, S&P500의 최근 30거래일 수익률 산출.
- KR 시장 알림은 KOSPI·KOSDAQ 둘 다, US 시장 알림은 S&P500 기준.
- 시장 지수가 −10% 이상 하락 중이면 `market_regime = "bear"`, +10% 이상 상승이면 `"bull"`, 그 사이는 `"neutral"`.
- `market_regime = "bear"` 시 §5.5.3 임계치 자동 상향.

### 5.5 점수 산정 (FR-SCORE)

#### 5.5.1 평탄화 가중합 공식

모든 부분 점수는 0~100 범위로 정규화된 후 다음 가중합으로 합산된다.

```
score_total =
    0.10 × score_drawdown          (§5.3.1)
  + 0.10 × score_macd_freshness    (§5.3.2)
  + 0.10 × score_volume_intensity  (§5.3.3)
  + 0.30 × score_news_sentiment    (§5.5.2)
  + 0.25 × score_fundamental       (§5.4.3)
  + 0.15 × score_mtf               (§5.4.4)

# 가중치 합 = 1.00, 따라서 score_total ∈ [0, 100]
```

가중치는 모두 `config.yaml: scoring.weights`로 조정 가능.

#### 5.5.2 뉴스 감성 점수 및 보정

```
score_news_sentiment = positive_ratio × 100
if news_count < min_count:
    score_news_sentiment ×= 0.5     # 관심도 낮음 페널티
if unknown_ratio > 0.5:
    score_news_sentiment ×= 0.5     # LLM 분류 실패 페널티 (§5.4.2)
```

**카탈리스트 보너스** (점수 합산 후 별도 보정):
- 실적 발표 직후 3거래일 이내 MACD 전환 종목: `score_total += catalyst_bonus` (기본 +5).
- 보너스 후 `score_total`은 100을 초과할 수 있다 (cap 없음).

#### 5.5.3 알림 임계치

```
threshold_effective = base_threshold + market_adjustment
                     (기본 60)        (bear 시 +10, 그 외 0)

if score_total ≥ threshold_effective:
    candidate for alert
```

#### 5.5.4 점수 산출 근거 표기

알림 메시지에 인자별 가중 기여 점수를 표기하여 사용자가 어떤 요인이 점수를 만들었는지 즉시 확인할 수 있게 한다 (§10.1 참조).

### 5.6 알림 중복 방지 (FR-COOLDOWN)

- 한 번 알림한 종목은 기본 14일 (달력일) 쿨다운.
- **재알림 조건**: 새 점수 ≥ 직전 동일 종목 알림의 점수 + 20. 직전 알림은 가장 최근 1건만 비교 대상.
- 알림 이력은 SQLite의 `alert_history`에 저장 (티커당 다중 행 허용).
- 모든 임계치는 `config.yaml: cooldown`으로 조정 가능.

### 5.7 텔레그램 알림 (FR-NOTIFY)

- 봇 토큰은 GitHub Secrets에 저장.
- 본인 chat_id 외 응답 차단.
- 후보 다수 시 점수 내림차순 정렬, 상위 N개 (`notification.max_alerts_per_run`, 기본 10) 발송.
- **메시지 길이 제한**: 텔레그램 단일 메시지는 최대 4096자. 종목 1건당 약 600자가 소요되므로 종목별로 메시지 1건씩 분할 발송. 발송 간격 1초 (rate limit 회피).
- 후보 없는 날도 헬스체크 메시지 1건 발송 (`notification.send_empty_summary`).
- 메시지 포맷은 §10 참조.

---

## 6. 비기능 요구사항

### 6.1 성능

- **NFR-PERF-01**: 단일 시장 1회 일상 실행이 60분 이내 완료 (GitHub Actions 무료 한도 고려).
- **NFR-PERF-02**: 게이트 단계는 캐시 데이터만으로 5분 이내 완료.
- **NFR-PERF-03**: 외부 API 호출은 안정성 우선. 속도보다 재시도와 폴백.
- **NFR-PERF-04**: 가격 데이터는 증분 수집으로 일일 API 호출량 최소화.
- **NFR-PERF-05**: 초기 백필은 일상 실행과 별도 워크플로우로 분할 진행 (§11.5).

### 6.2 안정성

- 개별 종목 또는 API 실패가 전체 파이프라인을 중단시키지 않을 것.
- 모든 외부 API 호출은 재시도 로직(최대 3회, 지수 백오프)을 가질 것.
- 파이프라인 실패 시 텔레그램으로 에러 알림.
- 부분 실행 결과도 가능한 범위에서 알림 발송.
- SQLite는 매 실행 종료 시 영속 저장소(§7.3)로 백업.

### 6.3 보안

- 모든 API 키, 토큰은 GitHub Secrets에 저장. 코드에 하드코딩 금지.
- 레포지토리는 private으로 운영.
- 로그에 토큰·키 노출 금지.
- 텔레그램 봇은 본인 chat_id 외 응답 차단.

### 6.4 비용

- 월 운영 비용은 LLM API 사용료를 제외하고 0원 목표.
- LLM 분류 비용은 월 5만원 이내 목표. **월 한도 초과 시 동작은 §11.7**.
- 유료 API 도입 시 PRD 개정 후 도입.

### 6.5 유지보수성

- 모든 임계치는 `config.yaml`로 외부화.
- 파이프라인의 각 단계는 독립 모듈로 분리. 단위 테스트 작성 가능 구조.
- README에 셋업·복구 가이드 작성.
- 의존 라이브러리 버전 고정 (`requirements.txt` 또는 `pyproject.toml`).
- 매 릴리스 태그(`v1.0.0`, `v1.1.0`, ...)로 버전 관리.

---

## 7. 데이터 모델

### 7.1 SQLite 스키마

```sql
-- 종목 마스터
CREATE TABLE tickers (
  ticker TEXT PRIMARY KEY,
  market TEXT NOT NULL,
  name TEXT NOT NULL,
  sector TEXT,
  market_cap REAL,
  is_excluded INTEGER DEFAULT 0,
  exclude_reason TEXT,
  updated_at TEXT
);

-- 일봉 시세 캐시 (수정주가 기준)
CREATE TABLE prices (
  ticker TEXT NOT NULL,
  date TEXT NOT NULL,                -- YYYY-MM-DD
  open REAL, high REAL, low REAL, close REAL,
  adj_close REAL NOT NULL,
  volume INTEGER,
  PRIMARY KEY (ticker, date)
);
CREATE INDEX idx_prices_ticker_date ON prices(ticker, date);

-- 분할·배당 이벤트
CREATE TABLE corporate_actions (
  ticker TEXT NOT NULL,
  ex_date TEXT NOT NULL,
  action_type TEXT NOT NULL,         -- 'split', 'dividend'
  factor REAL,                       -- split factor or dividend amount
  fetched_at TEXT,
  PRIMARY KEY (ticker, ex_date, action_type)
);

-- 게이트 통과 + 확장 + 점수 통합 기록
CREATE TABLE signals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ticker TEXT NOT NULL,
  signal_date TEXT NOT NULL,
  drawdown_pct REAL,
  macd_signal_type TEXT,
  macd_signal_age_days INTEGER,
  volume_ratio REAL,
  spike_flag INTEGER DEFAULT 0,
  news_count INTEGER,
  news_unknown_ratio REAL,
  sentiment_positive_ratio REAL,
  fundamental_status TEXT,           -- 'pass', 'excluded', 'unknown'
  fund_excluded_reasons TEXT,        -- JSON array
  mtf_status TEXT,
  upcoming_earnings_date TEXT,
  market_regime TEXT,
  score_drawdown REAL,
  score_macd_freshness REAL,
  score_volume_intensity REAL,
  score_news_sentiment REAL,
  score_fundamental REAL,
  score_mtf REAL,
  catalyst_bonus REAL DEFAULT 0,
  total_score REAL,
  details_json TEXT,
  created_at TEXT
);

-- 알림 이력 (쿨다운 관리)
CREATE TABLE alert_history (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ticker TEXT NOT NULL,
  alert_date TEXT NOT NULL,
  total_score REAL,
  signal_id INTEGER,
  created_at TEXT,
  FOREIGN KEY (signal_id) REFERENCES signals(id)
);
CREATE INDEX idx_alert_ticker_date ON alert_history(ticker, alert_date);

-- 뉴스 캐시 + 분류 결과
CREATE TABLE news (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ticker TEXT NOT NULL,
  published_at TEXT,
  title TEXT,
  url TEXT UNIQUE,
  source TEXT,
  classification TEXT,               -- 'positive', 'neutral', 'negative', 'unknown'
  topic TEXT,
  prompt_version INTEGER,
  classified_at TEXT,
  is_duplicate_of INTEGER REFERENCES news(id)
);

-- 재무 지표 캐시
CREATE TABLE fundamentals (
  ticker TEXT NOT NULL,
  period TEXT NOT NULL,              -- YYYY-Qn
  revenue REAL, op_income REAL, net_income REAL,
  total_debt REAL, total_equity REAL,
  fetched_at TEXT,
  PRIMARY KEY (ticker, period)
);

-- 카탈리스트 (실적 발표 일정)
CREATE TABLE catalysts (
  ticker TEXT NOT NULL,
  event_type TEXT NOT NULL,
  scheduled_date TEXT NOT NULL,
  fetched_at TEXT,
  PRIMARY KEY (ticker, event_type, scheduled_date)
);

-- 운영 메타 (LLM 토큰 사용량 등)
CREATE TABLE ops_meta (
  key TEXT PRIMARY KEY,
  value TEXT,
  updated_at TEXT
);
```

모든 시각 컬럼은 ISO 8601 UTC (`YYYY-MM-DD HH:MM:SS+00:00`).

### 7.2 캐싱 전략

시세는 종목당 마지막 저장일 이후만 API에서 조회한다. 분할·배당 검출 시 해당 종목 5년치를 재수집한다. 재무 데이터는 분기 1회 갱신. 뉴스는 종목·URL 단위 unique. 동일 URL의 LLM 분류 결과는 영구 저장. 카탈리스트는 주 1회 갱신.

### 7.3 SQLite 영속화 전략

GitHub Actions runner는 매 실행마다 디스크가 초기화되므로 SQLite 파일을 외부에 영속화해야 한다.

**1차 영속화: GitHub Actions Cache**
- `actions/cache@v4` 사용. 키는 `screener-db-${market}-${date}`.
- 워크플로우 시작 시 복원, 종료 시 저장.
- 7일 미사용 시 자동 만료. 일일 실행으로 만료 회피.

**2차 백업: 별도 git 브랜치**
- 매주 일요일(KR 시장 기준 마지막 실행 후) `data` 브랜치에 SQLite 파일 commit (force push로 history 단축).
- 1차 캐시 손실·만료 시 이 브랜치에서 복원.
- 파일이 100MB 초과로 커지면 월 1회 squash로 history 정리.

**3차 백업: 월 1회 GitHub Releases**
- 매월 1일 첫 실행 시 SQLite를 압축하여 Release asset으로 업로드.
- 중대한 데이터 손상 시 수동 복구용.

복원 우선순위: Cache → data 브랜치 → Releases 최신본 → (모두 실패 시) 초기 백필 트리거.

### 7.4 분할·배당 처리

- 매 실행 시 직전 7거래일의 corporate actions를 조회한다.
- split 또는 의미 있는 dividend (1% 이상) 발생 종목은 5년치 가격을 yfinance/pykrx에서 다시 받아 `prices.adj_close`를 갱신한다.
- 갱신 후 해당 종목의 MACD·이동평균 재계산.
- 재계산 결과 게이트 통과 여부가 변경될 수 있으나, **이전 알림 이력은 변경하지 않는다** (실시간 의사결정 시점의 정보를 보존).

---

## 8. 외부 의존성

### 8.1 데이터 소스

| 용도 | KR | US | 비용 |
|---|---|---|---|
| 시세·거래량·수정주가 | pykrx, FinanceDataReader | yfinance | 무료 |
| 종목 마스터·시총·섹터 | KRX (pykrx), DART | yfinance, NASDAQ Trader | 무료 |
| 분할·배당 | pykrx, FinanceDataReader | yfinance | 무료 |
| 재무 데이터 | DART OpenAPI | yfinance, SEC EDGAR | 무료 |
| 뉴스 | 네이버 검색 API, 빅카인즈 | NewsAPI, GDELT | 무료 또는 저비용 |
| 실적 일정 | 38커뮤니케이션 (스크레이핑) | yfinance calendar | 무료 |
| 시장 지수 | pykrx (KS11, KQ11) | yfinance (^GSPC) | 무료 |

### 8.2 텔레그램 봇

BotFather에서 봇 생성 → 토큰 발급 → GitHub Secrets에 `TELEGRAM_BOT_TOKEN` 저장. 사용자 chat_id는 별도 Secret `TELEGRAM_CHAT_ID`로 저장. 메시지는 `https://api.telegram.org/bot<TOKEN>/sendMessage` 호출로 발송.

### 8.3 LLM API

Anthropic API (Claude). API 키는 `ANTHROPIC_API_KEY` Secret. 분류용 모델은 Claude Haiku 4.5 (`enrich.llm.model`). 정확도 이슈 시 Claude Sonnet 4.6으로 상향. Prompt는 `prompts/news_classifier_v{N}.txt`로 버전 관리.

---

## 9. 설정 및 파라미터

### 9.1 환경 변수 (GitHub Secrets)

| 키 | 용도 |
|---|---|
| `TELEGRAM_BOT_TOKEN` | 텔레그램 봇 토큰 |
| `TELEGRAM_CHAT_ID` | 알림 수신 chat_id |
| `ANTHROPIC_API_KEY` | LLM 분류용 |
| `NAVER_CLIENT_ID` / `NAVER_CLIENT_SECRET` | 네이버 검색 API |
| `NEWS_API_KEY` | NewsAPI |
| `DART_API_KEY` | DART OpenAPI |
| `DATA_BRANCH_DEPLOY_KEY` | data 브랜치 push용 deploy key |

### 9.2 사용자 조정 파라미터 (`config.yaml`)

```yaml
universe:
  kr:
    markets: [KOSPI, KOSDAQ]
    min_market_cap_krw: 100_000_000_000
    min_avg_volume_krw: 500_000_000
  us:
    markets: [NYSE, NASDAQ]
    min_market_cap_usd: 500_000_000
    min_avg_volume_usd: 1_000_000

gates:
  price:
    min_drawdown_pct: 50              # 최고점 대비 −50% 이상
    lookback_years: 5
  macd:
    fast: 12
    slow: 26
    signal: 9
    window_days: 3                    # 거래일 기준
    track_zero_cross: true
    track_signal_cross: true
  volume:
    multiplier: 1.5
    ma_window: 20                     # 거래일
    spike_flag_threshold: 10.0

enrich:
  news:
    lookback_days: 7                  # 달력일
    min_count: 3
    duplicate_similarity_threshold: 0.85
  llm:
    model: claude-haiku-4-5
    auto_exclude_topics: [accounting_issue, legal_issue]
    auto_exclude_threshold: 0.5
    monthly_token_budget_usd: 35      # USD 환산 월 예산
  fundamental:
    enable: true
    max_consecutive_losses: 4
    max_debt_to_equity: 3.0
    min_revenue_growth_yoy: -0.30
    min_violations_for_exclude: 2

scoring:
  weights:                            # 합 = 1.00
    drawdown: 0.10
    macd_freshness: 0.10
    volume_intensity: 0.10
    news_sentiment: 0.30
    fundamental: 0.25
    multi_timeframe: 0.15
  alert_threshold: 60
  market_weakness_adjustment: 10
  catalyst_bonus: 5

cooldown:
  base_days: 14                       # 달력일
  reset_score_increase: 20

notification:
  max_alerts_per_run: 10
  send_empty_summary: true
  message_send_interval_sec: 1.0

ops:
  weekly_data_branch_backup: true
  monthly_release_backup: true
  llm_overrun_action: "notify_only"   # notify_only | disable_llm | halt

exclude_tickers: []
```

---

## 10. 출력 사양

### 10.1 텔레그램 메시지 포맷 (종목별)

```
🎯 [KR] 삼성전자 (005930)
점수: 72/100  ↑ 신규 알림  [bear 국면 임계치 70]
  └ 가중 기여: 게이트(22) + 뉴스(24) + 재무(18) + 주봉(8) + 카탈(0)

📉 가격
  현재가: 58,400원 (수정주가)
  5년 최고가 대비: -55.2% (2021-01-11 96,800원)

⚡ MACD
  신호: 0선 돌파 (2026-05-04, 1거래일 전)
  거래량 배수: 1.8x

📰 뉴스 (최근 7일, 12건 / 중복 제거 후 9건)
  호재 6 / 중립 2 / 악재 1 / 분류실패 0
  주요 토픽: 신규 수주, 실적 개선
  주요 기사: "삼성전자, 차세대 D램 양산 본격화"
  https://news.example.com/article/12345

📊 펀더멘털
  매출 YoY: +8.2% (점수 64)
  영업이익률: 11.3% (점수 76)
  부채비율: 28% (점수 100)
  ✅ 자동 제외 조건 미해당

📈 주봉 MACD
  상태: 양수 우상향 (점수 80)

⚠️ 카탈리스트
  실적 발표 예정: 2026-05-15 (10일 후)

🌐 시장 컨텍스트: KOSPI -2.3% (neutral)

🔗 차트: https://finance.naver.com/item/main.naver?code=005930
```

비정상 거래량 스파이크나 LLM 자동 제외 사유 발생 시 메시지 상단에 추가 표기:
- `⚠️ 거래량 ×12.4 — 작전 의심 검토 필요`
- `❌ 자동 제외 사유: 회계이슈 비중 0.62`

### 10.2 일일 요약 메시지

후보 없는 날에도 발송:
```
📭 2026-05-05 KR 시장 알림
오늘 조건을 만족하는 종목이 없습니다.

스캔: 1,432종목 (수집 실패 8)
└ Gate 1 통과: 87
  └ Gate 2 통과: 14
    └ Gate 3 통과: 5
      └ 자동 제외: 1 (회계이슈)
        └ 점수 임계치 통과: 0 (최고 56점)

시장 컨텍스트: KOSPI -2.3% (neutral)
LLM 호출: 0회 / 누적 월간: 247회 / 예산 ≈ 18% 사용
실행 시간: 12분 34초
```

---

## 11. 운영 및 배포

### 11.1 GitHub Actions 워크플로우

- `kr_screener.yml`: cron `30 7 * * 1-5` UTC = 16:30 KST Mon-Fri
- `us_screener.yml`: cron `30 21 * * 1-5` UTC = 다음날 06:30 KST (EST) / 30분 일찍 (EDT는 자연스레 더 많은 버퍼 확보)
- 휴장일 보호: 워크플로우 시작 시 해당 시장 휴장일 체크 → 휴장이면 조기 종료.
- 수동 실행: `workflow_dispatch` 트리거.
- 양 시장 비대칭 휴장 (US Thanksgiving, KR 추석 등): 시장별 독립 캘린더로 자동 처리.

### 11.2 Secrets 관리

토큰·키는 모두 GitHub Secrets에 등록. 분기 1회 토큰 회전. 노출 사고 시 즉시 회전 + 봇 재발급.

### 11.3 로깅 및 모니터링

실행 로그는 GitHub Actions 기본 로그로 보존 (90일). 주요 메트릭(처리 종목 수, 게이트별 통과 수, 확장 단계 호출 수, API 실패 수, LLM 토큰 사용량)을 일일 헬스체크 메시지에 포함. LLM API 비용은 월 1회 텔레그램으로 요약 보고.

### 11.4 장애 대응

외부 API 다운 시 다음 실행으로 자동 재시도. 7일 연속 실행 실패 시 별도 강한 경고. SQLite 손상 시 §7.3 영속화 우선순위에 따라 복구. 복구 불가 시 백필 워크플로우 수동 트리거.

### 11.5 초기 백필 (One-Time Bootstrap)

5년치 일봉 + 분할·배당 + 4분기 재무를 처음 받는 작업은 60분 한도 안에 끝나지 않을 수 있다.

**전용 워크플로우** `backfill.yml`:
- `workflow_dispatch` 수동 트리거.
- 종목을 200개씩 chunk로 나누어 순차 실행 (matrix strategy).
- chunk별 별도 잡으로 병렬 처리. 각 잡 50분 내 완료 목표.
- 모든 chunk 완료 후 SQLite를 §7.3에 따라 영속화.
- 완료 시 텔레그램으로 백필 완료 알림.

KR ~1,500종목 → 8개 chunk, US ~2,500종목 → 13개 chunk.

### 11.6 동시 실행 보호

- GitHub Actions의 `concurrency` 그룹으로 같은 워크플로우의 중첩 실행 방지:
  ```yaml
  concurrency:
    group: screener-${{ github.workflow }}
    cancel-in-progress: false
  ```
- 추가로 코드 레벨 잠금: SQLite 파일 옆 `.lock` 파일을 `filelock`으로 획득. 60초 내 미획득 시 실행 중단.
- KR과 US는 다른 SQLite 파일을 사용하므로 동시 실행 가능.

### 11.7 LLM 비용 한도 초과 대응

매 실행 시작 시 `ops_meta`의 월간 누적 토큰 사용량을 조회하여 `enrich.llm.monthly_token_budget_usd`와 비교한다.

`ops.llm_overrun_action` 설정에 따라:
- `notify_only`: 임계치 도달 시 텔레그램 경고만 발송, 분류는 계속 진행 (기본값).
- `disable_llm`: 분류를 건너뛰고 모든 종목의 `score_news_sentiment = 50` (중립값) 적용.
- `halt`: 워크플로우 즉시 중단, 강한 경고 발송.

월 1일 첫 실행 시 누적 카운터 리셋.

---

## 12. 구현 의존성 순서

본 PRD의 모든 기능은 v1.0 출시까지 통합 구현된다. 코드 작성에는 다음 기술적 의존성 순서를 따른다 (기능 우선순위가 아닌 빌드 순서).

1. **인프라 계층**: SQLite 스키마, `config.yaml` 로더, 로깅, 재시도 데코레이터, filelock 래퍼
2. **영속화 계층**: 캐시 복원/저장 로직, data 브랜치 동기화, Release 백업
3. **데이터 계층**: 유니버스 관리, 시세 수집기 (수정주가 + 분할·배당 검출), 휴장일 처리
4. **계산 계층**: MACD, 거래량 평균, 하락폭 등 지표 계산 함수
5. **게이트 계층**: 3개 게이트 필터 + 게이트 잔존 점수 계산
6. **확장 계층**: 뉴스 수집·중복 제거, LLM 분류 (프롬프트 버전 관리, 폴백), 재무 데이터, 주봉 MACD, 카탈리스트, 시장 컨텍스트
7. **판정 계층**: 점수 산정 (모든 공식), 카탈리스트 보너스, 시장 보정, 쿨다운
8. **출력 계층**: 텔레그램 포매터 (다중 메시지 분할), 봇 송신, 헬스체크 메시지
9. **자동화 계층**: GitHub Actions 워크플로우 (일상 + backfill), Secrets 연동, concurrency
10. **검증 계층**: 백테스트 인프라

---

## 13. 백테스트 계획

### 13.1 목적

게이트 임계치(특히 하락폭 −50%, MACD 윈도우 3일, 거래량 ×1.5)를 자의적이지 않게 정한다. 점수 가중치도 백테스트로 검증한다.

### 13.2 방법

- 과거 5년(2021-01-01 ~ 2026-05-05) 일봉 데이터에서 매일 룰셋을 적용한다.
- **look-ahead bias 방지**: 특정 날짜 D의 신호 판정 시 D 이후 정보를 사용하지 않는다. 재무는 D 시점 공시된 가장 최근 분기, 뉴스는 D 이전 7일치, 카탈리스트는 D 시점 알려진 일정만 사용.
- 게이트 통과 종목 + 점수 임계치 통과 종목별로 30거래일·90거래일·180거래일 후 종가 수익률 기록.
- 동일 기간 시장 지수 수익률과 비교.
- 임계치 조합 그리드 서치 (예: 하락폭 30/40/50/60%, MACD 윈도우 1/3/5/7, 거래량 1.0/1.5/2.0/3.0배).

### 13.3 평가 지표

- 승률 (양의 수익률 종목 비율)
- 평균 수익률 + 표준편차
- 시장 대비 알파
- 최대 손실 (Maximum Drawdown)
- 알림 빈도 (월 평균 알림 종목 수, 목표 시장당 일 10~30 게이트 통과)

### 13.4 산출물

- `backtest_report.html`: 임계치별 성과표, 수익률 분포 차트.
- 룰셋 조정 권장사항 문서.

---

## 14. 리스크 및 가정

### 14.1 리스크

| ID | 리스크 | 영향 | 완화 방안 |
|---|---|---|---|
| R-01 | yfinance 등 무료 API 정지 | 데이터 수집 불가 | 다중 소스 폴백 (Tiingo 등) |
| R-02 | LLM 비용 폭증 | 비용 부담 | 토큰 모니터링 + §11.7 한도 초과 대응 |
| R-03 | GitHub Actions 무료 분 초과 | 자동화 정지 | 실행 시간 모니터링, 필요 시 self-hosted runner |
| R-04 | 잘못된 신호로 손실 행동 유도 | 투자 손실 | 알림에 "추천 아님" 명시, 사용자 직접 판단 강조 |
| R-05 | 가짜 신호(value trap) 다수 | 노이즈 | 펀더멘털·LLM 자동 제외로 1차 차단 |
| R-06 | API 키 노출 | 보안 | Secrets 관리, 정기 회전 |
| R-07 | 시장 구조 변화로 룰셋 무효화 | 전략 실패 | 분기별 백테스트 재실행 |
| R-08 | 섹터별 거래량 분포 차이 | 게이트 편향 | v2 백로그: 섹터 상대 거래량 |
| R-09 | 게이트 임계치 too tight → 후보 0 | 시스템 무용 | 백테스트 기반 캘리브레이션, 시장당 일 10~30 통과 목표 |
| R-10 | 동시 실행으로 SQLite 손상 | 데이터 손실 | §11.6 concurrency + filelock |
| R-11 | 분할·배당 미반영으로 잘못된 MACD | 잘못된 신호 | §7.4 분할·배당 검출 시 5년치 재수집 |
| R-12 | 초기 백필이 60분 한도 초과 | 부트스트랩 실패 | §11.5 chunk matrix 분할 실행 |
| R-13 | DST 전환기 cron 타이밍 어긋남 | 알림 지연 | 30~90분 버퍼 확보, EDT/EST 모두에서 정상 작동 검증 |
| R-14 | 동일 와이어 기사 다른 URL로 인한 노이즈 | 점수 왜곡 | §5.4.1 제목 유사도 0.85 기준 중복 제거 |
| R-15 | 프롬프트 변경 시 과거 분류와 불일치 | 백테스트 일관성 깨짐 | 프롬프트 버전 관리, 변경 시 일괄 재분류 |

### 14.2 가정

사용자는 본 시스템의 알림을 매수 신호로 받아들이지 않고 추가 분석의 시작점으로 활용한다. GitHub Actions, Telegram, 사용된 무료 API들이 운영 기간 동안 정상 작동한다. 5년이 추세 분석에 충분한 기간이다. 일봉 종가 기준 데이터로 충분하며 분 단위 데이터는 불필요하다. KR과 US 시장은 운영상 독립적이며 한쪽의 장애가 다른 쪽 운영을 방해하지 않는다.

---

## 15. 변경 이력

| 버전 | 일자 | 작성자 | 변경 내용 |
|---|---|---|---|
| v0.1 | 2026-05-05 | Yoo Byung-gwan | 초안. P0/P1/P2 단계별 로드맵 포함. |
| v0.2 | 2026-05-05 | Yoo Byung-gwan | P0/P1/P2 제거. funnel 구조 도입. 거래량을 게이트로 격상. 점수 가중치 재조정. Phase 로드맵을 구현 의존성 순서로 대체. |
| v1.0 | 2026-05-05 | Yoo Byung-gwan | v0.2 검증 결과 반영. **정밀 정의** §4.5 신설(거래일/달력일, 시점 포함 여부, 신호일 결정 규칙, 부등호 규약). **수식 명시** §5.3.1~5.3.3, 5.4.3, 5.4.4, 5.5.1 모든 점수 공식을 앵커 포인트와 선형 보간으로 정의. **운영·인프라 보완** §7.3 SQLite 영속화 3계층 전략, §7.4 분할·배당 처리, §11.5 초기 백필 chunk 분할, §11.6 동시 실행 보호, §11.7 LLM 비용 한도 초과 대응. **엣지 케이스** R-10~R-15 추가 및 본문 처리 규칙. **일관성 정정** KR 장 마감 시간(15:30), 카탈리스트 보너스를 후보정으로 명시, 알림 메시지 포맷에 LLM 자동 제외/시장 컨텍스트/분류 실패 표기 추가. **데이터 무결성** 뉴스 유사도 중복 제거, LLM 분류 실패 폴백, 프롬프트 버전 관리, 수정주가 사용 명문화. |

---

## 부록

### A. 용어 정의

- **MACD (Moving Average Convergence Divergence)**: 단기·장기 EMA 차이로 추세 전환을 포착하는 지표. DIF = EMA12 − EMA26. Signal = EMA(DIF, 9).
- **0선 돌파 (Zero-Line Cross)**: MACD 값이 음수에서 양수로 전환되는 시점.
- **시그널 라인 돌파 (Signal-Line Cross)**: MACD 라인이 시그널 라인을 상향 돌파.
- **Drawdown**: 최고점 대비 현재가의 하락률. 본 문서에서는 5년 일봉 수정종가 기준.
- **Gate (게이트)**: 캐시 데이터로 즉시 판정 가능한 hard 필터. 통과 못 하면 확장 단계 진입 X.
- **Enrichment (확장)**: 게이트 통과 종목에 대해 외부 API로 추가 정보를 수집·계산하는 단계.
- **Cost-Tier Separation (비용 계층 분리)**: 싼 연산을 앞에, 비싼 연산을 뒤에 배치하는 파이프라인 설계 원칙.
- **Dual Role (이중 역할)**: 동일 인자가 게이트(binary)와 점수(continuous) 양쪽에 기여하는 설계.
- **Value Trap (가치 함정)**: 주가가 많이 빠져 저평가로 보이지만 비즈니스 훼손이 진행 중인 종목.
- **Catalyst (카탈리스트)**: 주가 변동을 유발할 수 있는 예정된 이벤트.
- **Look-ahead Bias**: 백테스트에서 해당 시점에 알 수 없었던 미래 정보를 사용하여 결과가 왜곡되는 오류.
- **Adjusted Close (수정종가)**: 분할·배당으로 보정된 종가. 추세·지표 계산 시 사용.

### B. 참고 자료

- pykrx: https://github.com/sharebook-kr/pykrx
- FinanceDataReader: https://github.com/financedata-org/FinanceDataReader
- yfinance: https://github.com/ranaroussi/yfinance
- pandas-ta: https://github.com/twopirllc/pandas-ta
- DART OpenAPI: https://opendart.fss.or.kr
- 네이버 검색 API: https://developers.naver.com
- Telegram Bot API: https://core.telegram.org/bots/api
- GitHub Actions cron: https://docs.github.com/actions/using-workflows/events-that-trigger-workflows#schedule
- GitHub Actions Cache: https://docs.github.com/actions/using-workflows/caching-dependencies-to-speed-up-workflows

---

*본 문서는 본인의 개인 사용 목적의 시스템 설계를 위한 것이며, 투자 추천이나 자문이 아닙니다. 시스템이 생성하는 신호는 사용자 본인의 추가 분석과 의사결정의 보조 자료로만 활용됩니다.*
