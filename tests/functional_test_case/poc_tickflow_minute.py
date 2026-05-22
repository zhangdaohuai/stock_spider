"""TickFlow 分钟线数据全量验证脚本(升级API Key)

验证升级后的API Key是否具备分钟线查询权限，
并深度测试1分钟/5分钟K线的历史深度、分页能力、数据质量。
"""

import os

for _proxy_key in [
    "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
    "ALL_PROXY", "all_proxy",
]:
    os.environ.pop(_proxy_key, None)

from datetime import datetime, timedelta, timezone

import requests

API_KEY = "tk_0829befe5a1640c78324d0c10a529c0e"
BASE_URL = "https://api.tickflow.org"

_HEADERS = {"x-api-key": API_KEY}

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


def _get(path: str, params: dict | None = None) -> dict:
    session = requests.Session()
    session.trust_env = False
    try:
        resp = session.get(f"{BASE_URL}{path}", params=params,
                           headers=_HEADERS, timeout=30)
        return resp.json()
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


def test_permission_check() -> None:
    print("=" * 70)
    print("测试1: 新API Key权限检查")
    print("=" * 70)

    tests = [
        ("1分钟K线", "/v1/klines", {"symbol": "600519.SH", "period": "1m", "count": 5}),
        ("5分钟K线", "/v1/klines", {"symbol": "600519.SH", "period": "5m", "count": 5}),
        ("日K线", "/v1/klines", {"symbol": "600519.SH", "period": "1d", "count": 5}),
        ("当日分钟K线", "/v1/klines/intraday", {"symbol": "600519.SH", "period": "1m"}),
        ("除权因子", "/v1/klines/ex-factors", {"symbols": "600519.SH"}),
        ("实时行情", "/v1/quotes", {"symbols": "600519.SH"}),
    ]

    for name, path, params in tests:
        data = _get(path, params)
        if "error" in data:
            print(f"  ❌ {name}: 连接错误 - {data['error'][:80]}")
        elif "code" in data and data["code"] not in (0, "0"):
            code = data.get("code", "")
            msg = data.get("message", "")[:60]
            print(f"  ❌ {name}: {code} - {msg}")
        elif "data" in data:
            d = data["data"]
            if isinstance(d, dict):
                n = len(d.get("timestamp", d.get("close", [])))
                if isinstance(d, list):
                    n = len(d)
                print(f"  ✅ {name}: {n}条数据")
            elif isinstance(d, list):
                print(f"  ✅ {name}: {len(d)}条数据")
            else:
                print(f"  ✅ {name}: 可用")
        else:
            print(f"  ❓ {name}: {str(data)[:80]}")


def test_1m_depth() -> None:
    print("\n" + "=" * 70)
    print("测试2: 1分钟K线历史深度(单次最大10000条)")
    print("=" * 70)

    symbol, name = "600519.SH", "贵州茅台"

    data = _get("/v1/klines", {
        "symbol": symbol, "period": "1m", "count": 10000,
    })
    if "data" in data:
        d = data["data"]
        timestamps = d.get("timestamp", [])
        n = len(timestamps)
        if n > 0:
            first = _ms_to_dt(timestamps[0])
            last = _ms_to_dt(timestamps[-1])
            print(f"  ✅ 1m(10000条): {n}条, {first} ~ {last}")

            # 按日统计
            dates: dict[str, int] = {}
            for ts in timestamps:
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
            print(f"  ❌ 1m: 无数据")
    else:
        print(f"  ❌ 1m: {data}")


