# 추천 깔때기 체크리스트 — 2026-08-07

> `scripts/recommend.py` 산출. **매수 리스트가 아니다** — 아래 후보를 사람
> 체크(negative screen, 종목당 15분, 베토 주 2건 상한)에 올려 3~5픽으로 좁힌다.
> **⭐ 우선 리서치(시장별 5)부터** — 나머지는 여유 있을 때만.
> 규칙·숫자는 12주 고정 (docs/recommendation-design-2026-07-17.md).

**시세 기준일: 2026-08-05 종가 ⚠️ 2영업일 낡음 — 휴장 또는 스캔 지연 확인 — 진입·손절·수량 초안의 기준. 주문 전 현재가로 재계산**

**계좌 가정: KR ₩10,000,000 · US $10,000 · R 1.0% (내장 기본값 — data/portfolio.json 없음) — 실계좌와 다르면 수량·비중은 예시일 뿐**

**레짐:** KR 200일선↑ 진입가능 +10.4%(기준 2026-08-04) · US 200일선↑ 진입가능 +10.0%(기준 2026-08-04)

**비용 리마인더:** 왕복 KR ≈0.45%(거래세 0.15% + 슬리피지 0.15%×2) · US ≈0.30% + 양도세(슬리피지 0.15%×2 · 이익의 22% 양도세(연 250만 공제) 별도) — 검증 엣지 +1.3~3.8%p/픽의 12~35%가 비용. 2트랜치 분할해도 %비용은 동일(금액 비례).

