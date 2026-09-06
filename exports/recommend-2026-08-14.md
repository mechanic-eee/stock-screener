# 추천 깔때기 체크리스트 — 2026-08-14

> `scripts/recommend.py` 산출. **매수 리스트가 아니다** — 아래 후보를 사람
> 체크(negative screen, 종목당 15분, 베토 주 2건 상한)에 올려 3~5픽으로 좁힌다.
> **⭐ 우선 리서치(시장별 5)부터** — 나머지는 여유 있을 때만.
> 규칙·숫자는 12주 고정 (docs/recommendation-design-2026-07-17.md).

**시세 기준일: 2026-08-13 종가 ⚠️ 1영업일 낡음 — 휴장 또는 스캔 지연 확인 — 진입·손절·수량 초안의 기준. 주문 전 현재가로 재계산**

**계좌 가정: KR ₩7,432,431 · US $9,559 · R 1.0% (data/portfolio.json) — 실계좌와 다르면 수량·비중은 예시일 뿐**

**레짐:** KR 200일선↑ 진입가능 +12.6%(기준 2026-08-12) · US 200일선↑ 진입가능 +9.7%(기준 2026-08-12)

**비용 리마인더:** 왕복 KR ≈0.45%(거래세 0.15% + 슬리피지 0.15%×2) · US ≈0.30% + 양도세(슬리피지 0.15%×2 · 이익의 22% 양도세(연 250만 공제) 별도) — 검증 엣지 +1.3~3.8%p/픽의 12~35%가 비용. 2트랜치 분할해도 %비용은 동일(금액 비례).

