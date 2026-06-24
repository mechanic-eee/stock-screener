# 폭락주 스크리너 — 전체 주식투자 서비스 최적화 설계 (2026-06-23)

> 코드 정밀 감사(4) + 웹 리서치(팩터투자·전문 스크리너·KR 데이터·폭락주 특화) + 적대적 검증을 멀티에이전트로 종합한 end-to-end 설계.
> **원칙:** 추가는 *왜 추가하는지(목적·효용·시너지)*를 설명한 뒤 더한다. 삭제는 *왜 삭제 후보인지*를 설명하되 **바로 지우지 않고 사용자 확인을 받는다**(§2는 전부 "확인 요청" 후보).
> 진행: §7에 **오늘 이미 적용한 변경**(ATR 지표 추가 + 정합성 수정 2건).

---

## 0. 한눈에 — 핵심 진단 3가지

1. **데이터 백본은 살아있다 (★오진단 정정).** "스냅샷이 5/24에 멈췄다"는 로컬 클론의 `origin/data` ref가 stale했던 것일 뿐, 원격 data 브랜치는 신선했다(HEAD = `snapshot 2026-06-23T00:25:58Z`, daily-scan이 6/11~6/22 전 평일 success). 원인은 orphan force-push라 로컬이 자동 갱신되지 않는 것 — **진단은 항상 `gh run list` / `git fetch origin data`로.** 단, 진짜로 죽어도 알 신호(헬스체크·신선도 경고)가 없는 건 실제 결함.
2. **전반부(발굴·점수·워치리스트)는 거의 완성, 후반부(결정저널·사이징·리뷰)는 미착수.** "발굴 보조도구"는 완성에 가깝지만 "투자 서비스"로 보면 절반이다.
3. **점수 모델의 빈 차원 = 이익의 질·부도위험·퀄리티.** 14종은 전부 가격기술 or 재무 '수준값'이라 "이익이 현금인가 / 회복 체력이 있나 / 구조적으로 돈 버나"를 안 본다. 그리고 가장 신뢰 낮은 news에 최고 가중(0.30)이 걸려 있다.

---

## 1. 추가 권고 (Add) — 임팩트순 정예 9종

> 모두 **무료/저비용 + 기존 14종과 직교 + 실증 근거**를 충족. 우리 플러그인 패턴(`filters/<x>.py` + `@register` + scoring 곡선 + fail-soft 중립50)에 그대로 얹힘. 클라우드는 기존 사이드카 prime 패턴 재사용으로 라이브 fetch 0.

| 우선 | 지표 | 차원(왜 직교) | 데이터 | 노력 |
|---|---|---|---|---|
| **P0** | **kr_market_action** | 거래소 **확정 조치**(관리/정지) — 단일 최고 ROI | KIND/KRX | 중 |
| **P0** | **altman_z (Z'')** | **부도위험** 게이트 — distress puzzle 백본 | 기존 재무+시총 | 중 |
| **P0** | **piotroski_fscore** | 재무 **추세**(개선 중인가) — 14종 전부 수준값 | yfinance/DART + CFO | 중 |
| **P0** | **net_share_issuance** | **희석/자사주** — 한계비용 0(캐시 shares) | 캐시된 shares | 하 |
| **P1** | **accruals_quality** | **이익의 질**(현금 vs 발생액) | NI·CFO·자산(공유) | 하 |
| **P1** | **gross_profitability** | **퀄리티**(GP/자산, 깨끗) | 매출원가 1줄 | 하 |
| **P1** | **dart_risk_event** | KR **감사의견/위험공시** | 기존 DART 인프라 | 중 |
| **P1** | **atr_risk** ✅ | **리스크/사이징 메타** | 일봉 OHLC | 하 (→§7 완료) |
| **P2** | **kr_short_and_flow** | KR **주체별 수급/공매도** | pykrx | 중 |

### P0 — 즉시

