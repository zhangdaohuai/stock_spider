"""TickFlow API 全量验证脚本

验证 https://docs.tickflow.org 的所有核心API接口，
重点关注历史分钟K线数据的获取能力和数据深度。
"""

import os

for _proxy_key in [
    "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
    "ALL_PROXY", "all_proxy",
]:
    os.environ.pop(_proxy_key, None)

import json
import time
from datetime import datetime, timedelta, timezone

import requests

API_KEY = "tk_1c0550b2bbab440b9001123daf680e1e"
BASE_URL = "https://api.tickflow.org"
FREE_URL = "https://free-api.tickflow.org"

_HEADERS = {"x-api-key": API_KEY}

# 主板测试股票: TickFlow格式 代码.市场后缀
_TEST_SYMBOLS = [
    ("600519.SH", "贵州茅台"),
    ("000858.SZ", "五粮液"),
    ("603288.SH", "海天味业"),
    ("000001.SZ", "平安银行"),
]


def _ts_ms(dt_str: str) -> int:
    return int(datetime.strptime(dt_str, "%Y-%m-%d").replace(
        tzinfo=timezone(timedelta(hours=8))
    ).timestamp() * 1000)


def _ms_to_dt(ms: int) -> str:
    return datetime.fromtimestamp(
        ms / 1000, tz=timezone(timedelta(hours=8))
    ).strftime("%Y-%m-%d %H:%M:%S")


def _get(base: str, path: str, params: dict | None = None,
         use_key: bool = True) -> dict:
    headers = _HEADERS if use_key else {}
    session = requests.Session()
    session.trust_env = False
    try:
        resp = session.get(f"{base}{path}", params=params,
                           headers=headers, timeout=30)
        return resp.json()
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


def test_kline_1m_depth() -> None:
    print("=" * 70)
    print("测试1: 1分钟K线历史深度探测")
    print("=" * 70)

    symbol, name = "600519.SH", "贵州茅台"

    # 默认100条
    data = _get(BASE_URL, "/v1/klines", {
        "symbol": symbol, "period": "1m", "count": 100,
    })
    if "data" in data:
        d = data["data"]
        n = len(d.get("timestamp", []))
        if n > 0:
            first = _ms_to_dt(d["timestamp"][0])
            last = _ms_to_dt(d["timestamp"][-1])
            print(f"  ✅ 1m默认100条: {n}条, {first} ~ {last}")
        else:
            print(f"  ❌ 1m默认: 无数据")
    else:
        print(f"  ❌ 1m默认: {data}")

    # 最大10000条
    data = _get(BASE_URL, "/v1/klines", {
        "symbol": symbol, "period": "1m", "count": 10000,
    })
    if "data" in data:
        d = data["data"]
        n = len(d.get("timestamp", []))
        if n > 0:
            first = _ms_to_dt(d["timestamp"][0])
            last = _ms_to_dt(d["timestamp"][-1])
            print(f"  ✅ 1m最大10000条: {n}条, {first} ~ {last}")

            # 按日统计
            dates: dict[str, int] = {}
            for ts in d["timestamp"]:
                dt_str = _ms_to_dt(ts)[:10]
                dates[dt_str] = dates.get(dt_str, 0) + 1
            print(f"  覆盖天数: {len(dates)}")
            for dt in sorted(dates.keys())[:3]:
                print(f"    {dt}: {dates[dt]}条")
            if len(dates) > 6:
                print(f"    ...")
            for dt in sorted(dates.keys())[-3:]:
                print(f"    {dt}: {dates[dt]}条")
        else:
            print(f"  ❌ 1m最大: 无数据")
    else:
        print(f"  ❌ 1m最大: {data}")