## ⭐ 259630 — 엠플러스 (KR) · 점수 87.2 · KR 1/15위 · 낙폭 65% · ATR 5.7%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EC%97%A0%ED%94%8C%EB%9F%AC%EC%8A%A4) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EC%97%A0%ED%94%8C%EB%9F%AC%EC%8A%A4) · [네이버금융](https://finance.naver.com/item/main.naver?code=259630)
- 진입초안 10,030원 · 손절초안 8,601원 (−14.2%) · 수량초안 52주 · 포지션 521,560원 (7.0%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 259630 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 259630` → 큐레이션 → `python scripts/decide.py --ticker 259630 --paper`  (첫 8주 페이퍼/반액)

## ⭐ 010780 — 아이에스동서 (KR) · 점수 84.0 · KR 3/15위 · 낙폭 70% · ATR 6.3%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EC%95%84%EC%9D%B4%EC%97%90%EC%8A%A4%EB%8F%99%EC%84%9C) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EC%95%84%EC%9D%B4%EC%97%90%EC%8A%A4%EB%8F%99%EC%84%9C) · [네이버금융](https://finance.naver.com/item/main.naver?code=010780)
- 진입초안 18,000원 · 손절초안 15,169원 (−15.7%) · 수량초안 26주 · 포지션 468,000원 (6.3%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 010780 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 010780` → 큐레이션 → `python scripts/decide.py --ticker 010780 --paper`  (첫 8주 페이퍼/반액)

## ⭐ 215200 — 메가스터디교육 (KR) · 점수 83.8 · KR 4/15위 · 낙폭 64% · ATR 4.9%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EB%A9%94%EA%B0%80%EC%8A%A4%ED%84%B0%EB%94%94%EA%B5%90%EC%9C%A1) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EB%A9%94%EA%B0%80%EC%8A%A4%ED%84%B0%EB%94%94%EA%B5%90%EC%9C%A1) · [네이버금융](https://finance.naver.com/item/main.naver?code=215200)
- 진입초안 37,050원 · 손절초안 32,540원 (−12.2%) · 수량초안 16주 · 포지션 592,800원 (8.0%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 215200 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 215200` → 큐레이션 → `python scripts/decide.py --ticker 215200 --paper`  (첫 8주 페이퍼/반액)

## ⭐ 002790 — 아모레퍼시픽홀딩스 (KR) · 점수 83.5 · KR 5/15위 · 낙폭 58% · ATR 4.5%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EC%95%84%EB%AA%A8%EB%A0%88%ED%8D%BC%EC%8B%9C%ED%94%BD%ED%99%80%EB%94%A9%EC%8A%A4) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EC%95%84%EB%AA%A8%EB%A0%88%ED%8D%BC%EC%8B%9C%ED%94%BD%ED%99%80%EB%94%A9%EC%8A%A4) · [네이버금융](https://finance.naver.com/item/main.naver?code=002790)
- 진입초안 26,200원 · 손절초안 23,225원 (−11.4%) · 수량초안 24주 · 포지션 628,800원 (8.5%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 002790 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 002790` → 큐레이션 → `python scripts/decide.py --ticker 002790 --paper`  (첫 8주 페이퍼/반액)

## ⭐ 108670 — LX하우시스 (KR) · 점수 83.5 · KR 6/15위 · 낙폭 68% · ATR 4.6%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=LX%ED%95%98%EC%9A%B0%EC%8B%9C%EC%8A%A4) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=LX%ED%95%98%EC%9A%B0%EC%8B%9C%EC%8A%A4) · [네이버금융](https://finance.naver.com/item/main.naver?code=108670)
- 진입초안 33,500원 · 손절초안 29,641원 (−11.5%) · 수량초안 19주 · 포지션 636,500원 (8.6%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 108670 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 108670` → 큐레이션 → `python scripts/decide.py --ticker 108670 --paper`  (첫 8주 페이퍼/반액)

## 020000 — 한섬 (KR) · 점수 83.1 · KR 7/15위 · 낙폭 64% · ATR 6.7%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%ED%95%9C%EC%84%AC) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%ED%95%9C%EC%84%AC) · [네이버금융](https://finance.naver.com/item/main.naver?code=020000)
- 진입초안 15,900원 · 손절초안 13,240원 (−16.7%) · 수량초안 27주 · 포지션 429,300원 (5.8%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 020000 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 020000` → 큐레이션 → `python scripts/decide.py --ticker 020000 --paper`  (첫 8주 페이퍼/반액)

## 260970 — 에스앤디 (KR) · 점수 83.0 · KR 8/15위 · 낙폭 61% · ATR 6.6%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EC%97%90%EC%8A%A4%EC%95%A4%EB%94%94) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EC%97%90%EC%8A%A4%EC%95%A4%EB%94%94) · [네이버금융](https://finance.naver.com/item/main.naver?code=260970)
- 진입초안 56,800원 · 손절초안 47,492원 (−16.4%) · 수량초안 7주 · 포지션 397,600원 (5.3%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 260970 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 260970` → 큐레이션 → `python scripts/decide.py --ticker 260970 --paper`  (첫 8주 페이퍼/반액)

## 049630 — 재영솔루텍 (KR) · 점수 82.6 · KR 9/15위 · 낙폭 81% · ATR 7.4%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EC%9E%AC%EC%98%81%EC%86%94%EB%A3%A8%ED%85%8D) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EC%9E%AC%EC%98%81%EC%86%94%EB%A3%A8%ED%85%8D) · [네이버금융](https://finance.naver.com/item/main.naver?code=049630)
- 진입초안 6,950원 · 손절초안 5,667원 (−18.5%) · 수량초안 57주 · 포지션 396,150원 (5.3%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 049630 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 049630` → 큐레이션 → `python scripts/decide.py --ticker 049630 --paper`  (첫 8주 페이퍼/반액)

## 099430 — 바이오플러스 (KR) · 점수 82.3 · KR 10/15위 · 낙폭 59% · ATR 5.4%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EB%B0%94%EC%9D%B4%EC%98%A4%ED%94%8C%EB%9F%AC%EC%8A%A4) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EB%B0%94%EC%9D%B4%EC%98%A4%ED%94%8C%EB%9F%AC%EC%8A%A4) · [네이버금융](https://finance.naver.com/item/main.naver?code=099430)
- 진입초안 3,610원 · 손절초안 3,119원 (−13.6%) · 수량초안 151주 · 포지션 545,110원 (7.3%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 099430 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 099430` → 큐레이션 → `python scripts/decide.py --ticker 099430 --paper`  (첫 8주 페이퍼/반액)

## 051160 — 지어소프트 (KR) · 점수 82.3 · KR 11/15위 · 낙폭 63% · ATR 6.2%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EC%A7%80%EC%96%B4%EC%86%8C%ED%94%84%ED%8A%B8) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EC%A7%80%EC%96%B4%EC%86%8C%ED%94%84%ED%8A%B8) · [네이버금융](https://finance.naver.com/item/main.naver?code=051160)
- 진입초안 10,030원 · 손절초안 8,479원 (−15.5%) · 수량초안 47주 · 포지션 471,410원 (6.3%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 051160 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 051160` → 큐레이션 → `python scripts/decide.py --ticker 051160 --paper`  (첫 8주 페이퍼/반액)

## 383220 — F&F (KR) · 점수 82.1 · KR 12/15위 · 낙폭 65% · ATR 6.4%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=F%26F) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=F%26F) · [네이버금융](https://finance.naver.com/item/main.naver?code=383220)
- 진입초안 68,800원 · 손절초안 57,851원 (−15.9%) · 수량초안 6주 · 포지션 412,800원 (5.6%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 383220 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 383220` → 큐레이션 → `python scripts/decide.py --ticker 383220 --paper`  (첫 8주 페이퍼/반액)

## 018290 — 브이티 (KR) · 점수 81.8 · KR 13/15위 · 낙폭 70% · ATR 6.8%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EB%B8%8C%EC%9D%B4%ED%8B%B0) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EB%B8%8C%EC%9D%B4%ED%8B%B0) · [네이버금융](https://finance.naver.com/item/main.naver?code=018290)
- 진입초안 13,380원 · 손절초안 11,111원 (−17.0%) · 수량초안 32주 · 포지션 428,160원 (5.8%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 018290 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 018290` → 큐레이션 → `python scripts/decide.py --ticker 018290 --paper`  (첫 8주 페이퍼/반액)

## 215000 — 골프존 (KR) · 점수 81.3 · KR 14/15위 · 낙폭 80% · ATR 3.9%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EA%B3%A8%ED%94%84%EC%A1%B4) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EA%B3%A8%ED%94%84%EC%A1%B4) · [네이버금융](https://finance.naver.com/item/main.naver?code=215000)
- 진입초안 36,400원 · 손절초안 32,895원 (−9.6%) · 수량초안 21주 · 포지션 764,400원 (10.3%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 215000 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 215000` → 큐레이션 → `python scripts/decide.py --ticker 215000 --paper`  (첫 8주 페이퍼/반액)

## ⭐ NVO — Novo Nordisk A/S Common Stock (US) · 점수 91.7 · US 1/15위 · Healthcare · 낙폭 66% · ATR 3.4%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=NVO&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=NVO&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=NVO%20stock)
- 진입초안 $46.72 · 손절초안 $42.78 (−8.4%) · 수량초안 24주 · 포지션 $1,121.28 (11.7%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker NVO --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers NVO` → 큐레이션 → `python scripts/decide.py --ticker NVO --paper`  (첫 8주 페이퍼/반액)

## ⭐ MNSO — MINISO Group Holding Limited American Depositary Shares, each representing four Ordinary Shares (US) · 점수 85.4 · US 3/15위 · Consumer Cyclical · 낙폭 57% · ATR 2.8%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=MNSO&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=MNSO&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=MNSO%20stock)
- 진입초안 $11.81 · 손절초안 $10.98 (−7.0%) · 수량초안 115주 · 포지션 $1,358.15 (14.2%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker MNSO --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers MNSO` → 큐레이션 → `python scripts/decide.py --ticker MNSO --paper`  (첫 8주 페이퍼/반액)

## ⭐ NRDS — NerdWallet, Inc. - Class A Common Stock (US) · 점수 84.8 · US 4/15위 · Communication Services · 낙폭 65% · ATR 4.2%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=NRDS&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=NRDS&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=NRDS%20stock)
- 진입초안 $10.00 · 손절초안 $8.96 (−10.4%) · 수량초안 91주 · 포지션 $910.00 (9.5%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker NRDS --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers NRDS` → 큐레이션 → `python scripts/decide.py --ticker NRDS --paper`  (첫 8주 페이퍼/반액)

## ⭐ SIRI — SiriusXM Holdings Inc. - Common Stock (US) · 점수 84.3 · US 5/15위 · Communication Services · 낙폭 59% · ATR 3.3%
- 위험공시 라이브 재점검: 통과
- ⚠️ 섹터 중복: NRDS와 동일 섹터(Communication Services) — 픽은 섹터당 1(점수 상위 우선)
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=SIRI&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=SIRI&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=SIRI%20stock)
- 진입초안 $27.99 · 손절초안 $25.68 (−8.2%) · 수량초안 41주 · 포지션 $1,147.59 (12.0%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker SIRI --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers SIRI` → 큐레이션 → `python scripts/decide.py --ticker SIRI --paper`  (첫 8주 페이퍼/반액)

## ⭐ ROKU — Roku, Inc. - Class A Common Stock (US) · 점수 82.9 · US 8/15위 · Communication Services · 낙폭 61% · ATR 1.4%
- 위험공시 라이브 재점검: 통과
- ⚠️ 섹터 중복: NRDS와 동일 섹터(Communication Services) — 픽은 섹터당 1(점수 상위 우선)
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=ROKU&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=ROKU&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=ROKU%20stock)
- 진입초안 $154.08 · 손절초안 $148.50 (−3.6%) · 수량초안 9주 · 포지션 $1,386.72 (14.5%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker ROKU --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers ROKU` → 큐레이션 → `python scripts/decide.py --ticker ROKU --paper`  (첫 8주 페이퍼/반액)

## GOOS — Canada Goose Holdings Inc. Subordinate Voting Shares (US) · 점수 82.6 · US 9/15위 · Consumer Cyclical · 낙폭 84% · ATR 3.5%
- 위험공시 라이브 재점검: 통과
- ⚠️ 섹터 중복: MNSO와 동일 섹터(Consumer Cyclical) — 픽은 섹터당 1(점수 상위 우선)
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=GOOS&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=GOOS&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=GOOS%20stock)
- 진입초안 $8.70 · 손절초안 $7.94 (−8.8%) · 수량초안 125주 · 포지션 $1,087.50 (11.4%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker GOOS --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers GOOS` → 큐레이션 → `python scripts/decide.py --ticker GOOS --paper`  (첫 8주 페이퍼/반액)

## LXU — LSB Industries, Inc. Common Stock (US) · 점수 82.0 · US 11/15위 · Basic Materials · 낙폭 63% · ATR 4.6%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=LXU&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=LXU&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=LXU%20stock)
- 진입초안 $9.87 · 손절초안 $8.73 (−11.6%) · 수량초안 83주 · 포지션 $819.21 (8.6%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker LXU --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers LXU` → 큐레이션 → `python scripts/decide.py --ticker LXU --paper`  (첫 8주 페이퍼/반액)

## TBLA — Taboola.com Ltd. - Ordinary Shares (US) · 점수 81.7 · US 12/15위 · Communication Services · 낙폭 61% · ATR 7.1%
- 위험공시 라이브 재점검: 통과
- ⚠️ 섹터 중복: NRDS와 동일 섹터(Communication Services) — 픽은 섹터당 1(점수 상위 우선)
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=TBLA&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=TBLA&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=TBLA%20stock)
- 진입초안 $3.94 · 손절초안 $3.24 (−17.7%) · 수량초안 137주 · 포지션 $539.78 (5.6%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker TBLA --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers TBLA` → 큐레이션 → `python scripts/decide.py --ticker TBLA --paper`  (첫 8주 페이퍼/반액)

## YALA — Yalla Group Limited American Depositary Shares, each representing one Class A Ordinary Share (US) · 점수 81.7 · US 13/15위 · Technology · 낙폭 60% · ATR 2.5%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=YALA&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=YALA&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=YALA%20stock)
- 진입초안 $5.42 · 손절초안 $5.09 (−6.2%) · 수량초안 264주 · 포지션 $1,430.88 (15.0%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker YALA --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers YALA` → 큐레이션 → `python scripts/decide.py --ticker YALA --paper`  (첫 8주 페이퍼/반액)

## BSX — Boston Scientific Corporation Common Stock (US) · 점수 81.6 · US 14/15위 · Healthcare · 낙폭 52% · ATR 3.3%
- 위험공시 라이브 재점검: 통과
- ⚠️ 섹터 중복: NVO와 동일 섹터(Healthcare) — 픽은 섹터당 1(점수 상위 우선)
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=BSX&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=BSX&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=BSX%20stock)
- 진입초안 $51.69 · 손절초안 $47.49 (−8.1%) · 수량초안 22주 · 포지션 $1,137.18 (11.9%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker BSX --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers BSX` → 큐레이션 → `python scripts/decide.py --ticker BSX --paper`  (첫 8주 페이퍼/반액)

## TME — Tencent Music Entertainment Group American Depositary Shares, each representing two Class A Ordinary Shares (US) · 점수 81.6 · US 15/15위 · Communication Services · 낙폭 66% · ATR 4.6%
- 위험공시 라이브 재점검: 통과
- ⚠️ 섹터 중복: NRDS와 동일 섹터(Communication Services) — 픽은 섹터당 1(점수 상위 우선)
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=TME&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=TME&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=TME%20stock)
- 진입초안 $8.66 · 손절초안 $7.67 (−11.5%) · 수량초안 96주 · 포지션 $831.36 (8.7%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker TME --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers TME` → 큐레이션 → `python scripts/decide.py --ticker TME --paper`  (첫 8주 페이퍼/반액)

## 게이트 탈락 (사유 기록 — 사후 검증 대상)

- 317450 (KR, 점수 86.4): 펀더 결측 1건(piotroski) — 결측-중립 함정
- 439260 (KR, 점수 80.8): 펀더 결측 1건(piotroski) — 결측-중립 함정
- MKTX (US, 점수 85.8): 펀더 결측 3건(altman_z,piotroski,gross_profit) — 결측-중립 함정
- MCHB (US, 점수 84.2): 펀더 결측 3건(altman_z,piotroski,gross_profit) — 결측-중립 함정
- BZ (US, 점수 84.1): 펀더 결측 1건(altman_z) — 결측-중립 함정
- LOB (US, 점수 82.1): 펀더 결측 2건(altman_z,gross_profit) — 결측-중립 함정

## 다음 단계

- 확정 픽은 **당일~익일 현재가 부근 즉시** 1차 트랜치(50%) — 눌림 대기 금지 [검증]
- 2차 트랜치 +2~4주 시간 기반 [재량] · 캘린더에 2차일·120d 리뷰일 기록
- 관망 탈락도 반드시 decide.py로 기록 — 베토 실효성 검증 데이터