**① kr_market_action — KR 관리종목/거래정지 게이트 (단일 최고 ROI 제외)**
- **목적:** KIND/KRX 관리종목·투자경고/위험·거래정지 명단으로 KR 종목 자동제외.
- **효용:** 감사가 짚은 **가장 큰 공백** — 현 `universe.py`는 시총·증권유형만 보고 시장조치를 전혀 안 봐 '5년 −70% + 관리종목'(전형적 상폐직전)이 무방비로 1차 후보 진입. 거래소 **확정** 조치라 추정과 독립된 강신호.
- **시너지:** fundamental(추정)·altman_z(추정)가 못 잡는 행정조치를 차단. 기존 `is_excluded` 인프라에 그대로 얹힘.
- **구현:** `data/market_actions.py`(일일 명단 fetch, `news/cache.py` 일일캐시 패턴)→`list_kr()`에서 `is_excluded=1`·`exclude_reason='admin_issue'`. US는 no-op. fail-soft(명단 fetch 실패 시 경고만).

**② altman_z (Z'') — 부도위험 게이트**
- **목적:** 비제조·신흥시장 Z''(=3.25+6.56·WC/TA+3.26·RE/TA+6.72·EBIT/TA+1.05·BVE/TL)로 distress-zone 자동제외 + 거리 스코어러.
- **효용:** falling-knife의 **학술적 백본** = distress risk puzzle(Campbell-Hilscher-Szilagyi 2008): 부도위험 높은 종목은 위험 대비 *비정상적으로 낮은* 수익. 우리 유니버스는 이미 고폭락=고부도위험이라 '추가 배제'가 수익의 핵심. 현 fundamental의 임의 4-flag를 **교정된 연속 점수**로 승격.
- **시너지:** drawdown 종곡선의 '>95% 낙폭=상폐위험 0점'(가격)을 재무로 뒷받침. *Ohlson O·Merton DtD는 같은 차원이라 중복 — Z만 1차 채택.*
- **구현:** Bundle에 total_assets·retained_earnings 추가, z'' 계산(시총=price×shares). `scoring.altman_z_score`: Z≤1.1→0, ≥2.6→100. `filters/altman_z.py`. **★검증 단서(§6): 적자·결손누적 기업에서 EBIT/RE가 음수라 게이트가 가격 휴리스틱과 이중 가중될 위험 → 출시는 게이트 OFF(스코어러만), 백테스트 후 게이트화.**

**③ piotroski_fscore — 폭락 저PBR 중 "돌아설 놈" 선별**
- **목적:** 9점 회계건전성(수익성4+레버리지/유동성3+효율2)으로 재무가 *실제 개선 중인가*를 점수화.
- **효용:** Piotroski 원논문이 **low-P/B 분리용**으로 설계 — 우리 thesis(폭락=1차→회복형=2차)와 동형. 고F 가치주 연 +7.5%p, 효과가 소형·저커버리지·재무곤경에 집중(=우리 유니버스). 추세 4항목(ΔROA·CFO>NI·Δ레버리지·Δ마진)은 14종 어디에도 없다.
- **시너지:** fundamental(배제)·valuation(저평가)와 직교. macd/weekly_macd(가격 추세전환)와 같은 방향이면 진짜 턴어라운드. CFO·총자산을 한 번 fetch하면 ⑤⑥과 입력 공유.
- **구현:** `FundamentalsBundle` 확장 → `f_score`(int) → 사이드카 컬럼. `scoring.piotroski_score(f)=f/9*100`. `filters/piotroski.py`(weight 0.20, `min_fscore` 기본3, 0이면 점수만).

**④ net_share_issuance — 희석/자사주 (가성비 최고)**
- **목적:** 발행주식수 YoY 변화로 '경영진이 싼 자기주식을 사나(호재) vs 살려고 증자하나(희석=악재)'.
- **효용:** **이미 캐시될 shares만으로 한계비용 0**인데 Pontiff-Woodgate(2008 JF): 발행주식수 변화가 size·B/M·모멘텀 각각보다 유의하게 수익 예측. 14종에 '주식수 변화' 전무.
- **시너지:** fundamental의 capital_impairment(자본잠식)와 보완(희석=잠식 직전). drawdown과 직교.
- **구현:** Bundle.share_change_yoy. `scoring.share_issuance_score`: +20%↑→0, 0→60, −10%↓→100. weight 0.10 스코어러. **★선결: KR shares 수집**(현재 `_fetch_kr` 미수집).

