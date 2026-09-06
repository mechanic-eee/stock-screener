# 추천 깔때기 체크리스트 — 2026-08-21

> `scripts/recommend.py` 산출. **매수 리스트가 아니다** — 아래 후보를 사람
> 체크(negative screen, 종목당 15분, 베토 주 2건 상한)에 올려 3~5픽으로 좁힌다.
> **⭐ 우선 리서치(시장별 5)부터** — 나머지는 여유 있을 때만.
> 규칙·숫자는 12주 고정 (docs/recommendation-design-2026-07-17.md).

**시세 기준일: 2026-08-20 종가 ⚠️ 1영업일 낡음 — 휴장 또는 스캔 지연 확인 — 진입·손절·수량 초안의 기준. 주문 전 현재가로 재계산**

**계좌 가정: KR ₩7,432,431 · US $9,559 · R 1.0% (data/portfolio.json) — 실계좌와 다르면 수량·비중은 예시일 뿐**

**레짐:** KR 200일선↑ 진입가능 +15.8%(기준 2026-08-20) · US 200일선↑ 진입가능 +7.7%(기준 2026-08-20)

**비용 리마인더:** 왕복 KR ≈0.45%(거래세 0.15% + 슬리피지 0.15%×2) · US ≈0.30% + 양도세(슬리피지 0.15%×2 · 이익의 22% 양도세(연 250만 공제) 별도) — 검증 엣지 +1.3~3.8%p/픽의 12~35%가 비용. 2트랜치 분할해도 %비용은 동일(금액 비례).

