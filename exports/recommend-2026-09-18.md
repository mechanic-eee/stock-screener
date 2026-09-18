# 추천 깔때기 체크리스트 — 2026-09-18

> `scripts/recommend.py` 산출. **매수 리스트가 아니다** — 아래 후보를 사람
> 체크(negative screen, 종목당 15분, 베토 주 2건 상한)에 올려 3~5픽으로 좁힌다.
> **⭐ 우선 리서치(시장별 5)부터** — 나머지는 여유 있을 때만.
> 규칙·숫자는 12주 고정 (docs/recommendation-design-2026-07-17.md).

**시세 기준일: 2026-09-18 종가 — 진입·손절·수량 초안의 기준. 주문 전 현재가로 재계산**
펀더 기준: KR 2026-06-30(중앙값) · US 2026-06-30(중앙값) — 점수·게이트가 본 재무 분기

**계좌 가정: KR ₩8,147,431 · US $9,810 · R 1.0% (data/portfolio.json) — 실계좌와 다르면 수량·비중은 예시일 뿐 · ⛔ 실계좌 신규 진입 차단 중(히트 12.2% > 6%) — 이번 픽은 페이퍼만, 실계좌는 축소 후**

**레짐:** US 200일선↑ 진입가능 +5.3%(기준 2026-09-16)

**비용 리마인더:** 왕복 KR ≈0.45%(거래세 0.15% + 슬리피지 0.15%×2) · US ≈0.30% + 양도세(슬리피지 0.15%×2 · 이익의 22% 양도세(연 250만 공제) 별도) — 검증 엣지 +1.3~3.8%p/픽의 12~35%가 비용. 2트랜치 분할해도 %비용은 동일(금액 비례).