def test_kline_5m_depth() -> None:
    print("\n" + "=" * 70)
    print("测试2: 5分钟K线历史深度探测")
    print("=" * 70)

    symbol, name = "600519.SH", "贵州茅台"

    data = _get(BASE_URL, "/v1/klines", {
        "symbol": symbol, "period": "5m", "count": 10000,
    })
    if "data" in data:
        d = data["data"]
        n = len(d.get("timestamp", []))
        if n > 0:
            first = _ms_to_dt(d["timestamp"][0])
            last = _ms_to_dt(d["timestamp"][-1])
            print(f"  ✅ 5m最大10000条: {n}条, {first} ~ {last}")

            dates: dict[str, int] = {}
            for ts in d["timestamp"]:
                dt_str = _ms_to_dt(ts)[:10]
                dates[dt_str] = dates.get(dt_str, 0) + 1
            print(f"  覆盖天数: {len(dates)}")
            for dt in sorted(dates.keys())[:3]:
                print(f"    {dt}: {dates[dt]}条")
            if len(dates) > 6:
                print(f"    ...")
            for dt in sorted(dates.keys())[-3:]:
                print(f"    {dt}: {dates[dt]}条")
        else:
            print(f"  ❌ 5m: 无数据")
    else:
        print(f"  ❌ 5m: {data}")


def test_kline_all_periods() -> None:
    print("\n" + "=" * 70)
    print("测试3: 所有K线周期可用性")
    print("=" * 70)

    symbol, name = "600519.SH", "贵州茅台"

    for period in ["1m", "5m", "10m", "15m", "30m", "60m",
                   "1d", "1w", "1M", "1Q", "1Y"]:
        data = _get(BASE_URL, "/v1/klines", {
            "symbol": symbol, "period": period, "count": 10,
        })
        if "data" in data:
            d = data["data"]
            n = len(d.get("timestamp", []))
            if n > 0:
                first = _ms_to_dt(d["timestamp"][0])[:19]
                last = _ms_to_dt(d["timestamp"][-1])[:19]
                print(f"  ✅ {period:4s}: {n}条, {first} ~ {last}")
            else:
                print(f"  ❌ {period:4s}: 无数据")
        else:
            err = data.get("error", data.get("message", str(data)))
            print(f"  ❌ {period:4s}: {err}")
        time.sleep(0.3)


def test_kline_time_range() -> None:
    print("\n" + "=" * 70)
    print("测试4: 指定时间范围获取K线")
    print("=" * 70)

    symbol, name = "600519.SH", "贵州茅台"

    # 2020年1月1分钟K线
    data = _get(BASE_URL, "/v1/klines", {
        "symbol": symbol, "period": "1m",
        "start_time": _ts_ms("2020-01-02"),
        "end_time": _ts_ms("2020-01-31"),
    })
    if "data" in data:
        d = data["data"]
        n = len(d.get("timestamp", []))
        if n > 0:
            first = _ms_to_dt(d["timestamp"][0])
            last = _ms_to_dt(d["timestamp"][-1])
            print(f"  ✅ 1m(2020-01): {n}条, {first} ~ {last}")
        else:
            print(f"  ❌ 1m(2020-01): 无数据")
    else:
        print(f"  ❌ 1m(2020-01): {data}")

    # 2020年全年5分钟K线
    data = _get(BASE_URL, "/v1/klines", {
        "symbol": symbol, "period": "5m",
        "start_time": _ts_ms("2020-01-02"),
        "end_time": _ts_ms("2020-12-31"),
    })
    if "data" in data:
        d = data["data"]
        n = len(d.get("timestamp", []))
        if n > 0:
            first = _ms_to_dt(d["timestamp"][0])
            last = _ms_to_dt(d["timestamp"][-1])
            print(f"  ✅ 5m(2020全年): {n}条, {first} ~ {last}")
        else:
            print(f"  ❌ 5m(2020全年): 无数据")
    else:
        print(f"  ❌ 5m(2020全年): {data}")


def test_kline_adjust() -> None:
    print("\n" + "=" * 70)
    print("测试5: 复权方式对比")
    print("=" * 70)

    symbol, name = "600519.SH", "贵州茅台"

    for adjust in ["none", "forward", "forward_additive", "backward",
                   "backward_additive"]:
        data = _get(BASE_URL, "/v1/klines", {
            "symbol": symbol, "period": "1d", "count": 5,
            "adjust": adjust,
        })
        if "data" in data:
            d = data["data"]
            n = len(d.get("timestamp", []))
            if n > 0:
                last_close = d["close"][-1]
                print(f"  ✅ adjust={adjust:20s}: 最新收盘{last_close:.2f}")
            else:
                print(f"  ❌ adjust={adjust:20s}: 无数据")
        else:
            print(f"  ❌ adjust={adjust:20s}: {data}")
        time.sleep(0.2)


