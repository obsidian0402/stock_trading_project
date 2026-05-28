from dataclasses import dataclass, field


@dataclass
class SignalConfig:
    # ── 필터링 조건 ────────────────────────────────────────────
    # 거래대금 50억 이상: 유동성 확보
    min_trading_value: int = 5_000_000_000

    # 등락률 5~30%: 유의미한 변동성 확보 (상한가 포함)
    min_change_pct: float = 5.0
    max_change_pct: float = 30.0

    # 주가 1,000원 이상: 동전주(작전주 위험) 배제
    min_price: int = 1_000
    max_price: int = 500_000

    # ── 제외 조건 ──────────────────────────────────────────────
    # ETF/스팩 제외: 개별 기업 분석에 부적합한 종목 배제
    exclude_etf: bool = True
    exclude_spac: bool = True
    exclude_preferred: bool = True  # 우선주

    exclude_keywords: list[str] = field(default_factory=lambda: [
        "스팩", "SPAC",
        "ETF", "ETN",
        "리츠",
        "우B", "우C",
        "1우", "2우", "3우",
        "인버스", "레버리지",
    ])

    # ── 차트 분석 조건 ─────────────────────────────────────────
    # 이동평균선 기간 (거래일 단위, 짧은 순 정렬)
    ma_periods: list[int] = field(default_factory=lambda: [5, 10, 20])

    # 연간 고저가 산출 기준 거래일 수 (기본 252 = 약 1년)
    annual_days: int = 252