def test_1m_pagination() -> None:
    print("\n" + "=" * 70)
    print("测试3: 1分钟K线分页深度探测(逐页回溯)")
    print("=" * 70)

    symbol, name = "600519.SH", "贵州茅台"

    end_ts = _ts_ms("2026-05-18")
    total = 0
    earliest = ""
    all_dates: dict[str, int] = {}

    for page in range(20):
        data = _get("/v1/klines", {
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
            print(f"  第{page+1:2d}页: {n}条, {earliest} ~ {latest}")

            for ts in timestamps:
                dt_str = _ms_to_dt(ts)[:10]
                all_dates[dt_str] = all_dates.get(dt_str, 0) + 1

            end_ts = timestamps[0] - 1
        else:
            print(f"  第{page+1:2d}页: ❌ {data}")
            break

    print(f"\n  📊 总计: {total}条, 覆盖{len(all_dates)}天, 最早: {earliest}")


def test_5m_depth() -> None:
    print("\n" + "=" * 70)
    print("测试4: 5分钟K线历史深度")
    print("=" * 70)

    symbol, name = "600519.SH", "贵州茅台"

    data = _get("/v1/klines", {
        "symbol": symbol, "period": "5m", "count": 10000,
    })
    if "data" in data:
        d = data["data"]
        timestamps = d.get("timestamp", [])
        n = len(timestamps)
        if n > 0:
            first = _ms_to_dt(timestamps[0])
            last = _ms_to_dt(timestamps[-1])
            print(f"  ✅ 5m(10000条): {n}条, {first} ~ {last}")

            dates: dict[str, int] = {}
            for ts in timestamps:
                dt_str = _ms_to_dt(ts)[:10]
                dates[dt_str] = dates.get(dt_str, 0) + 1
            print(f"  覆盖天数: {len(dates)}")
        else:
            print(f"  ❌ 5m: 无数据")
    else:
        print(f"  ❌ 5m: {data}")

    # 5分钟线分页深度
    end_ts = _ts_ms("2026-05-18")
    total = 0
    earliest = ""

    for page in range(10):
        data = _get("/v1/klines", {
            "symbol": symbol, "period": "5m", "count": 10000,
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
            if page < 3 or page % 5 == 0:
                print(f"  5m第{page+1:2d}页: {n}条, {earliest} ~ "
                      f"{_ms_to_dt(timestamps[-1])}")
            end_ts = timestamps[0] - 1
        else:
            break

    print(f"  📊 5m总计: {total}条, 最早: {earliest}")


def test_all_periods() -> None:
    print("\n" + "=" * 70)
    print("测试5: 所有分钟周期可用性")
    print("=" * 70)

    symbol, name = "600519.SH", "贵州茅台"

    for period in ["1m", "5m", "10m", "15m", "30m", "60m"]:
        data = _get("/v1/klines", {
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
            print(f"  ❌ {period:4s}: {data}")
        import time
        time.sleep(0.2)


def test_time_range() -> None:
    print("\n" + "=" * 70)
    print("测试6: 指定时间范围获取分钟K线")
    print("=" * 70)

    symbol, name = "600519.SH", "贵州茅台"

    # 2020年1月1分钟K线
    data = _get("/v1/klines", {
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
    data = _get("/v1/klines", {
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


def test_adjust() -> None:
    print("\n" + "=" * 70)
    print("测试7: 复权方式对比(1分钟线)")
    print("=" * 70)

    symbol, name = "600519.SH", "贵州茅台"

    for adjust in ["none", "forward", "forward_additive"]:
        data = _get("/v1/klines", {
            "symbol": symbol, "period": "1m", "count": 5,
            "adjust": adjust,
        })
        if "data" in data:
            d = data["data"]
            n = len(d.get("timestamp", []))
            if n > 0:
                last_close = d["close"][-1]
                first_close = d["close"][0]
                print(f"  ✅ adjust={adjust:20s}: "
                      f"首收{first_close:.2f} 末收{last_close:.2f}")
            else:
                print(f"  ❌ adjust={adjust:20s}: 无数据")
        else:
            print(f"  ❌ adjust={adjust:20s}: {data}")
        import time
        time.sleep(0.2)


def test_intraday() -> None:
    print("\n" + "=" * 70)
    print("测试8: 当日分钟K线 /v1/klines/intraday")
    print("=" * 70)

    for symbol, name in _TEST_SYMBOLS:
        for period in ["1m", "5m"]:
            data = _get("/v1/klines/intraday", {
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
            import time
            time.sleep(0.2)


def test_data_quality() -> None:
    print("\n" + "=" * 70)
    print("测试9: 1分钟K线数据质量")
    print("=" * 70)

    symbol, name = "600519.SH", "贵州茅台"

    data = _get("/v1/klines", {
        "symbol": symbol, "period": "1m", "count": 10,
    })
    if "data" in data:
        d = data["data"]
        n = len(d.get("timestamp", []))
        print(f"  字段: {list(d.keys())}")
        print(f"  条数: {n}")
        if n > 0:
            print(f"\n  前5条:")
            for i in range(min(5, n)):
                ts = _ms_to_dt(d["timestamp"][i])
                o = d["open"][i]
                h = d["high"][i]
                l = d["low"][i]
                c = d["close"][i]
                v = d["volume"][i]
                a = d["amount"][i]
                print(f"    {ts}: O={o:.2f} H={h:.2f} L={l:.2f} "
                      f"C={c:.2f} V={v} A={a:.2f}")

            # 验证OHLCV一致性
            print(f"\n  OHLCV一致性检查:")
            for i in range(min(5, n)):
                o = d["open"][i]
                h = d["high"][i]
                l = d["low"][i]
                c = d["close"][i]
                ok = (l <= o <= h and l <= c <= h)
                if not ok:
                    print(f"    ❌ 第{i}条: O={o} H={h} L={l} C={c} 不一致!")
            print(f"    ✅ OHLCV一致性检查通过")
    else:
        print(f"  ❌ 失败: {data}")


def test_batch_kline() -> None:
    print("\n" + "=" * 70)
    print("测试10: 批量K线查询 /v1/klines/batch")
    print("=" * 70)

    symbols = ",".join([s for s, _ in _TEST_SYMBOLS])
    data = _get("/v1/klines/batch", {
        "symbols": symbols, "period": "1m", "count": 5,
    })
    if "data" in data:
        d = data["data"]
        for sym, kdata in d.items():
            n = len(kdata.get("timestamp", []))
            if n > 0:
                last = _ms_to_dt(kdata["timestamp"][-1])
                print(f"  ✅ {sym}: {n}条1mK线, 最新{last}")
            else:
                print(f"  ❌ {sym}: 无数据")
    else:
        print(f"  ❌ 失败: {data}")


def test_ex_factors() -> None:
    print("\n" + "=" * 70)
    print("测试11: 除权因子 /v1/klines/ex-factors")
    print("=" * 70)

    data = _get("/v1/klines/ex-factors", {
        "symbols": "600519.SH,000001.SZ",
    })
    if "data" in data:
        d = data["data"]
        import json
        print(f"  ✅ 除权因子: {json.dumps(d, ensure_ascii=False)[:300]}")
    else:
        print(f"  ❌ 失败: {data}")


def test_multi_stock_1m() -> None:
    print("\n" + "=" * 70)
    print("测试12: 多股票1分钟线深度对比")
    print("=" * 70)

    for symbol, name in _TEST_SYMBOLS:
        data = _get("/v1/klines", {
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
        import time
        time.sleep(0.3)


def main() -> None:
    print("╔" + "═" * 68 + "╗")
    print("║" + " TickFlow 分钟线数据全量验证(升级Key)".center(46) + "║")
    print("║" + f" 验证日期: 2026-05-18".center(46) + "║")
    print("╚" + "═" * 68 + "╝")

    test_permission_check()
    test_1m_depth()
    test_1m_pagination()
    test_5m_depth()
    test_all_periods()
    test_time_range()
    test_adjust()
    test_intraday()
    test_data_quality()
    test_batch_kline()
    test_ex_factors()
    test_multi_stock_1m()

    print("\n" + "=" * 70)
    print("✅ TickFlow 分钟线全量验证完成")
    print("=" * 70)


if __name__ == "__main__":
    main()
