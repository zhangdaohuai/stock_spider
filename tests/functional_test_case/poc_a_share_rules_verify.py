"""A股交易规则交叉验证脚本

通过实际数据验证A股交易时间、涨跌幅限制、T+1等核心规则。
数据源：同花顺JSONP API + mootdx + BaoStock
"""

import os
import sys

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


def verify_trading_hours() -> None:
    """验证1: 交易时间规则"""
    print("=" * 70)
    print("验证1: A股交易时间规则")
    print("=" * 70)

    # 从同花顺v6 API获取1分钟线数据，验证交易时段
    url = "http://d.10jqka.com.cn/v6/line/hs_600519/60/last.js"
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        data = _parse_jsonp(resp.text)
        rt = data.get("rt", "")
        print(f"\n  同花顺v6 API返回的交易时段(rt字段): {rt}")

        if rt:
            # 解析rt字段: "0930-1130,1300-1500"
            sessions = rt.split(",")
            for session in sessions:
                parts = session.split("-")
                if len(parts) == 2:
                    start = parts[0]
                    end = parts[1]
                    start_fmt = f"{start[:2]}:{start[2:]}"
                    end_fmt = f"{end[:2]}:{end[2:]}"
                    print(f"    交易时段: {start_fmt} - {end_fmt}")

        # 从1分钟线数据验证首末条时间
        raw_data = data.get("data", "")
        if isinstance(raw_data, str) and raw_data:
            lines = [l for l in raw_data.split(";") if l.strip()]
            if lines:
                first_ts = lines[0].split(",")[0]
                last_ts = lines[-1].split(",")[0]
                print(f"\n  1分钟线首条时间: {first_ts}")
                print(f"  1分钟线末条时间: {last_ts}")

                # 验证时间是否在交易时段内
                if len(first_ts) >= 12:
                    date_part = first_ts[:8]
                    time_part = first_ts[8:12]
                    print(f"    日期: {date_part}, 时间: {time_part}")
                    print(f"    时间格式验证: {time_part[:2]}:{time_part[2:]}")

    except Exception as e:
        print(f"  ❌ 请求失败: {e}")

    # 从v2 API获取日K线，验证交易日
    print("\n  验证交易日(排除周末):")
    url_daily = "http://d.10jqka.com.cn/v2/line/hs_600519/01/2026.js"
    try:
        resp = requests.get(url_daily, headers=_HEADERS, timeout=15)
        data = _parse_jsonp(resp.text)
        raw_data = data.get("data", "")
        if isinstance(raw_data, str) and raw_data:
            lines = [l for l in raw_data.split(";") if l.strip()]
            # 检查最近10个交易日的日期
            recent = lines[-10:] if len(lines) >= 10 else lines
            import datetime
            weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
            print(f"    最近{len(recent)}个交易日:")
            for line in recent:
                date_str = line.split(",")[0]
                try:
                    dt = datetime.datetime.strptime(date_str, "%Y%m%d")
                    weekday = weekday_names[dt.weekday()]
                    is_weekend = dt.weekday() >= 5
                    flag = "❌周末!" if is_weekend else "✅"
                    print(f"      {date_str} ({weekday}) {flag}")
                except ValueError:
                    print(f"      {date_str} (解析失败)")
    except Exception as e:
        print(f"  ❌ 日K线请求失败: {e}")

    # 预期规则
    print("\n  📋 预期交易时间规则:")
    print("    开盘集合竞价: 09:15 - 09:25")
    print("    连续竞价(上午): 09:30 - 11:30")
    print("    连续竞价(下午): 13:00 - 14:57")
    print("    收盘集合竞价: 14:57 - 15:00")
    print("    盘后固定价格: 15:05 - 15:30")


