"""同花顺分钟线数据深度验证脚本 (PoC)

重点验证同花顺d.10jqka.com.cn的分钟线JSONP接口，
分析数据格式、历史覆盖范围、数据完整性。
"""

import os

for _proxy_key in [
    "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
    "ALL_PROXY", "all_proxy", "no_proxy", "NO_PROXY",
]:
    os.environ.pop(_proxy_key, None)

import json
import re
import time
from typing import Any

import requests


_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://stockpage.10jqka.com.cn/",
}

_PERIOD_MAP: dict[str, str] = {
    "1min": "01",
    "5min": "05",
    "15min": "15",
    "30min": "30",
    "60min": "60",
    "daily": "11",
    "weekly": "21",
    "monthly": "31",
}

_TEST_STOCKS: list[tuple[str, str, str]] = [
    ("600519", "hs_600519", "贵州茅台"),
    ("000858", "hs_000858", "五粮液"),
    ("603288", "hs_603288", "海天味业"),
    ("000001", "hs_000001", "平安银行"),
]


def _parse_jsonp(text: str) -> dict[str, Any]:
    m = re.search(r'\((\{.*\})\)', text, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return {}


def fetch_minute_data(
    session: requests.Session,
    hs_code: str,
    period: str,
    year: int,
) -> dict[str, Any]:
    period_code = _PERIOD_MAP.get(period, period)
    url = f"http://d.10jqka.com.cn/v2/line/{hs_code}/{period_code}/{year}.js"

    try:
        resp = session.get(url, headers=_HEADERS, timeout=15)
        if resp.status_code != 200:
            return {
                "success": False,
                "url": url,
                "status_code": resp.status_code,
                "error": f"HTTP {resp.status_code}",
            }

        data = _parse_jsonp(resp.text)
        if not data:
            csv_lines = [l for l in resp.text.strip().split(";") if l.strip()]
            if csv_lines:
                return {
                    "success": True,
                    "url": url,
                    "format": "csv",
                    "total_lines": len(csv_lines),
                    "first_line": csv_lines[0][:150] if csv_lines else "",
                    "last_line": csv_lines[-1][:150] if csv_lines else "",
                    "sample": csv_lines[:3],
                }
            return {
                "success": False,
                "url": url,
                "error": "无法解析响应",
                "raw": resp.text[:300],
            }

        return {
            "success": True,
            "url": url,
            "format": "jsonp",
            "data_keys": list(data.keys())[:10],
            "total_lines": _count_data_points(data),
            "sample": json.dumps(data, ensure_ascii=False)[:500],
        }

    except Exception as e:
        return {
            "success": False,
            "url": url,
            "error": f"{type(e).__name__}: {e}",
        }


def _count_data_points(data: dict[str, Any]) -> int:
    if not isinstance(data, dict):
        return 0
    for key in ("data", "klines", "trends", "items"):
        val = data.get(key)
        if isinstance(val, list):
            return len(val)
        if isinstance(val, dict):
            for sub_key in ("diff", "klines", "trends"):
                sub_val = val.get(sub_key)
                if isinstance(sub_val, list):
                    return len(sub_val)
    return 0


def test_minute_line_coverage(session: requests.Session) -> None:
    print("=" * 80)
    print("📊 测试1: 分钟线历史覆盖范围")
    print("=" * 80)

    hs_code = "hs_600519"
    stock_name = "贵州茅台"

    for period_name, period_code in _PERIOD_MAP.items():
        if period_name in ("daily", "weekly", "monthly"):
            continue

        print(f"\n--- {stock_name} {period_name}线 ---")
        for year in range(2020, 2027):
            result = fetch_minute_data(session, hs_code, period_name, year)
            status = "✅" if result.get("success") else "❌"
            lines = result.get("total_lines", 0)
            error = result.get("error", "")
            print(f"  {status} {year}: {lines}条数据" if result.get("success")
                  else f"  {status} {year}: {error}")
            time.sleep(0.5)


def test_minute_line_format(session: requests.Session) -> None:
    print("\n" + "=" * 80)
    print("📊 测试2: 分钟线数据格式解析")
    print("=" * 80)

    hs_code = "hs_600519"
    result = fetch_minute_data(session, hs_code, "5min", 2025)

    if not result.get("success"):
        print(f"  ❌ 获取失败: {result.get('error')}")
        return

    print(f"\n  URL: {result['url']}")
    print(f"  格式: {result.get('format', 'unknown')}")
    print(f"  总行数: {result.get('total_lines', 0)}")

    if result.get("format") == "csv":
        print(f"  首行: {result.get('first_line')}")
        print(f"  末行: {result.get('last_line')}")
        print(f"  样本(前3行):")
        for line in result.get("sample", []):
            print(f"    {line[:120]}")

        # 解析CSV格式
        print("\n  📋 CSV字段解析:")
        first = result.get("first_line", "")
        if first:
            fields = first.split(",")
            print(f"    字段数: {len(fields)}")
            field_names = [
                "日期时间", "开盘价", "最高价", "最低价", "收盘价",
                "成交量", "成交额", "换手率", "字段9", "字段10", "字段11",
            ]
            for i, val in enumerate(fields):
                name = field_names[i] if i < len(field_names) else f"字段{i+1}"
                print(f"    [{i}] {name}: {val}")

    elif result.get("format") == "jsonp":
        print(f"  数据键: {result.get('data_keys')}")
        print(f"  样本: {result.get('sample', '')[:300]}")


def test_multi_stock_minute(session: requests.Session) -> None:
    print("\n" + "=" * 80)
    print("📊 测试3: 多股票分钟线对比")
    print("=" * 80)

    for code, hs_code, name in _TEST_STOCKS:
        result = fetch_minute_data(session, hs_code, "5min", 2025)
        status = "✅" if result.get("success") else "❌"
        lines = result.get("total_lines", 0)
        error = result.get("error", "")
        print(f"  {status} {name}({code}): {lines}条" if result.get("success")
              else f"  {status} {name}({code}): {error}")
        time.sleep(0.5)


def test_realtime_quote(session: requests.Session) -> None:
    print("\n" + "=" * 80)
    print("📊 测试4: 实时行情数据")
    print("=" * 80)

    for code, hs_code, name in _TEST_STOCKS:
        url = f"http://d.10jqka.com.cn/v2/realhead/{hs_code}/last.js"
        try:
            resp = session.get(url, headers=_HEADERS, timeout=15)
            if resp.status_code != 200:
                print(f"  ❌ {name}: HTTP {resp.status_code}")
                continue

            data = _parse_jsonp(resp.text)
            if data:
                keys = list(data.keys())[:15]
                print(f"  ✅ {name}({code}): 字段={keys}")
                # 提取关键价格信息
                for price_key in ["price", "close", "new", "current", "现价"]:
                    val = data.get(price_key)
                    if val:
                        print(f"    {price_key}: {val}")
                        break
            else:
                print(f"  ⚠️ {name}: 响应无法解析 ({resp.text[:100]})")
        except Exception as e:
            print(f"  ❌ {name}: {type(e).__name__}: {e}")

        time.sleep(0.5)


def test_anti_crawl(session: requests.Session) -> None:
    print("\n" + "=" * 80)
    print("📊 测试5: 反爬策略检测")
    print("=" * 80)

    # 测试1: 不带Referer
    print("\n  测试5.1: 不带Referer访问分钟线")
    url = f"http://d.10jqka.com.cn/v2/line/hs_600519/05/2025.js"
    headers_no_referer = {
        "User-Agent": _HEADERS["User-Agent"],
    }
    try:
        resp = session.get(url, headers=headers_no_referer, timeout=15)
        print(f"    状态: {resp.status_code}, 长度: {len(resp.text)}")
    except Exception as e:
        print(f"    ❌ {e}")

    time.sleep(1)

    # 测试2: 不带User-Agent
    print("\n  测试5.2: 不带User-Agent访问分钟线")
    headers_no_ua = {"Referer": _HEADERS["Referer"]}
    try:
        resp = session.get(url, headers=headers_no_ua, timeout=15)
        print(f"    状态: {resp.status_code}, 长度: {len(resp.text)}")
    except Exception as e:
        print(f"    ❌ {e}")

    time.sleep(1)

    # 测试3: 高频请求(连续5次快速请求)
    print("\n  测试5.3: 高频请求测试(5次连续)")
    for i in range(5):
        try:
            resp = session.get(url, headers=_HEADERS, timeout=15)
            print(f"    第{i+1}次: 状态={resp.status_code}, 长度={len(resp.text)}")
        except Exception as e:
            print(f"    第{i+1}次: ❌ {e}")
        time.sleep(0.2)

    # 测试4: 问财接口(已知需hexin-v签名)
    print("\n  测试5.4: 问财接口(无签名)")
    iwencai_url = "http://www.iwencai.com/customized/chart/get-robot-data"
    try:
        resp = session.get(iwencai_url, headers=_HEADERS, timeout=15)
        print(f"    状态: {resp.status_code}")
        print(f"    响应: {resp.text[:200]}")
    except Exception as e:
        print(f"    ❌ {e}")

    time.sleep(1)

    # 测试5: qd.10jqka接口(需认证Token)
    print("\n  测试5.5: qd.10jqka接口(无Token)")
    qd_url = "http://qd.10jqka.com.cn/api/stock/info"
    try:
        resp = session.get(qd_url, headers=_HEADERS, timeout=15)
        print(f"    状态: {resp.status_code}")
        print(f"    响应: {resp.text[:200]}")
    except Exception as e:
        print(f"    ❌ {e}")


def test_v6_api(session: requests.Session) -> None:
    print("\n" + "=" * 80)
    print("📊 测试6: v6版API端点探测")
    print("=" * 80)

    v6_endpoints: list[tuple[str, str]] = [
        ("v6-1分钟线-当日", f"http://d.10jqka.com.cn/v6/line/hs_600519/01/last.js"),
        ("v6-5分钟线-当日", f"http://d.10jqka.com.cn/v6/line/hs_600519/05/last.js"),
        ("v6-分时-当日", f"http://d.10jqka.com.cn/v6/line/hs_600519/11/last.js"),
    ]

    for name, url in v6_endpoints:
        try:
            resp = session.get(url, headers=_HEADERS, timeout=15)
            data = _parse_jsonp(resp.text) if resp.status_code == 200 else {}
            lines = _count_data_points(data)
            status = "✅" if resp.status_code == 200 and lines > 0 else "❌"
            print(f"  {status} {name}: HTTP {resp.status_code}, {lines}条数据")
            if data:
                print(f"    键: {list(data.keys())[:8]}")
        except Exception as e:
            print(f"  ❌ {name}: {type(e).__name__}: {e}")
        time.sleep(0.5)


def main() -> None:
    session = requests.Session()

    test_minute_line_coverage(session)
    test_minute_line_format(session)
    test_multi_stock_minute(session)
    test_realtime_quote(session)
    test_anti_crawl(session)
    test_v6_api(session)

    print("\n" + "=" * 80)
    print("✅ 同花顺分钟线深度验证完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