def test_intraday() -> None:
    print("\n" + "=" * 70)
    print("测试6: 当日分钟K线 /v1/klines/intraday")
    print("=" * 70)

    for symbol, name in _TEST_SYMBOLS:
        for period in ["1m", "5m"]:
            data = _get(BASE_URL, "/v1/klines/intraday", {
                "symbol": symbol, "period": period,
            })
            if "data" in data:
                d = data["data"]
                n = len(d.get("timestamp", []))
                if n > 0:
                    first = _ms_to_dt(d["timestamp"][0])
                    last = _ms_to_dt(d["timestamp"][-1])
                    print(f"  ✅ {name}({symbol}) {period}: "
                          f"{n}条, {first} ~ {last}")
                else:
                    print(f"  ❌ {name}({symbol}) {period}: 无数据(非交易时间?)")
            else:
                print(f"  ❌ {name}({symbol}) {period}: {data}")
            time.sleep(0.2)


def test_quote() -> None:
    print("\n" + "=" * 70)
    print("测试7: 实时行情 /v1/quotes")
    print("=" * 70)

    symbols = ",".join([s for s, _ in _TEST_SYMBOLS])
    data = _get(BASE_URL, "/v1/quotes", {"symbols": symbols})
    if "data" in data:
        quotes = data["data"]
        print(f"  ✅ 获取 {len(quotes)} 只股票行情")
        for q in quotes:
            sym = q.get("symbol", "N/A")
            last = q.get("last_price", 0)
            vol = q.get("volume", 0)
            ext = q.get("ext", {})
            qname = ext.get("name", "N/A")
            change_pct = ext.get("change_pct", 0)
            print(f"    {sym}({qname}): 最新{last:.2f} "
                  f"涨跌{change_pct:.2f}% 成交量{vol}")
    else:
        print(f"  ❌ 失败: {data}")


def test_quote_depth() -> None:
    print("\n" + "=" * 70)
    print("测试8: 五档行情 /v1/quotes/depth")
    print("=" * 70)

    symbol, name = "600519.SH", "贵州茅台"
    data = _get(BASE_URL, "/v1/quotes/depth", {"symbol": symbol})
    if "data" in data:
        d = data["data"]
        print(f"  ✅ {name} 五档行情:")
        print(f"    结果: {json.dumps(d, ensure_ascii=False)[:300]}")
    else:
        print(f"  ❌ 失败: {data}")


def test_batch_quote() -> None:
    print("\n" + "=" * 70)
    print("测试9: 批量实时行情 /v1/quotes/batch")
    print("=" * 70)

    symbols = ",".join([s for s, _ in _TEST_SYMBOLS])
    data = _get(BASE_URL, "/v1/quotes/batch", {"symbols": symbols})
    if "data" in data:
        quotes = data["data"]
        print(f"  ✅ 批量获取 {len(quotes)} 只股票行情")
        for q in quotes:
            sym = q.get("symbol", "N/A")
            last = q.get("last_price", 0)
            print(f"    {sym}: {last:.2f}")
    else:
        print(f"  ❌ 失败: {data}")


def test_batch_kline() -> None:
    print("\n" + "=" * 70)
    print("测试10: 批量K线 /v1/klines/batch")
    print("=" * 70)

    symbols = ",".join([s for s, _ in _TEST_SYMBOLS])
    data = _get(BASE_URL, "/v1/klines/batch", {
        "symbols": symbols, "period": "1d", "count": 5,
    })
    if "data" in data:
        d = data["data"]
        for sym, kdata in d.items():
            n = len(kdata.get("timestamp", []))
            if n > 0:
                last = _ms_to_dt(kdata["timestamp"][-1])
                print(f"  ✅ {sym}: {n}条日K, 最新{last}")
            else:
                print(f"  ❌ {sym}: 无数据")
    else:
        print(f"  ❌ 失败: {data}")