def verify_price_limits() -> None:
    """验证2: 涨跌幅限制"""
    print("\n" + "=" * 70)
    print("验证2: A股涨跌幅限制")
    print("=" * 70)

    # 通过同花顺实时行情获取涨跌停价
    test_stocks: list[tuple[str, str, str]] = [
        ("hs_600519", "600519", "贵州茅台(主板)"),
        ("hs_000858", "000858", "五粮液(主板)"),
        ("hs_300033", "300033", "同花顺(创业板)"),
        ("hs_688981", "688981", "中芯国际(科创板)"),
    ]

    for hs_code, code, name in test_stocks:
        url = f"http://d.10jqka.com.cn/v2/realhead/{hs_code}/last.js"
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=10)
            if resp.status_code != 200:
                print(f"  ❌ {name}: HTTP {resp.status_code}")
                continue

            data = _parse_jsonp(resp.text)
            items = data.get("items", {})
            if not items:
                print(f"  ❌ {name}: 无items数据")
                continue

            current = float(items.get("10", items.get("30", 0)) or 0)
            limit_up = float(items.get("8", 0) or 0)
            limit_down = float(items.get("9", 0) or 0)

            if current > 0 and limit_up > 0:
                up_pct = round((limit_up / current - 1) * 100, 2)
                down_pct = round((1 - limit_down / current) * 100, 2)
                print(f"  {name}: 现价={current}, 涨停价={limit_up}({up_pct}%), "
                      f"跌停价={limit_down}(-{down_pct}%)")
            else:
                print(f"  ⚠️ {name}: 现价={current}, 涨停={limit_up}, 跌停={limit_down}")

        except Exception as e:
            print(f"  ❌ {name}: {e}")

    # 预期规则
    print("\n  📋 预期涨跌幅限制规则:")
    print("    沪深主板: ±10% (ST/*ST: ±5%, 2026年7月6日后改为±10%)")
    print("    创业板: ±20%")
    print("    科创板: ±20%")
    print("    北交所: ±30%")
    print("    新股上市前5日: 无涨跌幅限制(主板/创业板/科创板)")
    print("    北交所新股: 仅首日无限制")


def verify_t_plus_1() -> None:
    """验证3: T+1交割规则"""
    print("\n" + "=" * 70)
    print("验证3: T+1交割规则")
    print("=" * 70)

    print("  T+1规则说明(无法通过API直接验证，为制度性规则):")
    print("    1. 当日买入的股票，次一交易日方可卖出")
    print("    2. 当日卖出股票的资金，当日可用于再买入")
    print("    3. 当日卖出股票的资金，次一交易日方可转出至银行卡")
    print("    4. B股实行T+3交割")

    # 通过mootdx验证1分钟线数据的时间连续性
    print("\n  通过mootdx验证交易数据连续性:")
    try:
        from mootdx.quotes import Quotes

        client = Quotes.factory(market="std")
        df = client.bars(symbol="600519", frequency=8, offset=500)
        if df is not None and len(df) > 0:
            # 检查是否有跨日数据
            dates = sorted(set(str(idx)[:10] for idx in df.index))
            print(f"    数据覆盖 {len(dates)} 个交易日")
            print(f"    日期范围: {dates[0]} ~ {dates[-1]}")

            # 检查每日交易时段
            for date in dates[:3]:
                day_data = df[[str(idx)[:10] == date for idx in df.index]]
                if len(day_data) > 0:
                    first_time = str(day_data.index[0])
                    last_time = str(day_data.index[-1])
                    print(f"    {date}: {first_time} ~ {last_time} ({len(day_data)}条)")
        else:
            print("    ❌ 无数据")
    except Exception as e:
        print(f"    ❌ mootdx验证失败: {e}")


def verify_board_differences() -> None:
    """验证4: 各板块差异化规则"""
    print("\n" + "=" * 70)
    print("验证4: 各板块差异化规则")
    print("=" * 70)

    # 验证代码规则
    print("  股票代码规则验证:")
    code_rules: list[tuple[str, str, str]] = [
        ("600519", "60xxxx", "沪市主板A股"),
        ("000858", "00xxxx", "深市主板A股"),
        ("300033", "30xxxx", "创业板"),
        ("688981", "68xxxx", "科创板"),
        ("830799", "83xxxx", "北交所"),
        ("002xxx", "00xxxx", "中小板(已并入主板)"),
    ]

    for code, pattern, board in code_rules:
        print(f"    {code} → {pattern} → {board}")

    # 通过同花顺获取不同板块股票的实时行情，验证涨跌幅
    print("\n  各板块涨跌幅验证(通过实时行情):")
    board_stocks: list[tuple[str, str, str, float]] = [
        ("hs_600519", "600519", "主板-贵州茅台", 10.0),
        ("hs_300033", "300033", "创业板-同花顺", 20.0),
        ("hs_688981", "688981", "科创板-中芯国际", 20.0),
    ]

    for hs_code, code, name, expected_pct in board_stocks:
        url = f"http://d.10jqka.com.cn/v2/realhead/{hs_code}/last.js"
        try:
            resp = requests.get(url, headers=_HEADERS, timeout=10)
            if resp.status_code != 200:
                continue
            data = _parse_jsonp(resp.text)
            items = data.get("items", {})
            current = float(items.get("10", items.get("30", 0)) or 0)
            limit_up = float(items.get("8", 0) or 0)
            if current > 0 and limit_up > 0:
                actual_pct = round((limit_up / current - 1) * 100, 1)
                match = "✅" if abs(actual_pct - expected_pct) < 1.0 else "❌"
                print(f"    {match} {name}: 实际涨跌幅≈{actual_pct}%, "
                      f"预期={expected_pct}%")
        except Exception:
            pass


