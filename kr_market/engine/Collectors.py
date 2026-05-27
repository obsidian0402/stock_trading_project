import re
import requests
from bs4 import BeautifulSoup

from engine.config import SignalConfig


NAVER_RISE_URL = "https://finance.naver.com/sise/sise_rise.naver"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://finance.naver.com/",
}


def _to_int(text: str) -> int:
    return int(text.replace(",", "").strip())


def _to_float_rate(text: str) -> float:
    return float(text.replace("+", "").replace("%", "").replace(",", "").strip())


def _extract_code(href: str) -> str:
    match = re.search(r"code=(\d{6})", href)
    if match:
        return match.group(1)
    return href.split("code=")[-1][:6]


def _apply_filters(stocks: list[dict], config: SignalConfig) -> tuple[list[dict], dict]:
    before = len(stocks)
    filtered = []

    for s in stocks:
        name = s["name"]

        # 1. 제외 키워드 포함 종목
        if any(kw in name for kw in config.exclude_keywords):
            continue

        # 2. 우선주 — 종목명이 "우"로 끝나는 경우
        if config.exclude_preferred and name.endswith("우"):
            continue

        # 3. 가격 범위 밖
        if not (config.min_price <= s["price"] <= config.max_price):
            continue

        # 4. 등락률 범위 밖
        if not (config.min_change_pct <= s["change_rate"] <= config.max_change_pct):
            continue

        # 5. 거래대금 미달 (amount 단위: 백만원, min_trading_value 단위: 원)
        if s["amount"] * 1_000_000 < config.min_trading_value:
            continue

        filtered.append(s)

    after = len(filtered)
    print(f"[필터] {before}개 → {after}개 ({before - after}개 제외)")
    return filtered, {"before": before, "after": after}


def get_top_gainers(
    market: str, config: SignalConfig | None = None
) -> tuple[list[dict], dict]:
    market = market.upper()
    if market == "KOSPI":
        sosok = 0
    elif market == "KOSDAQ":
        sosok = 1
    else:
        raise ValueError(f"market must be 'KOSPI' or 'KOSDAQ', got {market!r}")

    try:
        response = requests.get(
            NAVER_RISE_URL,
            params={"sosok": sosok},
            headers=HEADERS,
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"네이버 금융 요청 실패: {e}") from e

    if response.apparent_encoding and response.apparent_encoding.lower() in ("euc-kr", "cp949"):
        response.encoding = response.apparent_encoding
    else:
        response.encoding = "euc-kr"

    try:
        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.select_one("table.type_2")
        if table is None:
            raise RuntimeError("상승 종목 테이블을 찾을 수 없습니다.")

        results: list[dict] = []
        for tr in table.select("tr"):
            tds = tr.find_all("td")
            if len(tds) < 7:
                continue

            name_tag = tr.select_one("a.tltle")
            if name_tag is None:
                continue

            name = name_tag.get_text(strip=True)
            href = name_tag.get("href", "")
            code = _extract_code(href)
            if not code or len(code) != 6:
                continue

            try:
                price = _to_int(tds[2].get_text())
                change_rate = _to_float_rate(tds[4].get_text())
                volume = _to_int(tds[5].get_text())
                amount = _to_int(tds[6].get_text())
            except (ValueError, IndexError):
                continue

            results.append(
                {
                    "name": name,
                    "code": code,
                    "price": price,
                    "change_rate": change_rate,
                    "volume": volume,
                    "amount": amount,
                }
            )

        if config is None:
            return results, {"before": len(results), "after": len(results)}

        return _apply_filters(results, config)

    except Exception as e:
        raise RuntimeError(f"파싱 실패: {e}") from e


if __name__ == "__main__":
    kospi, _ = get_top_gainers("KOSPI")
    kosdaq, _ = get_top_gainers("KOSDAQ")

    for item in kospi:
        item["market"] = "KOSPI"
    for item in kosdaq:
        item["market"] = "KOSDAQ"

    combined = kospi + kosdaq
    combined.sort(key=lambda x: x["change_rate"], reverse=True)

    print("=== KOSPI + KOSDAQ 상승률 상위 35개 ===")
    print(f"{'순위':>3}  {'시장':<6} {'코드':<6} {'종목명':<16} {'현재가':>10} {'등락률':>8} {'거래량':>14} {'거래대금':>16}")
    for i, item in enumerate(combined[:35], start=1):
        print(
            f"{i:>3}  {item['market']:<6} {item['code']:<6} {item['name']:<16} "
            f"{item['price']:>10,} {item['change_rate']:>7.2f}% "
            f"{item['volume']:>14,} {item['amount']:>16,}"
        )