## ⭐ 259630 — 엠플러스 (KR) · 점수 86.8 · KR 1/15위 · 낙폭 67% · ATR 5.9%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EC%97%A0%ED%94%8C%EB%9F%AC%EC%8A%A4) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EC%97%A0%ED%94%8C%EB%9F%AC%EC%8A%A4) · [네이버금융](https://finance.naver.com/item/main.naver?code=259630)
- 진입초안 9,390원 · 손절초안 7,998원 (−14.8%) · 수량초안 53주 · 포지션 497,670원 (6.7%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 259630 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 259630` → 큐레이션 → `python scripts/decide.py --ticker 259630 --paper`  (첫 8주 페이퍼/반액)

## ⭐ 215200 — 메가스터디교육 (KR) · 점수 84.7 · KR 3/15위 · 낙폭 65% · ATR 4.5%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EB%A9%94%EA%B0%80%EC%8A%A4%ED%84%B0%EB%94%94%EA%B5%90%EC%9C%A1) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EB%A9%94%EA%B0%80%EC%8A%A4%ED%84%B0%EB%94%94%EA%B5%90%EC%9C%A1) · [네이버금융](https://finance.naver.com/item/main.naver?code=215200)
- 진입초안 36,350원 · 손절초안 32,279원 (−11.2%) · 수량초안 18주 · 포지션 654,300원 (8.8%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 215200 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 215200` → 큐레이션 → `python scripts/decide.py --ticker 215200 --paper`  (첫 8주 페이퍼/반액)

## ⭐ 020000 — 한섬 (KR) · 점수 84.3 · KR 4/15위 · 낙폭 65% · ATR 6.2%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%ED%95%9C%EC%84%AC) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%ED%95%9C%EC%84%AC) · [네이버금융](https://finance.naver.com/item/main.naver?code=020000)
- 진입초안 15,360원 · 손절초안 12,985원 (−15.5%) · 수량초안 31주 · 포지션 476,160원 (6.4%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 020000 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 020000` → 큐레이션 → `python scripts/decide.py --ticker 020000 --paper`  (첫 8주 페이퍼/반액)

## ⭐ 108670 — LX하우시스 (KR) · 점수 83.9 · KR 5/15위 · 낙폭 66% · ATR 4.5%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=LX%ED%95%98%EC%9A%B0%EC%8B%9C%EC%8A%A4) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=LX%ED%95%98%EC%9A%B0%EC%8B%9C%EC%8A%A4) · [네이버금융](https://finance.naver.com/item/main.naver?code=108670)
- 진입초안 34,500원 · 손절초안 30,598원 (−11.3%) · 수량초안 19주 · 포지션 655,500원 (8.8%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 108670 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 108670` → 큐레이션 → `python scripts/decide.py --ticker 108670 --paper`  (첫 8주 페이퍼/반액)

## ⭐ 002790 — 아모레퍼시픽홀딩스 (KR) · 점수 83.5 · KR 6/15위 · 낙폭 57% · ATR 4.4%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EC%95%84%EB%AA%A8%EB%A0%88%ED%8D%BC%EC%8B%9C%ED%94%BD%ED%99%80%EB%94%A9%EC%8A%A4) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EC%95%84%EB%AA%A8%EB%A0%88%ED%8D%BC%EC%8B%9C%ED%94%BD%ED%99%80%EB%94%A9%EC%8A%A4) · [네이버금융](https://finance.naver.com/item/main.naver?code=002790)
- 진입초안 25,900원 · 손절초안 23,020원 (−11.1%) · 수량초안 25주 · 포지션 647,500원 (8.7%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 002790 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 002790` → 큐레이션 → `python scripts/decide.py --ticker 002790 --paper`  (첫 8주 페이퍼/반액)

## 260970 — 에스앤디 (KR) · 점수 83.1 · KR 7/15위 · 낙폭 65% · ATR 7.6%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EC%97%90%EC%8A%A4%EC%95%A4%EB%94%94) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EC%97%90%EC%8A%A4%EC%95%A4%EB%94%94) · [네이버금융](https://finance.naver.com/item/main.naver?code=260970)
- 진입초안 51,100원 · 손절초안 41,452원 (−18.9%) · 수량초안 7주 · 포지션 357,700원 (4.8%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 260970 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 260970` → 큐레이션 → `python scripts/decide.py --ticker 260970 --paper`  (첫 8주 페이퍼/반액)

## 051160 — 지어소프트 (KR) · 점수 82.6 · KR 8/15위 · 낙폭 65% · ATR 6.3%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EC%A7%80%EC%96%B4%EC%86%8C%ED%94%84%ED%8A%B8) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EC%A7%80%EC%96%B4%EC%86%8C%ED%94%84%ED%8A%B8) · [네이버금융](https://finance.naver.com/item/main.naver?code=051160)
- 진입초안 9,570원 · 손절초안 8,070원 (−15.7%) · 수량초안 49주 · 포지션 468,930원 (6.3%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 051160 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 051160` → 큐레이션 → `python scripts/decide.py --ticker 051160 --paper`  (첫 8주 페이퍼/반액)

## 018290 — 브이티 (KR) · 점수 82.0 · KR 9/15위 · 낙폭 72% · ATR 6.8%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EB%B8%8C%EC%9D%B4%ED%8B%B0) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EB%B8%8C%EC%9D%B4%ED%8B%B0) · [네이버금융](https://finance.naver.com/item/main.naver?code=018290)
- 진입초안 12,620원 · 손절초안 10,488원 (−16.9%) · 수량초안 34주 · 포지션 429,080원 (5.8%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 018290 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 018290` → 큐레이션 → `python scripts/decide.py --ticker 018290 --paper`  (첫 8주 페이퍼/반액)

## 099430 — 바이오플러스 (KR) · 점수 82.0 · KR 10/15위 · 낙폭 61% · ATR 6.0%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EB%B0%94%EC%9D%B4%EC%98%A4%ED%94%8C%EB%9F%AC%EC%8A%A4) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EB%B0%94%EC%9D%B4%EC%98%A4%ED%94%8C%EB%9F%AC%EC%8A%A4) · [네이버금융](https://finance.naver.com/item/main.naver?code=099430)
- 진입초안 3,475원 · 손절초안 2,955원 (−15.0%) · 수량초안 142주 · 포지션 493,450원 (6.6%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 099430 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 099430` → 큐레이션 → `python scripts/decide.py --ticker 099430 --paper`  (첫 8주 페이퍼/반액)

## 383220 — F&F (KR) · 점수 81.6 · KR 11/15위 · 낙폭 68% · ATR 6.4%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=F%26F) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=F%26F) · [네이버금융](https://finance.naver.com/item/main.naver?code=383220)
- 진입초안 61,900원 · 손절초안 51,924원 (−16.1%) · 수량초안 7주 · 포지션 433,300원 (5.8%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 383220 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 383220` → 큐레이션 → `python scripts/decide.py --ticker 383220 --paper`  (첫 8주 페이퍼/반액)

## 215000 — 골프존 (KR) · 점수 81.1 · KR 12/15위 · 낙폭 81% · ATR 3.8%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EA%B3%A8%ED%94%84%EC%A1%B4) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EA%B3%A8%ED%94%84%EC%A1%B4) · [네이버금융](https://finance.naver.com/item/main.naver?code=215000)
- 진입초안 34,900원 · 손절초안 31,595원 (−9.5%) · 수량초안 22주 · 포지션 767,800원 (10.3%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 215000 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 215000` → 큐레이션 → `python scripts/decide.py --ticker 215000 --paper`  (첫 8주 페이퍼/반액)

## 000080 — 하이트진로 (KR) · 점수 80.7 · KR 15/15위 · 낙폭 60% · ATR 3.0%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%ED%95%98%EC%9D%B4%ED%8A%B8%EC%A7%84%EB%A1%9C) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%ED%95%98%EC%9D%B4%ED%8A%B8%EC%A7%84%EB%A1%9C) · [네이버금융](https://finance.naver.com/item/main.naver?code=000080)
- 진입초안 15,130원 · 손절초안 14,000원 (−7.5%) · 수량초안 65주 · 포지션 983,450원 (13.2%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 000080 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 000080` → 큐레이션 → `python scripts/decide.py --ticker 000080 --paper`  (첫 8주 페이퍼/반액)

## ⭐ NVO — Novo Nordisk A/S Common Stock (US) · 점수 92.5 · US 1/15위 · Healthcare · 낙폭 66% · ATR 3.1%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=NVO&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=NVO&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=NVO%20stock)
- 진입초안 $46.14 · 손절초안 $42.59 (−7.7%) · 수량초안 26주 · 포지션 $1,199.64 (12.5%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker NVO --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers NVO` → 큐레이션 → `python scripts/decide.py --ticker NVO --paper`  (첫 8주 페이퍼/반액)

## ⭐ NRDS — NerdWallet, Inc. - Class A Common Stock (US) · 점수 85.5 · US 4/15위 · Communication Services · 낙폭 65% · ATR 3.8%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=NRDS&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=NRDS&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=NRDS%20stock)
- 진입초안 $10.01 · 손절초안 $9.05 (−9.6%) · 수량초안 99주 · 포지션 $990.99 (10.4%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker NRDS --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers NRDS` → 큐레이션 → `python scripts/decide.py --ticker NRDS --paper`  (첫 8주 페이퍼/반액)

## ⭐ MNSO — MINISO Group Holding Limited American Depositary Shares, each representing four Ordinary Shares (US) · 점수 85.5 · US 5/15위 · Consumer Cyclical · 낙폭 59% · ATR 3.1%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=MNSO&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=MNSO&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=MNSO%20stock)
- 진입초안 $11.13 · 손절초안 $10.25 (−7.9%) · 수량초안 109주 · 포지션 $1,213.17 (12.7%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker MNSO --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers MNSO` → 큐레이션 → `python scripts/decide.py --ticker MNSO --paper`  (첫 8주 페이퍼/반액)

## ⭐ SIRI — SiriusXM Holdings Inc. - Common Stock (US) · 점수 84.8 · US 6/15위 · Communication Services · 낙폭 59% · ATR 3.0%
- 위험공시 라이브 재점검: 통과
- ⚠️ 섹터 중복: NRDS와 동일 섹터(Communication Services) — 픽은 섹터당 1(점수 상위 우선)
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=SIRI&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=SIRI&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=SIRI%20stock)
- 진입초안 $28.39 · 손절초안 $26.26 (−7.5%) · 수량초안 44주 · 포지션 $1,249.16 (13.1%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker SIRI --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers SIRI` → 큐레이션 → `python scripts/decide.py --ticker SIRI --paper`  (첫 8주 페이퍼/반액)

## ⭐ GOOS — Canada Goose Holdings Inc. Subordinate Voting Shares (US) · 점수 82.7 · US 8/15위 · Consumer Cyclical · 낙폭 84% · ATR 3.5%
- 위험공시 라이브 재점검: 통과
- ⚠️ 섹터 중복: MNSO와 동일 섹터(Consumer Cyclical) — 픽은 섹터당 1(점수 상위 우선)
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=GOOS&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=GOOS&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=GOOS%20stock)
- 진입초안 $8.55 · 손절초안 $7.81 (−8.7%) · 수량초안 129주 · 포지션 $1,102.95 (11.5%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker GOOS --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers GOOS` → 큐레이션 → `python scripts/decide.py --ticker GOOS --paper`  (첫 8주 페이퍼/반액)

## AMN — AMN Healthcare Services Inc (US) · 점수 82.5 · US 9/15위 · Healthcare · 낙폭 73% · ATR 5.2%
- 위험공시 라이브 재점검: 통과
- ⚠️ 섹터 중복: NVO와 동일 섹터(Healthcare) — 픽은 섹터당 1(점수 상위 우선)
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=AMN&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=AMN&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=AMN%20stock)
- 진입초안 $34.79 · 손절초안 $30.27 (−13.0%) · 수량초안 21주 · 포지션 $730.59 (7.6%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker AMN --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers AMN` → 큐레이션 → `python scripts/decide.py --ticker AMN --paper`  (첫 8주 페이퍼/반액)

## TBLA — Taboola.com Ltd. - Ordinary Shares (US) · 점수 82.4 · US 10/15위 · Communication Services · 낙폭 63% · ATR 7.2%
- 위험공시 라이브 재점검: 통과
- ⚠️ 섹터 중복: NRDS와 동일 섹터(Communication Services) — 픽은 섹터당 1(점수 상위 우선)
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=TBLA&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=TBLA&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=TBLA%20stock)
- 진입초안 $3.68 · 손절초안 $3.02 (−18.0%) · 수량초안 144주 · 포지션 $529.92 (5.5%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker TBLA --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers TBLA` → 큐레이션 → `python scripts/decide.py --ticker TBLA --paper`  (첫 8주 페이퍼/반액)

## TME — Tencent Music Entertainment Group American Depositary Shares, each representing two Class A Ordinary Shares (US) · 점수 82.4 · US 11/15위 · Communication Services · 낙폭 66% · ATR 4.2%
- 위험공시 라이브 재점검: 통과
- ⚠️ 섹터 중복: NRDS와 동일 섹터(Communication Services) — 픽은 섹터당 1(점수 상위 우선)
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=TME&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=TME&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=TME%20stock)
- 진입초안 $8.85 · 손절초안 $7.93 (−10.4%) · 수량초안 103주 · 포지션 $911.55 (9.5%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker TME --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers TME` → 큐레이션 → `python scripts/decide.py --ticker TME --paper`  (첫 8주 페이퍼/반액)

## BSX — Boston Scientific Corporation Common Stock (US) · 점수 82.0 · US 13/15위 · Healthcare · 낙폭 54% · ATR 3.5%
- 위험공시 라이브 재점검: 통과
- ⚠️ 섹터 중복: NVO와 동일 섹터(Healthcare) — 픽은 섹터당 1(점수 상위 우선)
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=BSX&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=BSX&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=BSX%20stock)
- 진입초안 $49.37 · 손절초안 $45.04 (−8.8%) · 수량초안 22주 · 포지션 $1,086.14 (11.4%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker BSX --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers BSX` → 큐레이션 → `python scripts/decide.py --ticker BSX --paper`  (첫 8주 페이퍼/반액)

## ROKU — Roku, Inc. - Class A Common Stock (US) · 점수 81.8 · US 14/15위 · Communication Services · 낙폭 57% · ATR 1.4%
- 위험공시 라이브 재점검: 통과
- ⚠️ 섹터 중복: NRDS와 동일 섹터(Communication Services) — 픽은 섹터당 1(점수 상위 우선)
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=ROKU&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=ROKU&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=ROKU%20stock)
- 진입초안 $157.12 · 손절초안 $151.68 (−3.5%) · 수량초안 9주 · 포지션 $1,414.08 (14.8%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker ROKU --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers ROKU` → 큐레이션 → `python scripts/decide.py --ticker ROKU --paper`  (첫 8주 페이퍼/반액)

## DV — DoubleVerify Holdings, Inc. Common Stock (US) · 점수 81.3 · US 15/15위 · Communication Services · 낙폭 69% · ATR 2.6%
- 위험공시 라이브 재점검: 통과
- ⚠️ 섹터 중복: NRDS와 동일 섹터(Communication Services) — 픽은 섹터당 1(점수 상위 우선)
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=DV&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=DV&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=DV%20stock)
- 진입초안 $13.31 · 손절초안 $12.46 (−6.4%) · 수량초안 107주 · 포지션 $1,424.17 (14.9%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker DV --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers DV` → 큐레이션 → `python scripts/decide.py --ticker DV --paper`  (첫 8주 페이퍼/반액)

## 게이트 탈락 (사유 기록 — 사후 검증 대상)

- 317450 (KR, 점수 86.2): 펀더 결측 1건(piotroski) — 결측-중립 함정
- 439260 (KR, 점수 80.9): 펀더 결측 1건(piotroski) — 결측-중립 함정
- 259960 (KR, 점수 80.7): 펀더 결측 1건(gross_profit) — 결측-중립 함정
- MKTX (US, 점수 85.7): 펀더 결측 3건(altman_z,piotroski,gross_profit) — 결측-중립 함정
- MCHB (US, 점수 85.6): 펀더 결측 3건(altman_z,piotroski,gross_profit) — 결측-중립 함정
- BZ (US, 점수 84.3): 펀더 결측 1건(altman_z) — 결측-중립 함정
- LOB (US, 점수 82.1): 펀더 결측 2건(altman_z,gross_profit) — 결측-중립 함정

## 다음 단계

- 확정 픽은 **당일~익일 현재가 부근 즉시** 1차 트랜치(50%) — 눌림 대기 금지 [검증]
- 2차 트랜치 +2~4주 시간 기반 [재량] · 캘린더에 2차일·120d 리뷰일 기록
- 관망 탈락도 반드시 decide.py로 기록 — 베토 실효성 검증 데이터
