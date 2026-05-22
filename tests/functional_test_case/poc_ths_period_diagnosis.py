"""同花顺分钟线period code诊断脚本

通过分析v6 API元数据和尝试不同period code，
确定同花顺JSONP API的正确分钟线接口参数。
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


def _parse_jsonp(text: str) -> dict[str, Any]:
    m = re.search(r'\((\{.*\})\)', text, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return {}


def analyze_v6_metadata(session: requests.Session) -> None:
    print("=" * 80)
    print("📊 步骤1: 分析v6 API元数据")
    print("=" * 80)

    url = "http://d.10jqka.com.cn/v6/line/hs_600519/01/last.js"
    try:
        resp = session.get(url, headers=_HEADERS, timeout=15)
        data = _parse_jsonp(resp.text)
        print(f"  状态: {resp.status_code}")
        print(f"  顶层键: {list(data.keys())}")
        print(f"  total: {data.get('total')}")
        print(f"  start: {data.get('start')}")
        print(f"  rt: {data.get('rt')}")
        print(f"  num: {data.get('num')}")
        print(f"  name: {data.get('name')}")
        print(f"  marketType: {data.get('marketType')}")

        year_data = data.get("year", {})
        if year_data:
            print(f"\n  年份索引 (共{len(year_data)}年):")
            for year in sorted(year_data.keys()):
                days = year_data[year]
                print(f"    {year}: {days}个交易日")

        raw_data = data.get("data")
        if raw_data:
            if isinstance(raw_data, str):
                lines = [l for l in raw_data.split(";") if l.strip()]
                print(f"\n  data字段: 字符串, {len(lines)}条记录")
                if lines:
                    print(f"    首条: {lines[0][:150]}")
                    print(f"    末条: {lines[-1][:150]}")
            elif isinstance(raw_data, list):
                print(f"\n  data字段: 列表, {len(raw_data)}条记录")
                if raw_data:
                    print(f"    首条: {str(raw_data[0])[:150]}")
            elif isinstance(raw_data, dict):
                print(f"\n  data字段: 字典, 键={list(raw_data.keys())[:10]}")
        else:
            print(f"\n  data字段: {type(raw_data).__name__} = {str(raw_data)[:200]}")

    except Exception as e:
        print(f"  ❌ 请求失败: {type(e).__name__}: {e}")


def test_v6_year_endpoint(session: requests.Session) -> None:
    print("\n" + "=" * 80)
    print("📊 步骤2: 测试v6 API按年获取分钟线")
    print("=" * 80)

    for year in [2024, 2025, 2026]:
        url = f"http://d.10jqka.com.cn/v6/line/hs_600519/01/{year}.js"
        try:
            resp = session.get(url, headers=_HEADERS, timeout=15)
            if resp.status_code == 200:
                data = _parse_jsonp(resp.text)
                raw_data = data.get("data", "")
                if isinstance(raw_data, str) and raw_data:
                    lines = [l for l in raw_data.split(";") if l.strip()]
                    print(f"  ✅ {year}: {len(lines)}条1分钟数据")
                    if lines:
                        print(f"    首条: {lines[0][:120]}")
                        print(f"    末条: {lines[-1][:120]}")
                else:
                    print(f"  ⚠️ {year}: 无data字段 ({str(raw_data)[:100]})")
            else:
                print(f"  ❌ {year}: HTTP {resp.status_code}")
        except Exception as e:
            print(f"  ❌ {year}: {type(e).__name__}: {e}")
        time.sleep(0.5)


def test_v2_period_codes(session: requests.Session) -> None:
    print("\n" + "=" * 80)
    print("📊 步骤3: 暴力测试v2 API所有period code")
    print("=" * 80)

    results: dict[str, dict[str, Any]] = {}

    for code in range(0, 100):
        code_str = f"{code:02d}"
        url = f"http://d.10jqka.com.cn/v2/line/hs_600519/{code_str}/2025.js"
        try:
            resp = session.get(url, headers=_HEADERS, timeout=10)
            if resp.status_code == 200:
                data = _parse_jsonp(resp.text)
                raw_data = data.get("data", "")
                if isinstance(raw_data, str) and raw_data:
                    lines = [l for l in raw_data.split(";") if l.strip()]
                    first_line = lines[0] if lines else ""
                    has_time = bool(re.search(r'\d{8}\d{4}', first_line.split(",")[0]))
                    data_type = "分钟线" if has_time else "日K线"
                    results[code_str] = {
                        "status": 200,
                        "lines": len(lines),
                        "type": data_type,
                        "first": first_line[:100],
                    }
                    icon = "🕐" if has_time else "📅"
                    print(f"  {icon} period={code_str}: {len(lines)}条 {data_type}")
                    print(f"    首条: {first_line[:120]}")
        except Exception:
            pass
        time.sleep(0.15)

    print(f"\n  有效period code汇总: {len(results)}个")
    for code, info in sorted(results.items()):
        print(f"    {code}: {info['type']}, {info['lines']}条")


def test_v6_period_codes(session: requests.Session) -> None:
    print("\n" + "=" * 80)
    print("📊 步骤4: 测试v6 API不同period code")
    print("=" * 80)

    for code in ["01", "05", "15", "30", "60", "11", "21", "31"]:
        url = f"http://d.10jqka.com.cn/v6/line/hs_600519/{code}/last.js"
        try:
            resp = session.get(url, headers=_HEADERS, timeout=10)
            if resp.status_code == 200:
                data = _parse_jsonp(resp.text)
                raw_data = data.get("data", "")
                total = data.get("total", "")
                name = data.get("name", "")
                if isinstance(raw_data, str) and raw_data:
                    lines = [l for l in raw_data.split(";") if l.strip()]
                    first_line = lines[0] if lines else ""
                    has_time = bool(re.search(r'\d{8}\d{4}', first_line.split(",")[0]))
                    data_type = "分钟线" if has_time else "日K线"
                    print(f"  ✅ period={code}: {data_type}, {len(lines)}条, total={total}, name={name}")
                    if lines:
                        print(f"    首条: {first_line[:120]}")
                else:
                    print(f"  ⚠️ period={code}: total={total}, name={name}, data={str(raw_data)[:100]}")
            else:
                print(f"  ❌ period={code}: HTTP {resp.status_code}")
        except Exception as e:
            print(f"  ❌ period={code}: {type(e).__name__}: {e}")
        time.sleep(0.5)


def test_v6_minute_by_year(session: requests.Session) -> None:
    print("\n" + "=" * 80)
    print("📊 步骤5: v6 API 1分钟线按年获取(2020-2026)")
    print("=" * 80)

    for year in range(2020, 2027):
        url = f"http://d.10jqka.com.cn/v6/line/hs_600519/01/{year}.js"
        try:
            resp = session.get(url, headers=_HEADERS, timeout=15)
            if resp.status_code == 200:
                data = _parse_jsonp(resp.text)
                raw_data = data.get("data", "")
                if isinstance(raw_data, str) and raw_data:
                    lines = [l for l in raw_data.split(";") if l.strip()]
                    print(f"  ✅ {year}: {len(lines)}条1分钟数据")
                    if lines:
                        print(f"    首条: {lines[0][:120]}")
                else:
                    print(f"  ⚠️ {year}: 无数据")
            else:
                print(f"  ❌ {year}: HTTP {resp.status_code}")
        except Exception as e:
            print(f"  ❌ {year}: {type(e).__name__}: {e}")
        time.sleep(0.5)


def test_v6_5min_by_year(session: requests.Session) -> None:
    print("\n" + "=" * 80)
    print("📊 步骤6: v6 API 5分钟线按年获取(2020-2026)")
    print("=" * 80)

    for year in range(2020, 2027):
        url = f"http://d.10jqka.com.cn/v6/line/hs_600519/05/{year}.js"
        try:
            resp = session.get(url, headers=_HEADERS, timeout=15)
            if resp.status_code == 200:
                data = _parse_jsonp(resp.text)
                raw_data = data.get("data", "")
                if isinstance(raw_data, str) and raw_data:
                    lines = [l for l in raw_data.split(";") if l.strip()]
                    print(f"  ✅ {year}: {len(lines)}条5分钟数据")
                    if lines:
                        print(f"    首条: {lines[0][:120]}")
                else:
                    print(f"  ⚠️ {year}: 无数据")
            else:
                print(f"  ❌ {year}: HTTP {resp.status_code}")
        except Exception as e:
            print(f"  ❌ {year}: {type(e).__name__}: {e}")
        time.sleep(0.5)


def main() -> None:
    session = requests.Session()

    analyze_v6_metadata(session)
    test_v6_year_endpoint(session)
    test_v2_period_codes(session)
    test_v6_period_codes(session)
    test_v6_minute_by_year(session)
    test_v6_5min_by_year(session)

    print("\n" + "=" * 80)
    print("✅ 同花顺分钟线period code诊断完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