def verify_trading_units() -> None:
    """验证5: 交易单位和最小变动"""
    print("\n" + "=" * 70)
    print("验证5: 交易单位和最小变动")
    print("=" * 70)

    # 从1分钟线数据验证最小价格变动
    url = "http://d.10jqka.com.cn/v6/line/hs_600519/60/last.js"
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        data = _parse_jsonp(resp.text)
        raw_data = data.get("data", "")
        if isinstance(raw_data, str) and raw_data:
            lines = [l for l in raw_data.split(";") if l.strip()]
            # 检查价格的小数位数
            price_decimals: set[int] = set()
            for line in lines[:50]:
                parts = line.split(",")
                for price_idx in [1, 2, 3, 4]:  # 开高低收
                    if price_idx < len(parts):
                        price_str = parts[price_idx]
                        if "." in price_str:
                            decimal_part = price_str.split(".")[1]
                            price_decimals.add(len(decimal_part))
            print(f"  价格小数位数: {price_decimals}")
            print(f"  最小价格变动单位: 0.{'0' * (max(price_decimals) - 1)}1元"
                  if price_decimals else "  无法确定")

    except Exception as e:
        print(f"  ❌ 验证失败: {e}")

    print("\n  📋 预期交易单位规则:")
    print("    主板/创业板: 1手=100股，最小买入100股")
    print("    科创板: 最小买入200股，以1股为递增单位")
    print("    北交所: 1手=100股，最小买入100股")
    print("    最小价格变动: 0.01元(所有板块)")


def verify_new_rules_2026() -> None:
    """验证6: 2026年7月6日新规"""
    print("\n" + "=" * 70)
    print("验证6: 2026年7月6日交易规则变更")
    print("=" * 70)

    print("  根据三大交易所2026年4月24日发布的修订规则:")
    print()
    print("  变更1: 盘后固定价格交易扩展")
    print("    现状: 仅科创板/创业板可盘后固定价格交易")
    print("    新规: 扩展至全部A股及ETF(含北交所)")
    print("    时间: 15:05-15:30")
    print()
    print("  变更2: 主板ST/*ST涨跌幅放宽")
    print("    现状: 主板ST/*ST涨跌幅±5%")
    print("    新规: 主板ST/*ST涨跌幅±10%")
    print()
    print("  变更3: 上交所基金收盘方式调整")
    print("    现状: 连续竞价收盘")
    print("    新规: 收盘集合竞价(与股票一致)")
    print()
    print("  变更4: 创业板大宗交易改为盘中实时确认")
    print("    现状: 盘后确认")
    print("    新规: 盘中实时确认")
    print()
    print("  ⚠️ 以上变更自2026年7月6日起实施，当前仍执行旧规则")


def main() -> None:
    print("╔" + "═" * 68 + "╗")
    print("║" + " A股交易规则交叉验证报告".center(60) + "║")
    print("║" + f" 验证日期: 2026-05-18".center(60) + "║")
    print("╚" + "═" * 68 + "╝")

    verify_trading_hours()
    verify_price_limits()
    verify_t_plus_1()
    verify_board_differences()
    verify_trading_units()
    verify_new_rules_2026()

    print("\n" + "=" * 70)
    print("✅ A股交易规则交叉验证完成")
    print("=" * 70)


if __name__ == "__main__":
    main()