### P1 — 단기

**⑤ accruals_quality / ⑥ gross_profitability** — *이익의 질*과 *퀄리티* 차원. ②③과 입력(NI·CFO·총자산·매출원가)을 공유해 **한 fetch 확장에 묶어 동시 구현**. accruals=(NI−CFO)/자산: 흑자전환이 현금인가 회계착시인가(Sloan 1996, 소형·KR에 잔존). GP/자산: 가장 깨끗한 수익성(Novy-Marx 2013, B/M급 예측·value와 직교) — 가치함정(끝없이 싼 죽은 사업) 회피.

**⑦ dart_risk_event** — 감사의견 비적정(상폐 직행 사유)·주요사항보고서 위험이벤트(부도/영업정지/회생/채권은행관리). **기존 DART 인프라(키·corp_map·캐시) 재사용**이라 한계비용 거의 0. fundamental violations에 '감사의견' 추가, 치명 신호는 단독 제외.

**⑧ atr_risk** ✅ (오늘 구현, §7) — ATR%·권장손절폭(2.5×ATR)을 메타데이터로. 폭락주는 ATR이 비정상적으로 커 동일비중 매수 시 리스크 폭증. **to_watchlist 자동초안의 손절선 TBD를 자동으로 채워** 발굴→결정저널 마찰을 줄이는 후속(P1)이 남음.

### P2 — 중기

**⑨ kr_short_and_flow** — pykrx 단일 의존으로 공매도 잔고(급감=숏커버 반등)·외국인/기관 순매수(스마트머니 매집)를 KR에 점수화. KR은 주체별 수급이 익명 OBV보다 강함. **pykrx 하나로 공매도·수급·PER/PBR/시총 모두 커버.** 사이드카 prime으로 클라우드 라이브 fetch 0.

---

## 2. 삭제·강등 후보 (Remove) — ★바로 지우지 않음, 확인 요청

> 아래는 **사용자에게 확인받을 후보**다. 동의(또는 백테스트) 전엔 코드를 건드리지 않는다. 검증 결과 rsi/bollinger/moving_average는 **opt-in + 런타임 정규화**라 둘 다 켜지 않으면 이중계상이 안 생긴다 → 제거보다 **P2로 미루고 백테스트 후 결정**이 안전.

| 대상 | 왜 삭제(강등) 후보인가 | 위험 | confidence |
|---|---|---|---|
| **news weight 0.30 → 0.05~0.10 강등 + fail 동작 통일** | 감성원이 ~20단어 substring placeholder인데 enrichment 최고 가중. 켜면 노이즈가 합성점수 지배. news만 데이터없음→passed=False라 키 없는 US 켜면 미국 전체 탈락 | 낮음~중간(가중·fail 동시 처리 필수) | **high** |
| **bollinger 또는 rsi 중 하나** | %B≤0.2와 RSI≤35 강상관(같은 과매도 이중 가중). 폭락주는 둘 다 항상 켜져 변별력↓ | 중간 → **백테스트 후 결정(P2)** | medium |
| **moving_average (재정의 권장)** | macd_cross와 같은 단기 추세전환 차원(상관). 제거보다 **'200일선 회복'으로 재정의** 시 직교성↑ | 중간 → **검증 후(P2)** | medium |
| **catalyst 점수 보너스(+5)** | 발동조건이 너무 좁아 대부분 0. is_bonus라 가중 오염 없음 → 제거 ROI ~0, ⚠️임박경고는 유지 | 낮음 | medium |
| **WATCHLIST 미큐레이션 자동초안 행** | 11행 전부 동일 템플릿·TBD·한 달 방치 = 신호 0. 목적은 삭제가 아니라 **큐레이션 강제**(ATR 자동손절·점수분해) | 낮음(사용자 자산, 확인 필수) | low |

---

## 3. 개선 권고 (Improve)