def test_ex_factors() -> None:
    print("\n" + "=" * 70)
    print("测试11: 除权因子 /v1/klines/ex-factors")
    print("=" * 70)

    symbols = "600519.SH,000001.SZ"
    data = _get(BASE_URL, "/v1/klines/ex-factors", {"symbols": symbols})
    if "data" in data:
        d = data["data"]
        print(f"  ✅ 除权因子: {json.dumps(d, ensure_ascii=False)[:300]}")
    else:
        print(f"  ❌ 失败: {data}")


def test_universes() -> None:
    print("\n" + "=" * 70)
    print("测试12: 标的池 /v1/universes")
    print("=" * 70)

    data = _get(BASE_URL, "/v1/universes")
    if "data" in data:
        universes = data["data"]
        print(f"  ✅ 标的池列表:")
        for u in universes:
            uid = u.get("id", "N/A")
            uname = u.get("name", "N/A")
            count = u.get("symbol_count", 0)
            print(f"    {uid}: {uname} ({count}只)")
    else:
        print(f"  ❌ 失败: {data}")


def test_instruments() -> None:
    print("\n" + "=" * 70)
    print("测试13: 标的信息 /v1/instruments")
    print("=" * 70)

    for symbol, name in _TEST_SYMBOLS[:2]:
        data = _get(BASE_URL, f"/v1/instruments/{symbol}")
        if "data" in data:
            d = data["data"]
            print(f"  ✅ {symbol}: {d.get('name', 'N/A')} "
                  f"市场={d.get('region', 'N/A')} "
                  f"类型={d.get('type', 'N/A')}")
        else:
            print(f"  ❌ {symbol}: {data}")
        time.sleep(0.1)


def test_free_service() -> None:
    print("\n" + "=" * 70)
    print("测试14: 免费服务(日K线)")
    print("=" * 70)

    # 免费服务不需要API Key
    data = _get(FREE_URL, "/v1/klines", {
        "symbol": "600519.SH", "period": "1d", "count": 10,
    }, use_key=False)
    if "data" in data:
        d = data["data"]
        n = len(d.get("timestamp", []))
        if n > 0:
            first = _ms_to_dt(d["timestamp"][0])
            last = _ms_to_dt(d["timestamp"][-1])
            print(f"  ✅ 免费日K: {n}条, {first} ~ {last}")
        else:
            print(f"  ❌ 免费日K: 无数据")
    else:
        print(f"  ❌ 免费日K: {data}")

    # 免费服务不支持分钟线
    data = _get(FREE_URL, "/v1/klines", {
        "symbol": "600519.SH", "period": "1m", "count": 10,
    }, use_key=False)
    if "data" in data:
        d = data["data"]
        n = len(d.get("timestamp", []))
        print(f"  1m(免费): {n}条 {'✅' if n > 0 else '❌(预期不支持)'}")
    else:
        print(f"  1m(免费): ❌ {data.get('error', data)} (预期不支持)")


def test_kline_1m_history_depth() -> None:
    print("\n" + "=" * 70)
    print("测试15: 1分钟K线历史深度精确探测(分页)")
    print("=" * 70)

    symbol, name = "600519.SH", "贵州茅台"

    # 通过start_time分页获取更早数据
    end_ts = _ts_ms("2026-05-18")
    total = 0
    earliest = ""

    for page in range(10):
        data = _get(BASE_URL, "/v1/klines", {
            "symbol": symbol, "period": "1m", "count": 10000,
            "end_time": end_ts,
        })
        if "data" in data:
            d = data["data"]
            timestamps = d.get("timestamp", [])
            n = len(timestamps)
            if n == 0:
                break
            total += n
            earliest = _ms_to_dt(timestamps[0])
            latest = _ms_to_dt(timestamps[-1])
            print(f"  第{page+1}页: {n}条, {earliest} ~ {latest}")

            # 下一页的end_time = 本页最早时间 - 1ms
            end_ts = timestamps[0] - 1
        else:
            print(f"  第{page+1}页: ❌ {data}")
            break
        time.sleep(0.5)

    print(f"\n  📊 总计: {total}条, 最早: {earliest}")


