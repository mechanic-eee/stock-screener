# 추천 깔때기 체크리스트 — 2026-07-17

> `scripts/recommend.py` 산출. **매수 리스트가 아니다** — 아래 후보를 사람
> 체크(negative screen, 종목당 15분, 베토 주 2건 상한)에 올려 3~5픽으로 좁힌다.
> 규칙·숫자는 12주 고정 (docs/recommendation-design-2026-07-17.md).

**레짐:** KR 200일선↑ 진입가능 · US 200일선↑ 진입가능

**비용 리마인더:** 왕복 KR ≈0.45%(거래세 0.15% + 슬리피지 0.15%×2) · US ≈0.30%(슬리피지 0.15%×2) — 검증 엣지 +1.3~3.8%p/픽의 12~35%가 비용. 2트랜치 분할해도 %비용은 동일(금액 비례).

## 259630 — 엠플러스 (KR) · 점수 84.7 · 낙폭 66% · ATR 7.4%
- 진입초안 9,720원 · 손절초안 7,923원 (−18.5%) · 수량초안 55주 · 포지션 534,600원 (5.3%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker 259630 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 259630` → 큐레이션 → `python scripts/decide.py --ticker 259630 --paper`  (첫 8주 페이퍼/반액)

## 002790 — 아모레퍼시픽홀딩스 (KR) · 점수 83.5 · 낙폭 70% · ATR 5.2%
- 진입초안 23,950원 · 손절초안 20,838원 (−13.0%) · 수량초안 32주 · 포지션 766,400원 (7.7%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker 002790 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 002790` → 큐레이션 → `python scripts/decide.py --ticker 002790 --paper`  (첫 8주 페이퍼/반액)

## 260970 — 에스앤디 (KR) · 점수 83.1 · 낙폭 66% · ATR 7.6%
- 진입초안 49,950원 · 손절초안 40,481원 (−19.0%) · 수량초안 10주 · 포지션 499,500원 (5.0%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker 260970 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 260970` → 큐레이션 → `python scripts/decide.py --ticker 260970 --paper`  (첫 8주 페이퍼/반액)

## 008490 — 서흥 (KR) · 점수 83.0 · 낙폭 63% · ATR 4.9%
- 진입초안 21,350원 · 손절초안 18,735원 (−12.2%) · 수량초안 38주 · 포지션 811,300원 (8.1%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker 008490 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 008490` → 큐레이션 → `python scripts/decide.py --ticker 008490 --paper`  (첫 8주 페이퍼/반액)

## 215200 — 메가스터디교육 (KR) · 점수 82.5 · 낙폭 63% · ATR 5.3%
- 진입초안 38,400원 · 손절초안 33,299원 (−13.3%) · 수량초안 19주 · 포지션 729,600원 (7.3%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker 215200 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 215200` → 큐레이션 → `python scripts/decide.py --ticker 215200 --paper`  (첫 8주 페이퍼/반액)

## 018290 — 브이티 (KR) · 점수 82.4 · 낙폭 73% · ATR 6.5%
- 진입초안 12,080원 · 손절초안 10,124원 (−16.2%) · 수량초안 51주 · 포지션 616,080원 (6.2%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker 018290 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 018290` → 큐레이션 → `python scripts/decide.py --ticker 018290 --paper`  (첫 8주 페이퍼/반액)

## 108670 — LX하우시스 (KR) · 점수 81.8 · 낙폭 71% · ATR 5.3%
- 진입초안 31,550원 · 손절초안 27,382원 (−13.2%) · 수량초안 23주 · 포지션 725,650원 (7.3%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker 108670 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 108670` → 큐레이션 → `python scripts/decide.py --ticker 108670 --paper`  (첫 8주 페이퍼/반액)

## 000080 — 하이트진로 (KR) · 점수 80.9 · 낙폭 64% · ATR 3.4%
- 진입초안 14,550원 · 손절초안 13,331원 (−8.4%) · 수량초안 82주 · 포지션 1,193,100원 (11.9%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker 000080 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 000080` → 큐레이션 → `python scripts/decide.py --ticker 000080 --paper`  (첫 8주 페이퍼/반액)

## 215000 — 골프존 (KR) · 점수 80.6 · 낙폭 79% · ATR 4.4%
- 진입초안 39,000원 · 손절초안 34,689원 (−11.1%) · 수량초안 23주 · 포지션 897,000원 (9.0%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker 215000 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 215000` → 큐레이션 → `python scripts/decide.py --ticker 215000 --paper`  (첫 8주 페이퍼/반액)

## 003850 — 보령 (KR) · 점수 80.1 · 낙폭 60% · ATR 4.6%
- 진입초안 8,220원 · 손절초안 7,280원 (−11.4%) · 수량초안 106주 · 포지션 871,320원 (8.7%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker 003850 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 003850` → 큐레이션 → `python scripts/decide.py --ticker 003850 --paper`  (첫 8주 페이퍼/반액)

## 439090 — 마녀공장 (KR) · 점수 80.1 · 낙폭 65% · ATR 7.4%
- 진입초안 16,580원 · 손절초안 13,509원 (−18.5%) · 수량초안 32주 · 포지션 530,560원 (5.3%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker 439090 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 439090` → 큐레이션 → `python scripts/decide.py --ticker 439090 --paper`  (첫 8주 페이퍼/반액)

## 383220 — F&F (KR) · 점수 80.0 · 낙폭 60% · ATR 6.4%
- 진입초안 78,500원 · 손절초안 66,024원 (−15.9%) · 수량초안 8주 · 포지션 628,000원 (6.3%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker 383220 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 383220` → 큐레이션 → `python scripts/decide.py --ticker 383220 --paper`  (첫 8주 페이퍼/반액)

## NVO — Novo Nordisk A/S Common Stock (US) · 점수 93.1 · 낙폭 63% · ATR 2.6%
- 진입초안 $50.56 · 손절초안 $47.26 (−6.5%) · 수량초안 30주 · 포지션 $1,516.80 (15.2%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker NVO --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers NVO` → 큐레이션 → `python scripts/decide.py --ticker NVO --paper`  (첫 8주 페이퍼/반액)

## NRDS — NerdWallet, Inc. - Class A Common Stock (US) · 점수 86.6 · 낙폭 66% · ATR 3.4%
- 진입초안 $9.53 · 손절초안 $8.72 (−8.5%) · 수량초안 123주 · 포지션 $1,172.19 (11.7%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker NRDS --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers NRDS` → 큐레이션 → `python scripts/decide.py --ticker NRDS --paper`  (첫 8주 페이퍼/반액)

## TME — Tencent Music Entertainment Group American Depositary Shares, each representing two Class A Ordinary Shares (US) · 점수 84.7 · 낙폭 65% · ATR 3.2%
- 진입초안 $8.86 · 손절초안 $8.15 (−8.0%) · 수량초안 140주 · 포지션 $1,240.40 (12.4%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker TME --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers TME` → 큐레이션 → `python scripts/decide.py --ticker TME --paper`  (첫 8주 페이퍼/반액)

## BSX — Boston Scientific Corporation Common Stock (US) · 점수 84.4 · 낙폭 60% · ATR 3.6%
- 진입초안 $43.04 · 손절초안 $39.16 (−9.0%) · 수량초안 25주 · 포지션 $1,076.00 (10.8%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker BSX --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers BSX` → 큐레이션 → `python scripts/decide.py --ticker BSX --paper`  (첫 8주 페이퍼/반액)

## SIRI — SiriusXM Holdings Inc. - Common Stock (US) · 점수 84.1 · 낙폭 56% · ATR 2.8%
- 진입초안 $30.65 · 손절초안 $28.51 (−7.0%) · 수량초안 46주 · 포지션 $1,409.90 (14.1%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker SIRI --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers SIRI` → 큐레이션 → `python scripts/decide.py --ticker SIRI --paper`  (첫 8주 페이퍼/반액)

## DXCM — DexCom, Inc. - Common Stock (US) · 점수 83.9 · 낙폭 55% · ATR 3.6%
- 진입초안 $72.73 · 손절초안 $66.23 (−8.9%) · 수량초안 15주 · 포지션 $1,090.95 (10.9%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker DXCM --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers DXCM` → 큐레이션 → `python scripts/decide.py --ticker DXCM --paper`  (첫 8주 페이퍼/반액)

## GOOS — Canada Goose Holdings Inc. Subordinate Voting Shares (US) · 점수 83.5 · 낙폭 82% · ATR 3.3%
- 진입초안 $9.66 · 손절초안 $8.86 (−8.3%) · 수량초안 125주 · 포지션 $1,207.50 (12.1%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker GOOS --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers GOOS` → 큐레이션 → `python scripts/decide.py --ticker GOOS --paper`  (첫 8주 페이퍼/반액)

## ADMA — ADMA Biologics Inc - Common Stock (US) · 점수 82.8 · 낙폭 65% · ATR 3.8%
- 진입초안 $8.68 · 손절초안 $7.86 (−9.5%) · 수량초안 121주 · 포지션 $1,050.28 (10.5%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker ADMA --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers ADMA` → 큐레이션 → `python scripts/decide.py --ticker ADMA --paper`  (첫 8주 페이퍼/반액)

## MNSO — MINISO Group Holding Limited American Depositary Shares, each representing four Ordinary Shares (US) · 점수 82.8 · 낙폭 54% · ATR 3.4%
- 진입초안 $12.62 · 손절초안 $11.54 (−8.5%) · 수량초안 92주 · 포지션 $1,161.04 (11.6%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker MNSO --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers MNSO` → 큐레이션 → `python scripts/decide.py --ticker MNSO --paper`  (첫 8주 페이퍼/반액)

## OTEX — Open Text Corporation - Common Shares (US) · 점수 82.5 · 낙폭 52% · ATR 4.0%
- 진입초안 $22.75 · 손절초안 $20.47 (−10.0%) · 수량초안 43주 · 포지션 $978.25 (9.8%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker OTEX --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers OTEX` → 큐레이션 → `python scripts/decide.py --ticker OTEX --paper`  (첫 8주 페이퍼/반액)

## ROKU — Roku, Inc. - Class A Common Stock (US) · 점수 82.5 · 낙폭 70% · ATR 2.2%
- 진입초안 $143.32 · 손절초안 $135.28 (−5.6%) · 수량초안 12주 · 포지션 $1,719.84 (17.2%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker ROKU --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers ROKU` → 큐레이션 → `python scripts/decide.py --ticker ROKU --paper`  (첫 8주 페이퍼/반액)

## AMN — AMN Healthcare Services Inc (US) · 점수 82.5 · 낙폭 75% · ATR 5.1%
- 진입초안 $32.35 · 손절초안 $28.19 (−12.9%) · 수량초안 24주 · 포지션 $776.40 (7.8%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker AMN --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers AMN` → 큐레이션 → `python scripts/decide.py --ticker AMN --paper`  (첫 8주 페이퍼/반액)

## 게이트 탈락 (사유 기록 — 사후 검증 대상)

- 317450 (KR, 점수 87.4): 펀더 결측 1건(piotroski) — 결측-중립 함정
- 010780 (KR, 점수 80.8): ATR 8.9% > 8% [재량]
- 382800 (KR, 점수 79.9): ATR 10.9% > 8% [재량]
- MCHB (US, 점수 85.3): 펀더 결측 3건(altman_z,piotroski,gross_profit) — 결측-중립 함정
- BZ (US, 점수 85.2): 펀더 결측 1건(altman_z) — 결측-중립 함정
- LOB (US, 점수 83.1): 펀더 결측 2건(altman_z,gross_profit) — 결측-중립 함정

## 다음 단계

- 확정 픽은 **당일~익일 현재가 부근 즉시** 1차 트랜치(50%) — 눌림 대기 금지 [검증]
- 2차 트랜치 +2~4주 시간 기반 [재량] · 캘린더에 2차일·120d 리뷰일 기록
- 관망 탈락도 반드시 decide.py로 기록 — 베토 실효성 검증 데이터