**정합성·백본 (P0)**
- **drawdown 임계 통일:** `drawdown.py` default **−80 → −50**. ✅ 오늘 적용(§7).
- **actions/cache 키 고정:** `screener-db-${{run_id}}` → **`screener-db-v1`**. ✅ 오늘 적용(§7, commit+push 필요).
- **헬스/신선도 dead-man-switch:** daily_scan 끝에 `data/health.json`(last_run_utc·base_survivors·snapshot_tickers·last_price_date·available 비율) 발행 → app이 last_date가 오늘−3일보다 오래면 **경고 배너**, Actions fail 시 **텔레그램 핑**. '진단은 `gh run list`/`git fetch`로'를 운영노트에 명문화.

**점수 모델 (P1)**
- **news fail 통일:** bundle None → passed=True·중립50·available=False. 가중 강등과 **반드시 함께**.
- **fundamental 치명/약신호 분리:** 자본잠식·4Q적자·감사의견 비적정 = **단독 제외**, 매출급감·고부채 = 누적(min_violations).
- **KR shares 수집 + 4Q적자 작동:** `_fetch_kr`이 발행주식수 라인 + 최근 4분기 수집 → KR valuation이 price×shares, four_quarters_all_loss가 KR에서도 작동(share_issuance 선결).
- **가중치 데이터기반 재산정 + 백분위 정규화:** 회복 라벨로 지표별 IC/IR 측정해 직관 가중 교정. `apply_filters`에 **배치 내 백분위 정규화** 토글 + Quality/Value/Momentum 3축 그룹화(추가 데이터 0).

**운영·신뢰 위생**
- **의존성 핀:** yfinance·FDR ==핀/lockfile(차단 우회가 balance-sheet 스키마에 민감).
- **점수 해석가능성 + 면책 UI:** 필터별 기여 분해(막대/표) + '매수 추천 아님'·신선도 경고를 app·워치리스트에 상시 노출.
- **backtest 실데이터 실행:** 실 KR/US parquet으로 임계치(50/3/1.5) confirm 또는 '미검증 이론값' 명시.

---

## 4. 서비스 아키텍처 — end-to-end (스크리너 + stock-investing 통합)

```
①발굴 → ②평가/점수 → ③워치리스트 → ④결정저널 → ⑤포지션/리스크 → ⑥추적/리뷰
[견고]    [견고/미검증]    [한 방향]      [미착수]      [전무]        [전무]
```

- **①발굴 [견고]:** universe→prices(SQLite 캐시)→build_candidates(drawdown 게이트), 플러그인 레지스트리. *공백:* KR 관리종목/저유동성 제외(→①market_actions·유동성 하한).
- **②평가/점수 [견고하나 미검증]:** apply_filters가 게이트+0~100 스코어러를 정규화 가중평균+is_bonus 후가산. fail-soft·diag 투명화. *공백:* 가중치 미검증, backtest 실데이터 미실행, 이익품질·부도·퀄리티 차원 부재(→§1).
- **③워치리스트 [한 방향]:** to_watchlist 멱등 시드. *공백:* 자동초안 전부 TBD → 한 달 방치(→atr 자동손절·점수분해 초안화).
- **④결정저널 [미착수]:** DECISIONS.md·notes 0건. '왜 샀나'가 안 남음.
- **⑤포지션/리스크 [전무]:** 사이징·계좌 리스크 한도·유동성 하한 0. atr_risk가 첫 입력.
- **⑥추적/리뷰 [전무]:** 시드 후보의 사후 수익 추적·점수 실효성 검증 루프 없음. backtest를 '실제 회복' 라벨 사후검증으로 살리는 게 ⑥의 핵심.
- **데이터 백본:** daily-scan→사이드카→data 브랜치 prime(차단 우회: US 시총=종가×shares). **신규 KR 신호·이익품질 사이드카는 전부 이 prime 패턴 재사용.**

---

## 5. 로드맵

### P0 — 즉시 (정합성·백본·최고ROI 게이트)
- ✅ drawdown −80→−50 / ✅ actions/cache 키 고정 / health.json + 신선도 배너 + 실패 핑
- news 강등 + fail 통일(**사용자 확인 후**)
- **kr_market_action**(관리종목 게이트) · **altman_z**(부도, 게이트는 검증 후) · **piotroski_fscore**(Bundle 확장 1회 fetch) · **net_share_issuance**(KR shares 선결)

