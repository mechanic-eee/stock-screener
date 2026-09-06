# 추천 깔때기 체크리스트 — 2026-07-19

> `scripts/recommend.py` 산출. **매수 리스트가 아니다** — 아래 후보를 사람
> 체크(negative screen, 종목당 15분, 베토 주 2건 상한)에 올려 3~5픽으로 좁힌다.
> **⭐ 우선 리서치(시장별 5)부터** — 나머지는 여유 있을 때만.
> 규칙·숫자는 12주 고정 (docs/recommendation-design-2026-07-17.md).

**시세 기준일: 2026-07-17 종가 — 진입·손절·수량 초안의 기준. 주문 전 현재가로 재계산**

**계좌 가정: KR ₩10,000,000 · US $10,000 · R 1.0% (내장 기본값 — data/portfolio.json 없음) — 실계좌와 다르면 수량·비중은 예시일 뿐**

**레짐:** KR 200일선↑ 진입가능(기준 2026-07-16) · US 200일선↑ 진입가능(기준 2026-07-17)

**비용 리마인더:** 왕복 KR ≈0.45%(거래세 0.15% + 슬리피지 0.15%×2) · US ≈0.30% + 양도세(슬리피지 0.15%×2 · 이익의 22% 양도세(연 250만 공제) 별도) — 검증 엣지 +1.3~3.8%p/픽의 12~35%가 비용. 2트랜치 분할해도 %비용은 동일(금액 비례).

