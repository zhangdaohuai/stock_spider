"""A股涨跌幅限制精确验证脚本

通过日K线获取前日收盘价，计算预期涨跌停价，
与实时行情中的涨跌停价对比验证。
"""

import os

for _proxy_key in [
    "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
    "ALL_PROXY", "all_proxy",
]:
    os.environ.pop(_proxy_key, None)

import json
import re
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


def get_prev_close(hs_code: str) -> float:
    """从日K线获取前日收盘价"""
    url = f"http://d.10jqka.com.cn/v2/line/{hs_code}/01/2026.js"
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        data = _parse_jsonp(resp.text)
        raw_data = data.get("data", "")
        if isinstance(raw_data, str) and raw_data:
            lines = [l for l in raw_data.split(";") if l.strip()]
            if lines:
                last_line = lines[-1]
                parts = last_line.split(",")
                if len(parts) >= 5:
                    return float(parts[4])
    except Exception:
        pass
    return 0.0


def get_realtime_items(hs_code: str) -> dict[str, str]:
    """获取实时行情items"""
    url = f"http://d.10jqka.com.cn/v2/realhead/{hs_code}/last.js"
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=10)
        if resp.status_code == 200:
            data = _parse_jsonp(resp.text)
            return data.get("items", {})
    except Exception:
        pass
    return {}


def calc_limit_price(prev_close: float, limit_pct: float) -> tuple[float, float]:
    """根据前日收盘价和涨跌幅限制计算涨跌停价"""
    limit_up = round(prev_close * (1 + limit_pct / 100), 2)
    limit_down = round(prev_close * (1 - limit_pct / 100), 2)
    return limit_up, limit_down


def main() -> None:
    print("=" * 70)
    print("A股涨跌幅限制精确验证")
    print("=" * 70)

    # 测试股票: (hs_code, code, name, expected_limit_pct)
    test_stocks: list[tuple[str, str, str, float]] = [
        ("hs_600519", "600519", "贵州茅台(主板)", 10.0),
        ("hs_000858", "000858", "五粮液(主板)", 10.0),
        ("hs_603288", "603288", "海天味业(主板)", 10.0),
        ("hs_300033", "300033", "同花顺(创业板)", 20.0),
        ("hs_300750", "300750", "宁德时代(创业板)", 20.0),
        ("hs_688981", "688981", "中芯国际(科创板)", 20.0),
    ]

    for hs_code, code, name, expected_pct in test_stocks:
        print(f"\n--- {name} ---")

        # 获取前日收盘价
        prev_close = get_prev_close(hs_code)
        if prev_close <= 0:
            print(f"  ❌ 无法获取前日收盘价")
            continue
        print(f"  前日收盘价(后复权): {prev_close}")

        # 计算预期涨跌停价
        expected_up, expected_down = calc_limit_price(prev_close, expected_pct)
        print(f"  预期涨停价(±{expected_pct}%): {expected_up}")
        print(f"  预期跌停价(±{expected_pct}%): {expected_down}")

        # 获取实时行情
        items = get_realtime_items(hs_code)
        if not items:
            print(f"  ❌ 无法获取实时行情")
            continue

        # 打印所有items字段用于分析
        print(f"  实时行情items关键字段:")
        for key in sorted(items.keys(), key=lambda x: int(x) if x.isdigit() else 999):
            val = items[key]
            if val and val != "0" and val != "0.00" and val != "":
                try:
                    num_val = float(val)
                    if num_val > 0:
                        print(f"    items[{key}] = {val}")
                except ValueError:
                    pass

        # 尝试匹配涨跌停价
        # 从items中找到接近预期涨停价和跌停价的字段
        print(f"\n  涨跌停价匹配:")
        for key, val in items.items():
            try:
                num_val = float(val)
                if num_val <= 0:
                    continue
                # 检查是否接近涨停价
                if abs(num_val - expected_up) < 0.1:
                    print(f"    ✅ items[{key}]={val} ≈ 预期涨停价{expected_up}")
                # 检查是否接近跌停价
                if abs(num_val - expected_down) < 0.1:
                    print(f"    ✅ items[{key}]={val} ≈ 预期跌停价{expected_down}")
            except (ValueError, TypeError):
                pass

    # 特别验证: ST股票
    print("\n" + "=" * 70)
    print("ST股票涨跌幅验证(±5%)")
    print("=" * 70)

    # 查找ST股票 - 使用pywencai
    try:
        import pywencai
        result = pywencai.get(query="ST股票 涨跌幅", loop=False)
        if result is not None and len(result) > 0:
            print(f"  找到 {len(result)} 只ST股票")
            st_codes = result["股票代码"].head(3).tolist()
            print(f"  前3只: {st_codes}")

            for code_str in st_codes:
                # 转换代码格式
                code = code_str.split(".")[0]
                if code.startswith("6"):
                    hs_code = f"hs_{code}"
                else:
                    hs_code = f"hs_{code}"

                prev_close = get_prev_close(hs_code)
                if prev_close > 0:
                    expected_up, expected_down = calc_limit_price(prev_close, 5.0)
                    print(f"\n  ST股票 {code}: 前收={prev_close}")
                    print(f"    预期涨停价(±5%): {expected_up}")
                    print(f"    预期跌停价(±5%): {expected_down}")

                    items = get_realtime_items(hs_code)
                    for key, val in items.items():
                        try:
                            num_val = float(val)
                            if abs(num_val - expected_up) < 0.05:
                                print(f"    ✅ items[{key}]={val} ≈ 涨停价{expected_up}")
                            if abs(num_val - expected_down) < 0.05:
                                print(f"    ✅ items[{key}]={val} ≈ 跌停价{expected_down}")
                        except (ValueError, TypeError):
                            pass
    except Exception as e:
        print(f"  ⚠️ ST股票验证跳过: {e}")

    print("\n" + "=" * 70)
    print("✅ 涨跌幅限制验证完成")
    print("=" * 70)


if __name__ == "__main__":
    main()