### P1 — 단기 (이익품질·KR위험·리스크·신뢰)
- ✅ **atr_risk** / + 워치리스트 손절 자동초안(후속)
- **accruals_quality · gross_profitability**(P0 fetch에 묶어 동시) · **dart_risk_event**
- fundamental 치명/약신호 분리 + KR shares·4Q적자 수정 / 점수 분해·면책 UI / 의존성 핀 / **backtest 실데이터 confirm**

### P2 — 중기 (KR수급·데이터가중·후반부 루프)
- **kr_short_and_flow**(pykrx) / 회복 라벨 IC·IR 가중 재산정 + 백분위 정규화·3축
- rsi↔bollinger·macd↔ma 상관 백테스트→중복 정리(확인 후) / catalyst 보너스 제거(확인 후)
- stock-investing 후반부: DECISIONS.md·사이징·리스크 한도 / 추적·리뷰 피드백 루프 / data 롤백·유동성 하한·섹터 편중 경고

---

## 6. 적대적 검증 반영 — 구현 함정 & 우선순위 정정

> 종합안을 회의적으로 재검증한 결과. **신규 펀더 지표를 만들 때 반드시 지킬 것.**

1. **무음 직렬화 고장 (최우선 주의).** `FundamentalsBundle`에 신규 컬럼을 더할 때 **4곳을 원자적으로** 고쳐야 한다: ① `db.py` SCHEMA(+`_migrate` ALTER), ② `_save` INSERT, ③ **`_load_cached` SELECT(현재 6컬럼만 읽어 캐시 reload 시 신규 필드 유실)**, ④ `snapshot.export_fundamentals`/`load_fundamentals` 사이드카. 하나라도 빠지면 신규 지표가 클라우드에서 조용히 `available=False`(중립50)로 떨어진다 — 2026-05-24 'enrichment 무음 먹통'의 재발. → **F/Z/accruals/GP를 1개 PR로 묶고, effort는 medium→medium-high.**
2. **KR 현금흐름표(CFO) 매핑은 신규 작업.** 현 `_DART_ACCOUNT_IDS`는 IS(손익)+BS(재무상태)만 매핑 — CFO account_id가 없다. piotroski(CFO>NI·ΔROA)·accruals(NI−CFO)는 KR에서 새 매핑 + 불균일 커버리지. "절반은 이미 fetch"는 **US 한정**. KR 결측 시 piotroski=부분점수+available, accruals=available=False로 명시.
3. **적자기업 Z''/F-score 부호 가드.** 우리 유니버스(고폭락=결손누적·영업적자 다수)에서 Z''의 EBIT·RE, F의 ΔROA가 음수가 흔하다. `total_assets<=0`/`equity<=0`/매출=0 시 None→available=False 폴백을 명시하고, **altman 게이트(z<1.1 제외)는 출시 시 OFF(스코어러만) → 백테스트 후 게이트화**(가격 휴리스틱과의 이중 가중 회피).
4. **캘리브레이션 순환참조.** 설계안은 altman 임계·piotroski min·share 곡선·가중치를 모두 '백테스트로 확정'한다고 전제하나, `backtest/`는 합성데이터로만 검증됐고 실 KR/US 회복 라벨 백테스트는 한 번도 안 돌았다. → **'backtest를 실 parquet로 돌려 12개월 회복 라벨 만들기'가 모든 캘리브레이션의 선결**이고, 빠지면 9개 지표 임계가 전부 미검증 이론값으로 남는다.
5. **yfinance 분기 BS/CF 커버리지 선측정.** CFO·current_assets·retained_earnings·Cost Of Revenue는 소형·신규·ADR에서 결측이 흔하다(우리 유니버스 다수). **후보 샘플 50종으로 piotroski 9항목 중 몇 개가 계산 가능한지 coverage를 먼저 측정**해야 effort 추정이 산다.
6. **유동성(거래대금) 하한이 atr_risk보다 먼저.** 폭락주는 거래대금이 말라 실제 진입·사이징이 불가능한 경우가 많다 → KR/US 공통 일평균 거래대금 floor를 base/universe `is_excluded`에 넣는 게 가장 값싼 1차 컷(가격 데이터만, fetch 0).
7. **actions/cache 키 고정은 실측이 뒷받침.** 동일 워크플로 런타임 7m53s(6/11)~1h11m17s(6/22) 9배 편차 = 캐시 miss 시 풀 리페치 패턴. → §7에서 적용.