def test_data_quality() -> None:
    print("\n" + "=" * 70)
    print("测试16: 数据质量验证")
    print("=" * 70)

    symbol, name = "600519.SH", "贵州茅台"

    data = _get(BASE_URL, "/v1/klines", {
        "symbol": symbol, "period": "1m", "count": 5,
    })
    if "data" in data:
        d = data["data"]
        n = len(d.get("timestamp", []))
        print(f"  字段: {list(d.keys())}")
        print(f"  条数: {n}")
        if n > 0:
            for i in range(n):
                ts = _ms_to_dt(d["timestamp"][i])
                o = d["open"][i]
                h = d["high"][i]
                l = d["low"][i]
                c = d["close"][i]
                v = d["volume"][i]
                a = d["amount"][i]
                print(f"    {ts}: O={o:.2f} H={h:.2f} L={l:.2f} "
                      f"C={c:.2f} V={v} A={a:.2f}")
    else:
        print(f"  ❌ 失败: {data}")


def test_financial_data() -> None:
    print("\n" + "=" * 70)
    print("测试17: 财务数据接口")
    print("=" * 70)

    symbol, name = "600519.SH", "贵州茅台"

    for endpoint, desc in [
        ("/v1/financials/income", "利润表"),
        ("/v1/financials/balance-sheet", "资产负债表"),
        ("/v1/financials/cash-flow", "现金流量表"),
        ("/v1/financials/key-metrics", "核心财务指标"),
        ("/v1/financials/share-capital", "股本表"),
    ]:
        data = _get(BASE_URL, endpoint, {"symbol": symbol, "count": 2})
        if "data" in data:
            d = data["data"]
            if isinstance(d, list):
                print(f"  ✅ {desc}: {len(d)}条")
            elif isinstance(d, dict):
                keys = list(d.keys())[:5]
                print(f"  ✅ {desc}: 字段{keys}")
            else:
                print(f"  ✅ {desc}: {str(d)[:100]}")
        else:
            print(f"  ❌ {desc}: {data.get('error', data)}")
        time.sleep(0.2)


def test_multi_stock_1m() -> None:
    print("\n" + "=" * 70)
    print("测试18: 多股票1分钟线对比")
    print("=" * 70)

    for symbol, name in _TEST_SYMBOLS:
        data = _get(BASE_URL, "/v1/klines", {
            "symbol": symbol, "period": "1m", "count": 10000,
        })
        if "data" in data:
            d = data["data"]
            n = len(d.get("timestamp", []))
            if n > 0:
                first = _ms_to_dt(d["timestamp"][0])
                last = _ms_to_dt(d["timestamp"][-1])
                print(f"  ✅ {name}({symbol}): {n}条, {first} ~ {last}")
            else:
                print(f"  ❌ {name}({symbol}): 无数据")
        else:
            print(f"  ❌ {name}({symbol}): {data}")
        time.sleep(0.3)


def main() -> None:
    print("╔" + "═" * 68 + "╗")
    print("║" + " TickFlow API 全量验证".center(50) + "║")
    print("║" + " https://docs.tickflow.org".center(50) + "║")
    print("║" + f" 验证日期: 2026-05-18".center(50) + "║")
    print("╚" + "═" * 68 + "╝")

    test_kline_1m_depth()
    test_kline_5m_depth()
    test_kline_all_periods()
    test_kline_time_range()
    test_kline_adjust()
    test_intraday()
    test_quote()
    test_quote_depth()
    test_batch_quote()
    test_batch_kline()
    test_ex_factors()
    test_universes()
    test_instruments()
    test_free_service()
    test_kline_1m_history_depth()
    test_data_quality()
    test_financial_data()
    test_multi_stock_1m()

    print("\n" + "=" * 70)
    print("✅ TickFlow API 全量验证完成")
    print("=" * 70)


if __name__ == "__main__":
    main()