## ⭐ 259630 — 엠플러스 (KR) · 점수 85.0 · KR 2/15위 · 낙폭 67% · ATR 7.0%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EC%97%A0%ED%94%8C%EB%9F%AC%EC%8A%A4) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EC%97%A0%ED%94%8C%EB%9F%AC%EC%8A%A4) · [네이버금융](https://finance.naver.com/item/main.naver?code=259630)
- 진입초안 9,400원 · 손절초안 7,745원 (−17.6%) · 수량초안 60주 · 포지션 564,000원 (5.6%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 259630 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 259630` → 큐레이션 → `python scripts/decide.py --ticker 259630 --paper`  (첫 8주 페이퍼/반액)

## ⭐ 010780 — 아이에스동서 (KR) · 점수 84.0 · KR 3/15위 · 낙폭 67% · ATR 6.5%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EC%95%84%EC%9D%B4%EC%97%90%EC%8A%A4%EB%8F%99%EC%84%9C) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EC%95%84%EC%9D%B4%EC%97%90%EC%8A%A4%EB%8F%99%EC%84%9C) · [네이버금융](https://finance.naver.com/item/main.naver?code=010780)
- 진입초안 19,510원 · 손절초안 16,339원 (−16.3%) · 수량초안 31주 · 포지션 604,810원 (6.0%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 010780 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 010780` → 큐레이션 → `python scripts/decide.py --ticker 010780 --paper`  (첫 8주 페이퍼/반액)

## ⭐ 002790 — 아모레퍼시픽홀딩스 (KR) · 점수 83.6 · KR 4/15위 · 낙폭 59% · ATR 4.7%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EC%95%84%EB%AA%A8%EB%A0%88%ED%8D%BC%EC%8B%9C%ED%94%BD%ED%99%80%EB%94%A9%EC%8A%A4) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EC%95%84%EB%AA%A8%EB%A0%88%ED%8D%BC%EC%8B%9C%ED%94%BD%ED%99%80%EB%94%A9%EC%8A%A4) · [네이버금융](https://finance.naver.com/item/main.naver?code=002790)
- 진입초안 26,100원 · 손절초안 23,058원 (−11.7%) · 수량초안 32주 · 포지션 835,200원 (8.4%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 002790 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 002790` → 큐레이션 → `python scripts/decide.py --ticker 002790 --paper`  (첫 8주 페이퍼/반액)

## ⭐ 018290 — 브이티 (KR) · 점수 83.2 · KR 5/15위 · 낙폭 70% · ATR 6.1%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EB%B8%8C%EC%9D%B4%ED%8B%B0) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EB%B8%8C%EC%9D%B4%ED%8B%B0) · [네이버금융](https://finance.naver.com/item/main.naver?code=018290)
- 진입초안 13,140원 · 손절초안 11,136원 (−15.3%) · 수량초안 49주 · 포지션 643,860원 (6.4%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 018290 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 018290` → 큐레이션 → `python scripts/decide.py --ticker 018290 --paper`  (첫 8주 페이퍼/반액)

## ⭐ 215200 — 메가스터디교육 (KR) · 점수 83.1 · KR 6/15위 · 낙폭 60% · ATR 4.4%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EB%A9%94%EA%B0%80%EC%8A%A4%ED%84%B0%EB%94%94%EA%B5%90%EC%9C%A1) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EB%A9%94%EA%B0%80%EC%8A%A4%ED%84%B0%EB%94%94%EA%B5%90%EC%9C%A1) · [네이버금융](https://finance.naver.com/item/main.naver?code=215200)
- 진입초안 41,450원 · 손절초안 36,900원 (−11.0%) · 수량초안 21주 · 포지션 870,450원 (8.7%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 215200 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 215200` → 큐레이션 → `python scripts/decide.py --ticker 215200 --paper`  (첫 8주 페이퍼/반액)

## 260970 — 에스앤디 (KR) · 점수 83.0 · KR 7/15위 · 낙폭 63% · ATR 7.2%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EC%97%90%EC%8A%A4%EC%95%A4%EB%94%94) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EC%97%90%EC%8A%A4%EC%95%A4%EB%94%94) · [네이버금융](https://finance.naver.com/item/main.naver?code=260970)
- 진입초안 53,200원 · 손절초안 43,631원 (−18.0%) · 수량초안 10주 · 포지션 532,000원 (5.3%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 260970 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 260970` → 큐레이션 → `python scripts/decide.py --ticker 260970 --paper`  (첫 8주 페이퍼/반액)

## 108670 — LX하우시스 (KR) · 점수 82.5 · KR 8/15위 · 낙폭 69% · ATR 5.1%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=LX%ED%95%98%EC%9A%B0%EC%8B%9C%EC%8A%A4) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=LX%ED%95%98%EC%9A%B0%EC%8B%9C%EC%8A%A4) · [네이버금융](https://finance.naver.com/item/main.naver?code=108670)
- 진입초안 33,900원 · 손절초안 29,590원 (−12.7%) · 수량초안 23주 · 포지션 779,700원 (7.8%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 108670 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 108670` → 큐레이션 → `python scripts/decide.py --ticker 108670 --paper`  (첫 8주 페이퍼/반액)

## 008490 — 서흥 (KR) · 점수 81.6 · KR 9/15위 · 낙폭 60% · ATR 5.4%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EC%84%9C%ED%9D%A5) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EC%84%9C%ED%9D%A5) · [네이버금융](https://finance.naver.com/item/main.naver?code=008490)
- 진입초안 22,100원 · 손절초안 19,133원 (−13.4%) · 수량초안 33주 · 포지션 729,300원 (7.3%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 008490 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 008490` → 큐레이션 → `python scripts/decide.py --ticker 008490 --paper`  (첫 8주 페이퍼/반액)

## 439090 — 마녀공장 (KR) · 점수 81.3 · KR 11/15위 · 낙폭 65% · ATR 6.5%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EB%A7%88%EB%85%80%EA%B3%B5%EC%9E%A5) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EB%A7%88%EB%85%80%EA%B3%B5%EC%9E%A5) · [네이버금융](https://finance.naver.com/item/main.naver?code=439090)
- 진입초안 16,550원 · 손절초안 13,879원 (−16.1%) · 수량초안 37주 · 포지션 612,350원 (6.1%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 439090 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 439090` → 큐레이션 → `python scripts/decide.py --ticker 439090 --paper`  (첫 8주 페이퍼/반액)

## 099430 — 바이오플러스 (KR) · 점수 81.0 · KR 13/15위 · 낙폭 59% · ATR 6.1%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [DART 공시](https://dart.fss.or.kr/dsab007/main.do?option=corp&textCrpNm=%EB%B0%94%EC%9D%B4%EC%98%A4%ED%94%8C%EB%9F%AC%EC%8A%A4) · [네이버뉴스](https://search.naver.com/search.naver?where=news&query=%EB%B0%94%EC%9D%B4%EC%98%A4%ED%94%8C%EB%9F%AC%EC%8A%A4) · [네이버금융](https://finance.naver.com/item/main.naver?code=099430)
- 진입초안 3,660원 · 손절초안 3,098원 (−15.4%) · 수량초안 177주 · 포지션 647,820원 (6.5%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker 099430 --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers 099430` → 큐레이션 → `python scripts/decide.py --ticker 099430 --paper`  (첫 8주 페이퍼/반액)

## ⭐ NVO — Novo Nordisk A/S Common Stock (US) · 점수 90.1 · US 1/15위 · Healthcare · 낙폭 68% · ATR 4.0%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=NVO&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=NVO&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=NVO%20stock)
- 진입초안 $44.53 · 손절초안 $40.13 (−9.9%) · 수량초안 22주 · 포지션 $979.66 (9.8%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker NVO --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers NVO` → 큐레이션 → `python scripts/decide.py --ticker NVO --paper`  (첫 8주 페이퍼/반액)

## ⭐ NRDS — NerdWallet, Inc. - Class A Common Stock (US) · 점수 85.4 · US 3/15위 · Communication Services · 낙폭 68% · ATR 3.8%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=NRDS&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=NRDS&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=NRDS%20stock)
- 진입초안 $9.08 · 손절초안 $8.22 (−9.5%) · 수량초안 115주 · 포지션 $1,044.20 (10.4%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker NRDS --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers NRDS` → 큐레이션 → `python scripts/decide.py --ticker NRDS --paper`  (첫 8주 페이퍼/반액)

## ⭐ MNSO — MINISO Group Holding Limited American Depositary Shares, each representing four Ordinary Shares (US) · 점수 84.5 · US 5/15위 · Consumer Cyclical · 낙폭 55% · ATR 2.9%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=MNSO&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=MNSO&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=MNSO%20stock)
- 진입초안 $12.29 · 손절초안 $11.39 (−7.3%) · 수량초안 111주 · 포지션 $1,364.19 (13.6%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker MNSO --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers MNSO` → 큐레이션 → `python scripts/decide.py --ticker MNSO --paper`  (첫 8주 페이퍼/반액)

## ⭐ TME — Tencent Music Entertainment Group American Depositary Shares, each representing two Class A Ordinary Shares (US) · 점수 84.2 · US 6/15위 · Communication Services · 낙폭 63% · ATR 3.2%
- 위험공시 라이브 재점검: 통과
- ⚠️ 섹터 중복: NRDS와 동일 섹터(Communication Services) — 픽은 섹터당 1(점수 상위 우선)
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=TME&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=TME&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=TME%20stock)
- 진입초안 $9.53 · 손절초안 $8.76 (−8.1%) · 수량초안 130주 · 포지션 $1,238.90 (12.4%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker TME --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers TME` → 큐레이션 → `python scripts/decide.py --ticker TME --paper`  (첫 8주 페이퍼/반액)

## ⭐ ROKU — Roku, Inc. - Class A Common Stock (US) · 점수 83.6 · US 7/15위 · Communication Services · 낙폭 67% · ATR 1.5%
- 위험공시 라이브 재점검: 통과
- ⚠️ 섹터 중복: NRDS와 동일 섹터(Communication Services) — 픽은 섹터당 1(점수 상위 우선)
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=ROKU&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=ROKU&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=ROKU%20stock)
- 진입초안 $146.96 · 손절초안 $141.55 (−3.7%) · 수량초안 10주 · 포지션 $1,469.60 (14.7%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker ROKU --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers ROKU` → 큐레이션 → `python scripts/decide.py --ticker ROKU --paper`  (첫 8주 페이퍼/반액)

## ADMA — ADMA Biologics Inc - Common Stock (US) · 점수 82.8 · US 8/15위 · Healthcare · 낙폭 62% · ATR 3.5%
- 위험공시 라이브 재점검: 통과
- ⚠️ 섹터 중복: NVO와 동일 섹터(Healthcare) — 픽은 섹터당 1(점수 상위 우선)
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=ADMA&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=ADMA&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=ADMA%20stock)
- 진입초안 $9.26 · 손절초안 $8.46 (−8.7%) · 수량초안 124주 · 포지션 $1,148.24 (11.5%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker ADMA --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers ADMA` → 큐레이션 → `python scripts/decide.py --ticker ADMA --paper`  (첫 8주 페이퍼/반액)

## SIRI — SiriusXM Holdings Inc. - Common Stock (US) · 점수 82.8 · US 9/15위 · Communication Services · 낙폭 56% · ATR 3.3%
- 위험공시 라이브 재점검: 통과
- ⚠️ 섹터 중복: NRDS와 동일 섹터(Communication Services) — 픽은 섹터당 1(점수 상위 우선)
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=SIRI&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=SIRI&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=SIRI%20stock)
- 진입초안 $30.70 · 손절초안 $28.17 (−8.2%) · 수량초안 39주 · 포지션 $1,197.30 (12.0%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker SIRI --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers SIRI` → 큐레이션 → `python scripts/decide.py --ticker SIRI --paper`  (첫 8주 페이퍼/반액)

## AMN — AMN Healthcare Services Inc (US) · 점수 82.7 · US 10/15위 · Healthcare · 낙폭 74% · ATR 5.0%
- 위험공시 라이브 재점검: 통과
- ⚠️ 섹터 중복: NVO와 동일 섹터(Healthcare) — 픽은 섹터당 1(점수 상위 우선)
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=AMN&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=AMN&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=AMN%20stock)
- 진입초안 $32.80 · 손절초안 $28.67 (−12.6%) · 수량초안 24주 · 포지션 $787.20 (7.9%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker AMN --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers AMN` → 큐레이션 → `python scripts/decide.py --ticker AMN --paper`  (첫 8주 페이퍼/반액)

## BSX — Boston Scientific Corporation Common Stock (US) · 점수 82.1 · US 12/15위 · Healthcare · 낙폭 56% · ATR 3.7%
- 위험공시 라이브 재점검: 통과
- ⚠️ 섹터 중복: NVO와 동일 섹터(Healthcare) — 픽은 섹터당 1(점수 상위 우선)
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=BSX&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=BSX&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=BSX%20stock)
- 진입초안 $47.74 · 손절초안 $43.29 (−9.3%) · 수량초안 22주 · 포지션 $1,050.28 (10.5%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker BSX --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers BSX` → 큐레이션 → `python scripts/decide.py --ticker BSX --paper`  (첫 8주 페이퍼/반액)

## PAYC — Paycom Software, Inc. Common Stock (US) · 점수 81.9 · US 13/15위 · Technology · 낙폭 68% · ATR 4.5%
- 위험공시 라이브 재점검: 통과
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=PAYC&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=PAYC&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=PAYC%20stock)
- 진입초안 $174.80 · 손절초안 $155.07 (−11.3%) · 수량초안 5주 · 포지션 $874.00 (8.7%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker PAYC --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers PAYC` → 큐레이션 → `python scripts/decide.py --ticker PAYC --paper`  (첫 8주 페이퍼/반액)

## GOOS — Canada Goose Holdings Inc. Subordinate Voting Shares (US) · 점수 81.5 · US 15/15위 · Consumer Cyclical · 낙폭 83% · ATR 4.0%
- 위험공시 라이브 재점검: 통과
- ⚠️ 섹터 중복: MNSO와 동일 섹터(Consumer Cyclical) — 픽은 섹터당 1(점수 상위 우선)
- 조사 링크: [EDGAR 8-K](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=GOOS&type=8-K&count=10) · [EDGAR S-1·424B](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=GOOS&type=424&count=10) · [구글뉴스](https://news.google.com/search?q=GOOS%20stock)
- 진입초안 $8.82 · 손절초안 $7.94 (−9.9%) · 수량초안 114주 · 포지션 $1,005.48 (10.1%, R 1.0%)
- [ ] 낙폭 사유 한 문장 (구조적 소멸형=핵심사업 상실·규제 퇴출·존속위협 소송이면 탈락): 
- [ ] 진행 중 대규모 증자·CB 없음 (KR DART / US EDGAR S-1·424B)
- [ ] 현금+영업CF 18개월 생존 (점수 분해 + 최근 분기보고서)
- [ ] 다음 실적일: ____ — 첫 트랜치가 3일 이내면 실적 후로 이연 [재량]
- [ ] 섹터 중복 없음 (자동 감지 — 위 ⚠️ 섹터 중복 줄 없으면 통과, 미상이면 수동): 
- 탈락 시: `python scripts/decide.py --ticker GOOS --action 관망 --note "<사유>"`
- 채택 시: `python scripts/to_watchlist.py --tickers GOOS` → 큐레이션 → `python scripts/decide.py --ticker GOOS --paper`  (첫 8주 페이퍼/반액)

## 게이트 탈락 (사유 기록 — 사후 검증 대상)

- 317450 (KR, 점수 87.5): 펀더 결측 1건(piotroski) — 결측-중립 함정
- 382800 (KR, 점수 81.5): ATR 8.5% > 8% [재량]
- 036570 (KR, 점수 81.0): 펀더 결측 1건(gross_profit) — 결측-중립 함정
- 020000 (KR, 점수 80.6): ATR 8.7% > 8% [재량]
- 049630 (KR, 점수 80.5): ATR 9.0% > 8% [재량]
- BZ (US, 점수 85.6): 펀더 결측 1건(altman_z) — 결측-중립 함정
- MCHB (US, 점수 85.2): 펀더 결측 3건(altman_z,piotroski,gross_profit) — 결측-중립 함정
- MKTX (US, 점수 82.1): 펀더 결측 3건(altman_z,piotroski,gross_profit) — 결측-중립 함정
- LOB (US, 점수 81.7): 펀더 결측 2건(altman_z,gross_profit) — 결측-중립 함정

## 다음 단계

- 확정 픽은 **당일~익일 현재가 부근 즉시** 1차 트랜치(50%) — 눌림 대기 금지 [검증]
- 2차 트랜치 +2~4주 시간 기반 [재량] · 캘린더에 2차일·120d 리뷰일 기록
- 관망 탈락도 반드시 decide.py로 기록 — 베토 실효성 검증 데이터