---

## 7. 오늘 적용된 변경 (2026-06-23)

1. **[추가] ATR 리스크/손절 지표** (`indicators.atr` + `scoring.atr_risk_score` + `filters/atr_risk.py` + `base.load_all` 등록). 일봉 ATR을 가격 대비 %로 측정해 변동성·권장손절폭(2.5×ATR)을 메타데이터로 노출. 비어있던 '리스크/사이징' 차원의 첫 입력. 기본 정보성(weight 0, 제외 안 함). 스모크 통과(필터 15종, ATR 4.6%/손절±11%/score 64, 곡선 2%→100·8%→34·20%→0). **후속(P1): `to_watchlist` 자동초안 손절선을 `close−2.5×ATR`로 채우기.**
2. **[수정] drawdown 기본 임계 −80 → −50** (`filters/drawdown.py`). 클라우드 daily-scan 운영값과 일치 → 스냅샷↔로컬 UI 모집단 불일치 제거.
3. **[수정] GitHub Actions 캐시 키 고정** (`daily-scan.yml`: `screener-db-${{run_id}}` → `screener-db-v1`). 캐시 churn·런타임 편차 제거. **commit+push 해야 프로덕션에 반영됨.**

### 2차 적용 (사용자 승인 후)
4. **[추가/P0] kr_market_action — 관리종목/투자주의환기 게이트** (`data/market_actions.py` + `universe.list_kr` 배선). 두 무료 소스 결합: `fdr.StockListing('KRX-ADMINISTRATIVE')`(관리종목 106) + KRX 리스팅 `Dept` 컬럼('관리종목'·'투자주의환기종목', 추가 fetch 0). 일일 JSON 캐시·fail-soft. **라이브 검증: KR 144종목 후보 진입 전 차단**(금양·메지온 등). is_excluded 인프라에 얹어 코드 최소.
5. **[강등] news 가중 0.30→0.10 + fail-soft 통일** (`filters/news.py`). placeholder 감성에 최고가중이던 미스배분 교정 + 데이터없음→passed=True·중립50·available=False로 **US 전체탈락 버그 제거**(검증: diag[1,1], 행 생존).
6. **[제거] catalyst 점수 보너스 → 기본 0** (`filters/catalyst.py`). 발동조건 협소·KR 커버리지 얇음. ⚠️실적 임박경고는 유지, 슬라이더로 재활성 가능.
7. **[정리] WATCHLIST 미큐레이션 11행** (`stock-investing/WATCHLIST.md`). 삭제 대신 '🗄 보류' 섹션으로 이동·상태 `제외`(데이터 보존). 활성 테이블은 예시행만 남김.

> 보류(사용자 결정): rsi·bollinger·moving_average 중복 정리는 **백테스트로 증분가치 확인 후** 결정(opt-in+런타임정규화라 동시활성 시에만 이중계상).

### 3차 적용 (P0 펀더멘털 묶음 — 1 PR)
8. **[추가/P0] Altman Z''·Piotroski F·accruals·gross_profitability·발행주식수** (5개 신규 필터 + `models.FundamentalsBundle` 확장 + `scoring` 곡선 5종). 검증에이전트가 경고한 **4곳 직렬화 라운드트립을 원자처리**: `db.py` SCHEMA(6컬럼+migrate ALTER) → `_save` INSERT → `_load_cached` SELECT → `snapshot.export/load_fundamentals` 사이드카(구 사이드카 getattr 폴백). **KR DART 매핑 추가**: 총자산·유동자산/부채·이익잉여금·매출총이익(매출원가 폴백)·영업활동현금흐름(CFO). 부호 가드: 적자기업에서 분모≤0/입력결측 시 None→available=False(중립50), Altman 게이트는 OFF(스코어러만, min_score 슬라이더로 게이트화). 부분데이터(은행 등)는 Piotroski를 evaluable로 정규화.
   - **실데이터 검증:** CRL(F3·Z''4.91·자사주−1.9%)/AHCO(F5·Z''3.24) 전신호, FLG(은행) Z·GP=None fail-soft, **SQLite·사이드카 라운드트립 derived 신호 100% 보존**(무음먹통 없음), 엔진 5필터 동작·점수 합성.
   - **남은 것:** KR 발행주식수는 DART 재무제표 밖이라 share_issuance 현재 US만 / Altman·F 임계는 backtest 실데이터 confirm 전까지 이론값.