## ⭐ 002790 — 아모레퍼시픽홀딩스 (KR) · 점수 84.4 · KR 2/15위 · 낙폭 66% · ATR 5.0%
- 위험공시 라이브 재점검: 생략(--no-fresh-distress) ⚠️
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EC%95%84%EB%AA%A8%EB%A0%88%ED%8D%BC%EC%8B%9C%ED%94%BD%ED%99%80%EB%94%A9%EC%8A%A4) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EC%95%84%EB%AA%A8%EB%A0%88%ED%8D%BC%EC%8B%9C%ED%94%BD%ED%99%80%EB%94%A9%EC%8A%A4) · [네이버금융](https://finance.naver.com/item/main.naver?code=002790)
- 진입초안 25,000원 · 손절초안 21,860원 (−12.6%) · 수량초안 31주 · 포지션 775,000원 (7.8%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker 002790 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 002790` → 큐레이션 → `python scripts/decide.py --ticker 002790 --paper`  (첫 8주 페이퍼/반액)

## ⭐ 259630 — 엠플러스 (KR) · 점수 84.4 · KR 3/15위 · 낙폭 67% · ATR 7.5%
- 위험공시 라이브 재점검: 생략(--no-fresh-distress) ⚠️
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EC%97%A0%ED%94%8C%EB%9F%AC%EC%8A%A4) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EC%97%A0%ED%94%8C%EB%9F%AC%EC%8A%A4) · [네이버금융](https://finance.naver.com/item/main.naver?code=259630)
- 진입초안 9,400원 · 손절초안 7,642원 (−18.7%) · 수량초안 56주 · 포지션 526,400원 (5.3%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker 259630 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 259630` → 큐레이션 → `python scripts/decide.py --ticker 259630 --paper`  (첫 8주 페이퍼/반액)

## ⭐ 260970 — 에스앤디 (KR) · 점수 83.4 · KR 4/15위 · 낙폭 65% · ATR 7.4%
- 위험공시 라이브 재점검: 생략(--no-fresh-distress) ⚠️
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EC%97%90%EC%8A%A4%EC%95%A4%EB%94%94) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EC%97%90%EC%8A%A4%EC%95%A4%EB%94%94) · [네이버금융](https://finance.naver.com/item/main.naver?code=260970)
- 진입초안 51,000원 · 손절초안 41,627원 (−18.4%) · 수량초안 10주 · 포지션 510,000원 (5.1%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker 260970 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 260970` → 큐레이션 → `python scripts/decide.py --ticker 260970 --paper`  (첫 8주 페이퍼/반액)

## ⭐ 215200 — 메가스터디교육 (KR) · 점수 82.9 · KR 5/15위 · 낙폭 63% · ATR 5.2%
- 위험공시 라이브 재점검: 생략(--no-fresh-distress) ⚠️
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EB%A9%94%EA%B0%80%EC%8A%A4%ED%84%B0%EB%94%94%EA%B5%90%EC%9C%A1) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EB%A9%94%EA%B0%80%EC%8A%A4%ED%84%B0%EB%94%94%EA%B5%90%EC%9C%A1) · [네이버금융](https://finance.naver.com/item/main.naver?code=215200)
- 진입초안 38,150원 · 손절초안 33,234원 (−12.9%) · 수량초안 20주 · 포지션 763,000원 (7.6%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker 215200 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 215200` → 큐레이션 → `python scripts/decide.py --ticker 215200 --paper`  (첫 8주 페이퍼/반액)

## ⭐ 008490 — 서흥 (KR) · 점수 82.8 · KR 6/15위 · 낙폭 64% · ATR 5.3%
- 위험공시 라이브 재점검: 생략(--no-fresh-distress) ⚠️
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EC%84%9C%ED%9D%A5) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EC%84%9C%ED%9D%A5) · [네이버금융](https://finance.naver.com/item/main.naver?code=008490)
- 진입초안 20,300원 · 손절초안 17,613원 (−13.2%) · 수량초안 37주 · 포지션 751,100원 (7.5%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker 008490 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 008490` → 큐레이션 → `python scripts/decide.py --ticker 008490 --paper`  (첫 8주 페이퍼/반액)

## 018290 — 브이티 (KR) · 점수 82.1 · KR 7/15위 · 낙폭 73% · ATR 6.6%
- 위험공시 라이브 재점검: 생략(--no-fresh-distress) ⚠️
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EB%B8%8C%EC%9D%B4%ED%8B%B0) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EB%B8%8C%EC%9D%B4%ED%8B%B0) · [네이버금융](https://finance.naver.com/item/main.naver?code=018290)
- 진입초안 11,820원 · 손절초안 9,874원 (−16.5%) · 수량초안 51주 · 포지션 602,820원 (6.0%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker 018290 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 018290` → 큐레이션 → `python scripts/decide.py --ticker 018290 --paper`  (첫 8주 페이퍼/반액)

## 108670 — LX하우시스 (KR) · 점수 81.9 · KR 8/15위 · 낙폭 71% · ATR 5.2%
- 위험공시 라이브 재점검: 생략(--no-fresh-distress) ⚠️
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=LX%ED%95%98%EC%9A%B0%EC%8B%9C%EC%8A%A4) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=LX%ED%95%98%EC%9A%B0%EC%8B%9C%EC%8A%A4) · [네이버금융](https://finance.naver.com/item/main.naver?code=108670)
- 진입초안 31,550원 · 손절초안 27,429원 (−13.1%) · 수량초안 24주 · 포지션 757,200원 (7.6%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker 108670 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 108670` → 큐레이션 → `python scripts/decide.py --ticker 108670 --paper`  (첫 8주 페이퍼/반액)

## 215000 — 골프존 (KR) · 점수 80.8 · KR 10/15위 · 낙폭 79% · ATR 4.3%
- 위험공시 라이브 재점검: 생략(--no-fresh-distress) ⚠️
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EA%B3%A8%ED%94%84%EC%A1%B4) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EA%B3%A8%ED%94%84%EC%A1%B4) · [네이버금융](https://finance.naver.com/item/main.naver?code=215000)
- 진입초안 39,000원 · 손절초안 34,819원 (−10.7%) · 수량초안 23주 · 포지션 897,000원 (9.0%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker 215000 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 215000` → 큐레이션 → `python scripts/decide.py --ticker 215000 --paper`  (첫 8주 페이퍼/반액)

## 000080 — 하이트진로 (KR) · 점수 80.5 · KR 11/15위 · 낙폭 62% · ATR 3.3%
- 위험공시 라이브 재점검: 생략(--no-fresh-distress) ⚠️
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%ED%95%98%EC%9D%B4%ED%8A%B8%EC%A7%84%EB%A1%9C) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%ED%95%98%EC%9D%B4%ED%8A%B8%EC%A7%84%EB%A1%9C) · [네이버금융](https://finance.naver.com/item/main.naver?code=000080)
- 진입초안 14,910원 · 손절초안 13,662원 (−8.4%) · 수량초안 80주 · 포지션 1,192,800원 (11.9%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker 000080 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 000080` → 큐레이션 → `python scripts/decide.py --ticker 000080 --paper`  (첫 8주 페이퍼/반액)

## 383220 — F&F (KR) · 점수 80.2 · KR 13/15위 · 낙폭 60% · ATR 6.2%
- 위험공시 라이브 재점검: 생략(--no-fresh-distress) ⚠️
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=F%26F) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=F%26F) · [네이버금융](https://finance.naver.com/item/main.naver?code=383220)
- 진입초안 79,000원 · 손절초안 66,755원 (−15.5%) · 수량초안 8주 · 포지션 632,000원 (6.3%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker 383220 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 383220` → 큐레이션 → `python scripts/decide.py --ticker 383220 --paper`  (첫 8주 페이퍼/반액)

## 003850 — 보령 (KR) · 점수 80.2 · KR 15/15위 · 낙폭 60% · ATR 4.4%
- 위험공시 라이브 재점검: 생략(--no-fresh-distress) ⚠️
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EB%B3%B4%EB%A0%B9) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EB%B3%B4%EB%A0%B9) · [네이버금융](https://finance.naver.com/item/main.naver?code=003850)
- 진입초안 8,300원 · 손절초안 7,384원 (−11.0%) · 수량초안 109주 · 포지션 904,700원 (9.0%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker 003850 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 003850` → 큐레이션 → `python scripts/decide.py --ticker 003850 --paper`  (첫 8주 페이퍼/반액)

## ⭐ NVO — Novo Nordisk A/S Common Stock (US) · 점수 93.2 · US 1/15위 · Healthcare · 낙폭 63% · ATR 2.6%
- 위험공시 라이브 재점검: 생략(--no-fresh-distress) ⚠️
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=NVO&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=NVO&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=NVO%20stock)
- 진입초안 $50.32 · 손절초안 $47.06 (−6.5%) · 수량초안 29주 · 포지션 $1,459.28 (14.6%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker NVO --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers NVO` → 큐레이션 → `python scripts/decide.py --ticker NVO --paper`  (첫 8주 페이퍼/반액)

## ⭐ NRDS — NerdWallet, Inc. - Class A Common Stock (US) · 점수 86.4 · US 2/15위 · Communication Services · 낙폭 67% · ATR 3.4%
- 위험공시 라이브 재점검: 생략(--no-fresh-distress) ⚠️
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=NRDS&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=NRDS&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=NRDS%20stock)
- 진입초안 $9.26 · 손절초안 $8.46 (−8.6%) · 수량초안 125주 · 포지션 $1,157.50 (11.6%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker NRDS --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers NRDS` → 큐레이션 → `python scripts/decide.py --ticker NRDS --paper`  (첫 8주 페이퍼/반액)

## ⭐ SIRI — SiriusXM Holdings Inc. - Common Stock (US) · 점수 84.3 · US 5/15위 · Communication Services · 낙폭 56% · ATR 2.8%
- 위험공시 라이브 재점검: 생략(--no-fresh-distress) ⚠️
- ⚠️ 섹터 중복: NRDS와 동일 섹터(Communication Services) — 픽은 섹터당 1(점수 상위 우선)
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=SIRI&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=SIRI&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=SIRI%20stock)
- 진입초안 $30.59 · 손절초안 $28.48 (−6.9%) · 수량초안 47주 · 포지션 $1,437.73 (14.4%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker SIRI --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers SIRI` → 큐레이션 → `python scripts/decide.py --ticker SIRI --paper`  (첫 8주 페이퍼/반액)

## ⭐ TME — Tencent Music Entertainment Group American Depositary Shares, each representing two Class A Ordinary Shares (US) · 점수 84.2 · US 6/15위 · Communication Services · 낙폭 64% · ATR 3.4%
- 위험공시 라이브 재점검: 생략(--no-fresh-distress) ⚠️
- ⚠️ 섹터 중복: NRDS와 동일 섹터(Communication Services) — 픽은 섹터당 1(점수 상위 우선)
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=TME&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=TME&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=TME%20stock)
- 진입초안 $9.12 · 손절초안 $8.35 (−8.5%) · 수량초안 129주 · 포지션 $1,176.48 (11.8%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker TME --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers TME` → 큐레이션 → `python scripts/decide.py --ticker TME --paper`  (첫 8주 페이퍼/반액)

## ⭐ BSX — Boston Scientific Corporation Common Stock (US) · 점수 83.9 · US 7/15위 · Healthcare · 낙폭 59% · ATR 3.6%
- 위험공시 라이브 재점검: 생략(--no-fresh-distress) ⚠️
- ⚠️ 섹터 중복: NVO와 동일 섹터(Healthcare) — 픽은 섹터당 1(점수 상위 우선)
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=BSX&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=BSX&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=BSX%20stock)
- 진입초안 $44.03 · 손절초안 $40.02 (−9.1%) · 수량초안 24주 · 포지션 $1,056.72 (10.6%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker BSX --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers BSX` → 큐레이션 → `python scripts/decide.py --ticker BSX --paper`  (첫 8주 페이퍼/반액)

## GOOS — Canada Goose Holdings Inc. Subordinate Voting Shares (US) · 점수 83.9 · US 8/15위 · Consumer Cyclical · 낙폭 82% · ATR 3.2%
- 위험공시 라이브 재점검: 생략(--no-fresh-distress) ⚠️
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=GOOS&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=GOOS&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=GOOS%20stock)
- 진입초안 $9.81 · 손절초안 $9.04 (−7.9%) · 수량초안 129주 · 포지션 $1,265.49 (12.7%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker GOOS --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers GOOS` → 큐레이션 → `python scripts/decide.py --ticker GOOS --paper`  (첫 8주 페이퍼/반액)

## ADMA — ADMA Biologics Inc - Common Stock (US) · 점수 83.1 · US 9/15위 · Healthcare · 낙폭 64% · ATR 3.7%
- 위험공시 라이브 재점검: 생략(--no-fresh-distress) ⚠️
- ⚠️ 섹터 중복: NVO와 동일 섹터(Healthcare) — 픽은 섹터당 1(점수 상위 우선)
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=ADMA&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=ADMA&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=ADMA%20stock)
- 진입초안 $8.71 · 손절초안 $7.91 (−9.1%) · 수량초안 125주 · 포지션 $1,088.75 (10.9%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker ADMA --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers ADMA` → 큐레이션 → `python scripts/decide.py --ticker ADMA --paper`  (첫 8주 페이퍼/반액)

## ROKU — Roku, Inc. - Class A Common Stock (US) · 점수 83.1 · US 10/15위 · Communication Services · 낙폭 70% · ATR 2.0%
- 위험공시 라이브 재점검: 생략(--no-fresh-distress) ⚠️
- ⚠️ 섹터 중복: NRDS와 동일 섹터(Communication Services) — 픽은 섹터당 1(점수 상위 우선)
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=ROKU&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=ROKU&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=ROKU%20stock)
- 진입초안 $144.43 · 손절초안 $137.07 (−5.1%) · 수량초안 10주 · 포지션 $1,444.30 (14.4%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker ROKU --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers ROKU` → 큐레이션 → `python scripts/decide.py --ticker ROKU --paper`  (첫 8주 페이퍼/반액)

## DXCM — DexCom, Inc. - Common Stock (US) · 점수 83.0 · US 11/15위 · Healthcare · 낙폭 53% · ATR 3.7%
- 위험공시 라이브 재점검: 생략(--no-fresh-distress) ⚠️
- ⚠️ 섹터 중복: NVO와 동일 섹터(Healthcare) — 픽은 섹터당 1(점수 상위 우선)
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=DXCM&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=DXCM&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=DXCM%20stock)
- 진입초안 $76.65 · 손절초안 $69.61 (−9.2%) · 수량초안 14주 · 포지션 $1,073.10 (10.7%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker DXCM --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers DXCM` → 큐레이션 → `python scripts/decide.py --ticker DXCM --paper`  (첫 8주 페이퍼/반액)

## AMN — AMN Healthcare Services Inc (US) · 점수 82.6 · US 12/15위 · Healthcare · 낙폭 72% · ATR 5.2%
- 위험공시 라이브 재점검: 생략(--no-fresh-distress) ⚠️
- ⚠️ 섹터 중복: NVO와 동일 섹터(Healthcare) — 픽은 섹터당 1(점수 상위 우선)
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=AMN&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=AMN&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=AMN%20stock)
- 진입초안 $35.00 · 손절초안 $30.48 (−12.9%) · 수량초안 22주 · 포지션 $770.00 (7.7%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker AMN --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers AMN` → 큐레이션 → `python scripts/decide.py --ticker AMN --paper`  (첫 8주 페이퍼/반액)

## MNSO — MINISO Group Holding Limited American Depositary Shares, each representing four Ordinary Shares (US) · 점수 82.5 · US 13/15위 · Consumer Cyclical · 낙폭 54% · ATR 3.5%
- 위험공시 라이브 재점검: 생략(--no-fresh-distress) ⚠️
- ⚠️ 섹터 중복: GOOS와 동일 섹터(Consumer Cyclical) — 픽은 섹터당 1(점수 상위 우선)
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=MNSO&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=MNSO&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=MNSO%20stock)
- 진입초안 $12.75 · 손절초안 $11.65 (−8.7%) · 수량초안 90주 · 포지션 $1,147.50 (11.5%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker MNSO --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers MNSO` → 큐레이션 → `python scripts/decide.py --ticker MNSO --paper`  (첫 8주 페이퍼/반액)

## OTEX — Open Text Corporation - Common Shares (US) · 점수 82.4 · US 14/15위 · Technology · 낙폭 51% · ATR 3.8%
- 위험공시 라이브 재점검: 생략(--no-fresh-distress) ⚠️
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=OTEX&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=OTEX&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=OTEX%20stock)
- 진입초안 $23.27 · 손절초안 $21.03 (−9.6%) · 수량초안 44주 · 포지션 $1,023.88 (10.2%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (수동 — universe sector 미구축): 
- 탈락 시: `python scripts/decide.py --ticker OTEX --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers OTEX` → 큐레이션 → `python scripts/decide.py --ticker OTEX --paper`  (첫 8주 페이퍼/반액)

## 게이트 탈락 (사유 기록 — 사후 검증 대상)

- 317450 (KR, 점수 87.5): 펀더 결측 1건(piotroski) — 결측-중립 함정
- 010780 (KR, 점수 80.8): ATR 8.9% > 8% [재량]
- 382800 (KR, 점수 80.3): ATR 11.2% > 8% [재량]
- 439260 (KR, 점수 80.2): 펀더 결측 1건(piotroski) — 결측-중립 함정
- BZ (US, 점수 85.4): 펀더 결측 1건(altman_z) — 결측-중립 함정
- MCHB (US, 점수 84.8): 펀더 결측 3건(altman_z,piotroski,gross_profit) — 결측-중립 함정
- LOB (US, 점수 82.4): 펀더 결측 2건(altman_z,gross_profit) — 결측-중립 함정

## 다음 단계

- 확정 픽은 **당일~익일 현재가 부근 즉시** 1차 트랜치(50%) — 눌림 대기 금지 [검증]
- 2차 트랜치 +2~4주 시간 기반 [재량] · 캘린더에 2차일·120d 리뷰일 기록
- 관망 탈락도 반드시 decide.py로 기록 — 베토 실효성 검증 데이터
