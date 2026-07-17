# stock-screener — 폭락주 스크리너 + 검증된 점수 모델

5년 고가 대비 폭락한 종목(KR+US) 중 **회복 가능성 높은 쪽을 점수로 줄 세워** 발굴→결정→사이징→추적→감시까지 잇는 투자 보조 서비스. 점수는 **백테스트로 검증됐다**(2026-06).

> **▶ 먼저 읽기: [`docs/서비스-개요.md`](docs/서비스-개요.md)** — 검증된 진실·사용법·도구지도 한눈에.
> 점수를 *어떻게 믿고 쓰나*: [`docs/점수-활용-가이드.md`](docs/점수-활용-가이드.md) · 일일 운영: [`../stock-investing/워크플로.md`](../stock-investing/워크플로.md)

## 한 줄 요약 (검증으로 확인)
- 폭락주를 *그냥* 사면 동전던지기(승률~40%). **점수는 그 안에서 회복주 vs falling knife를 줄 세우는 랭킹 필터.**
- 엣지 = **저변동성(ATR) + 부도회피(Altman) + 퀄리티(GP·Piotroski·재무)**. 두 시장 高검정력으로 확증(per-date IC t4~7). 가중치는 IC로 보정됨.
- **랭킹엔 펀더 필수**(가격만은 최상위 역전) · **배치는 시장 200일선 위에서** · **바운스 기다리지 마라**. 상세: `docs/score-validation-2026-06-27.md`.

## 닫힌 루프
```
발굴(앱·알림) → recommend.py(주간 깔때기) → 워치리스트 → decide.py(결정+사이징) → track.py(추적) → monitor.py(감시/청산)
```
주간 추천은 `recommend.py`가 랭킹 상위를 하드 게이트(펀더 결측·ATR·부도 이중확인·유동성·위험공시 재점검)로
걸러 사람 체크리스트 후보를 뽑는다 — 설계·검증: `docs/recommendation-design-2026-07-17.md`.

## 스택
- Python 3.x / 순수 pandas 지표(외부 TA 의존성 없음). 시세: FinanceDataReader(KR)·yfinance(US). 펀더: DART(KR)·yfinance/SEC EDGAR(US). 영속화: SQLite. UI: Streamlit. 알림: 텔레그램.
- **클라우드 배포:** GitHub Actions 일일 스캔(평일) → data 브랜치 스냅샷 → Streamlit Cloud 호스팅(라이브 fetch 0). 알림에 점수 상위 + 건강라인(데이터신선도) + 시장레짐(200일선) + 🆕신규.

## 구조
```
app.py                 Streamlit 대시보드 (4그룹 지표 토글·행클릭 점수분해·레짐 배지·모바일 대응)
scan.py                CLI 스캔
scripts/
  daily_scan.py        일일 스캔·알림 (GitHub Actions)
  recommend.py         주간 추천 깔때기 (레짐→하드게이트→체크리스트 후보, exports/)
  to_watchlist.py      후보 → 워치리스트 시드 (ATR 손절 자동초안)
  decide.py            워치리스트행 → 사이징 → DECISIONS (매수/관망/청산, --paper 지원)
  position_size.py     ATR 손절 기반 리스크 사이징
  track.py             시드/포지션 사후 추적 (점수 실효성)
  monitor.py           보유종목 손절이탈·DART위험공시 감시
  daily.ps1            일일 리뷰 원클릭 (track+monitor)
  selftest.py          검증된 가중치·파이프라인 회귀가드
backtest/
  composite_decile_backtest.py  점수 검증 (production 필터를 PIT 슬라이스에 호출)
  edgar_pit.py / dart_pit.py    point-in-time 펀더 (SEC EDGAR / DART)
  weight_experiment.py / fund_weight_experiment.py  가중치 실험
  strategy_backtest.py / regime_analysis.py         기대수익 · 타이밍(200일선)
  fundamental_decompose.py / timing_signals_explore.py  신호 분해 · 타이밍 탐색
  deepen_us_prices.py           US 가격사 딥페치 (검정력 보강)
src/screener/
  models.py indicators.py scoring.py engine.py
  filters/   base(레지스트리) + 지표 필터 1파일씩 (score+weight, IC로 보정됨)
  data/ news/ notify/
docs/                  서비스개요·점수활용가이드·검증리포트·전략·레짐·타이밍 …
```

## 점수 모델 (IC로 보정된 가중치)
- 기본 게이트: 5년 고가 대비 −50%↓ + 유동성 하한. 합성점수 = Σ(가중치×신호점수)/Σ가중치.
- 🟢 강: atr_risk(0.20)·fundamental(0.25)·altman_z(0.18)·piotroski(0.20)·gross_profit(0.10)
- 🟡 약: relative_strength·weekly_macd(0.05)·rsi·bollinger·moving_average(0.05)
- ⚪ 제외(가중0): obv·volume_surge·accruals (예측력 0/음수로 검증됨)
- 검증·근거: `docs/score-validation-2026-06-27.md` (적대적 검증 포함).

## 실행
```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # DART_API_KEY / NewsAPI / 텔레그램 (선택)

python -m streamlit run app.py            # 대시보드
python scripts/selftest.py                # 검증된 설정·파이프라인 점검 (~1s)
pwsh scripts/daily.ps1                    # 일일 리뷰 (track + monitor)
pwsh scripts/register-daily-task.ps1      # 평일 08:10 자동 리뷰 등록 (감시 자동화)

# 점수 검증 재현 (시세·EDGAR/DART 캐시 필요)
python backtest/composite_decile_backtest.py --market KR --fundamentals dart
python backtest/strategy_backtest.py --topn 10
```

## 알려진 한계 / 다음
- **US 생존편향:** 무료 상폐시세 부재 → US 절대수익·레짐·debt신호가 부풀려짐(생존편향 아티팩트 3종). 순위 검증은 두 시장 신뢰, *절대수익·타이밍은 KR(상폐보정) 기준*.
- KR `four_quarters_all_loss`는 US-only(의도) — KR distress는 altman/capital_impairment/DART로 커버(`docs/gap-audit`).
- 감성 사전은 placeholder(KR-FinBERT 교체 여지). 다음 레버: 보유종목 자동감시 스케줄·forward 추적 누적.