### 4차 적용 (헬스 + 백테스트 실데이터)
9. **[추가/P0] 헬스 dead-man-switch** — `snapshot.export_health`→`data/health.json`(마지막 스캔·시세일·후보수·enrich available비율), daily_scan 발행 + daily-scan.yml data브랜치 publish·**Actions 실패 텔레그램 핑** + app 신선도 배너(시세 5일↑ 경고 + `gh run list`/`git fetch` 진단). '성공'과 '정상'을 분리.
10. **[검증/P1] backtest 실데이터 실행** — 로컬 5년치(US 6111·KR 1635) OFAT. 상세 `docs/backtest-findings-2026-06-23.md`. **절대수치 신뢰불가**(US 90d +118%=생존편향+유동성하한 부재로 잡주 아티팩트, Sharpe 0.02). **방향성 결론:** ①맨몸 게이트 승률<50%(US 33~40·KR 43~47) → enrichment 필터가 승률의 본령(이번 추가 정당화) ②US 유동성하한 시급(Sharpe~0=노이즈) ③낙폭 −50 방어가능 ④거래량배수 올리면 악화. **임계·가중치 튜닝은 보류**(노이즈·편향 데이터에 과최적화 회피) → 선결: 유동성하한 + 생존편향 보정 백테스트.

### 6차 적용 (KR 위험공시 — dart_risk_event)
12. **[추가/P1] dart_risk_event** — DART **감사의견 비적정**(`accnutAdtorNmNdAdtOpinion`, adt_opinion ∈ 한정/부적정/의견거절) + **주요사항보고서 위험이벤트**(부도 dfOcr·영업정지 bsnSp·회생 ctrcvsBgrq·채권은행관리 bnkMngtPcbg). `FundamentalsBundle.audit_qualified·risk_event`(또 4곳 라운드트립 원자처리: SCHEMA+migrate/_save/_load_cached/사이드카) + `_fetch_kr`에서 fetch(기존 DART 키·corp_map 재사용). **fundamental 필터를 치명/약신호로 분리**: 치명(자본잠식·4Q적자·감사의견·DART이벤트)=단독 제외, 약신호(매출급감·고부채)=min_violations 누적. **실 DART 검증:** 금양 2024 의견거절→audit_qualified=True→min_violations=0에도 단독 제외(관리종목 게이트와 defense-in-depth). KR전용·fail-soft. (이로써 설계 추가 9종 중 8종 구현 완료; LLM 뉴스분류만 유료키로 보류.)

### 5차 적용 (유동성 하한 — 데이터근거 P1)
11. **[추가/P1] 유동성/가격 하한** — `engine.build_candidates`에 시장별 floor(KR ₩5억/일·₩1,000, US $1M/일·$1; `indicators.median_turnover` 중앙값으로 스파이크 방지; 이미 받은 가격으로 계산 fetch 0). `daily_scan --no-liquidity`로 토글, 백테스트에도 `--min-turnover/--min-price` 추가. **검증(US base):** 90d +118.6%→**+6.2%**, 승률 37%→**45%**, Sharpe 0.016→**0.092**(≈6배) — +118% 허수가 페니·잡주였음 확정, KR(0.16)에 근접. US 6,111→**3,699(61%)** 통과. 기본 ON → 다음 daily-scan부터 스냅샷 자동 정제. **다음:** 생존편향 보정(상폐종목 포함) 백테스트 → 그 후 임계·가중치 데이터튜닝.