## ⭐ NVO — Novo Nordisk A/S Common Stock (US) · 점수 85.6 · US 3/15위 · Healthcare · 낙폭 69% · ATR 3.0%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=NVO&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=NVO&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=NVO%20stock)
- 진입초안 $41.71 · 손절초안 $38.62 (−7.4%) · 수량초안 31주 · 포지션 $1,293.01 (13.2%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker NVO --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers NVO` → 큐레이션 → `python scripts/decide.py --ticker NVO --paper`  (첫 8주 페이퍼/반액)

## ⭐ VET — Vermilion Energy Inc. Common (Canada) (US) · 점수 84.6 · US 4/15위 · Energy · 낙폭 52% · ATR 3.8%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=VET&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=VET&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=VET%20stock)
- 진입초안 $12.62 · 손절초안 $11.41 (−9.5%) · 수량초안 81주 · 포지션 $1,022.22 (10.4%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker VET --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers VET` → 큐레이션 → `python scripts/decide.py --ticker VET --paper`  (첫 8주 페이퍼/반액)

## ⭐ ROKU — Roku, Inc. - Class A Common Stock (US) · 점수 83.5 · US 6/15위 · Communication Services · 낙폭 55% · ATR 1.4%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=ROKU&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=ROKU&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=ROKU%20stock)
- 진입초안 $155.12 · 손절초안 $149.74 (−3.5%) · 수량초안 9주 · 포지션 $1,396.08 (14.2%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker ROKU --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers ROKU` → 큐레이션 → `python scripts/decide.py --ticker ROKU --paper`  (첫 8주 페이퍼/반액)

## ⭐ DV — DoubleVerify Holdings, Inc. Common Stock (US) · 점수 82.7 · US 8/15위 · Communication Services · 낙폭 68% · ATR 1.0%
- 위험공시 라이브 재점검: 통과
- ⚠️ 섹터 중복: ROKU와 동일 섹터(Communication Services) — 픽은 섹터당 1(점수 상위 우선)
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=DV&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=DV&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=DV%20stock)
- 진입초안 $13.49 · 손절초안 $13.17 (−2.4%) · 수량초안 109주 · 포지션 $1,470.41 (15.0%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker DV --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers DV` → 큐레이션 → `python scripts/decide.py --ticker DV --paper`  (첫 8주 페이퍼/반액)

## ⭐ CRCT — Cricut, Inc. - Class A common stock (US) · 점수 82.5 · US 9/15위 · Technology · 낙폭 76% · ATR 3.8%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=CRCT&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=CRCT&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=CRCT%20stock)
- 진입초안 $5.59 · 손절초안 $5.06 (−9.5%) · 수량초안 184주 · 포지션 $1,028.56 (10.5%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker CRCT --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers CRCT` → 큐레이션 → `python scripts/decide.py --ticker CRCT --paper`  (첫 8주 페이퍼/반액)

## VIR — Vir Biotechnology, Inc. - Common Stock (US) · 점수 82.4 · US 10/15위 · Healthcare · 낙폭 81% · ATR 4.9%
- 위험공시 라이브 재점검: 통과
- ⚠️ 섹터 중복: NVO와 동일 섹터(Healthcare) — 픽은 섹터당 1(점수 상위 우선)
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=VIR&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=VIR&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=VIR%20stock)
- 진입초안 $10.52 · 손절초안 $9.22 (−12.3%) · 수량초안 75주 · 포지션 $789.00 (8.0%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker VIR --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers VIR` → 큐레이션 → `python scripts/decide.py --ticker VIR --paper`  (첫 8주 페이퍼/반액)

## PDD — PDD Holdings Inc. - American Depositary Shares (US) · 점수 82.1 · US 12/15위 · Consumer Cyclical · 낙폭 50% · ATR 2.6%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=PDD&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=PDD&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=PDD%20stock)
- 진입초안 $78.76 · 손절초안 $73.64 (−6.5%) · 수량초안 18주 · 포지션 $1,417.68 (14.5%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker PDD --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers PDD` → 큐레이션 → `python scripts/decide.py --ticker PDD --paper`  (첫 8주 페이퍼/반액)

## SIRI — SiriusXM Holdings Inc. - Common Stock (US) · 점수 82.1 · US 13/15위 · Communication Services · 낙폭 59% · ATR 2.8%
- 위험공시 라이브 재점검: 통과
- ⚠️ 섹터 중복: ROKU와 동일 섹터(Communication Services) — 픽은 섹터당 1(점수 상위 우선)
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=SIRI&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=SIRI&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=SIRI%20stock)
- 진입초안 $28.56 · 손절초안 $26.56 (−7.0%) · 수량초안 49주 · 포지션 $1,399.44 (14.3%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker SIRI --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers SIRI` → 큐레이션 → `python scripts/decide.py --ticker SIRI --paper`  (첫 8주 페이퍼/반액)

## PODD — Insulet Corporation - Common Stock (US) · 점수 81.6 · US 14/15위 · Healthcare · 낙폭 60% · ATR 4.1%
- 위험공시 라이브 재점검: 통과
- ⚠️ 섹터 중복: NVO와 동일 섹터(Healthcare) — 픽은 섹터당 1(점수 상위 우선)
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=PODD&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=PODD&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=PODD%20stock)
- 진입초안 $140.60 · 손절초안 $126.24 (−10.2%) · 수량초안 6주 · 포지션 $843.60 (8.6%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker PODD --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers PODD` → 큐레이션 → `python scripts/decide.py --ticker PODD --paper`  (첫 8주 페이퍼/반액)

## CAL — Caleres, Inc. Common Stock (US) · 점수 81.2 · US 15/15위 · Consumer Cyclical · 낙폭 71% · ATR 6.0%
- 위험공시 라이브 재점검: 통과
- ⚠️ 섹터 중복: PDD와 동일 섹터(Consumer Cyclical) — 픽은 섹터당 1(점수 상위 우선)
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=CAL&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=CAL&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=CAL%20stock)
- 진입초안 $12.02 · 손절초안 $10.23 (−14.9%) · 수량초안 54주 · 포지션 $649.08 (6.6%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker CAL --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers CAL` → 큐레이션 → `python scripts/decide.py --ticker CAL --paper`  (첫 8주 페이퍼/반액)

## 게이트 탈락 (사유 기록 — 사후 검증 대상)

- DEO (US, 점수 88.5): 펀더 결측 4건(fundamental,altman_z,piotroski,gross_profit) — 결측-중립 함정
- IVR (US, 점수 88.1): 펀더 결측 2건(altman_z,gross_profit) — 결측-중립 함정
- MCHB (US, 점수 83.7): 펀더 결측 3건(altman_z,piotroski,gross_profit) — 결측-중립 함정
- WPP (US, 점수 83.1): 펀더 결측 4건(fundamental,altman_z,piotroski,gross_profit) — 결측-중립 함정
- BZ (US, 점수 82.2): 펀더 결측 1건(altman_z) — 결측-중립 함정

## 다음 단계

- 확정 픽은 **당일~익일 현재가 부근 즉시** 1차 트랜치(50%) — 눌림 대기 금지 [검증]
- 2차 트랜치 +2~4주 시간 기반 [재량] · 캘린더에 2차일·120d 리뷰일 기록
- 관망 탈락도 반드시 decide.py로 기록 — 베토 실효성 검증 데이터
