"""TickFlow API 权限和免费服务深度验证

1. 验证API Key的权限范围
2. 免费服务日K线深度探测
3. 付费服务可用接口测试
"""

import os

for _proxy_key in [
    "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
    "ALL_PROXY", "all_proxy",
]:
    os.environ.pop(_proxy_key, None)

from datetime import datetime, timedelta, timezone

import requests

API_KEY = "tk_1c0550b2bbab440b9001123daf680e1e"
BASE_URL = "https://api.tickflow.org"
FREE_URL = "https://free-api.tickflow.org"

_HEADERS = {"x-api-key": API_KEY}


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


def test_api_key_permissions() -> None:
    print("=" * 70)
    print("测试1: API Key权限范围检测")
    print("=" * 70)

    # 逐个测试各接口
    tests = [
        ("实时行情", "/v1/quotes", {"symbols": "600519.SH"}),
        ("五档行情", "/v1/quotes/depth", {"symbol": "600519.SH"}),
        ("K线1m", "/v1/klines", {"symbol": "600519.SH", "period": "1m", "count": 5}),
        ("K线1d", "/v1/klines", {"symbol": "600519.SH", "period": "1d", "count": 5}),
        ("当日分钟K线", "/v1/klines/intraday", {"symbol": "600519.SH", "period": "1m"}),
        ("除权因子", "/v1/klines/ex-factors", {"symbols": "600519.SH"}),
        ("标的池", "/v1/universes", None),
        ("标的信息", "/v1/instruments/600519.SH", None),
    ]

    for name, path, params in tests:
        data = _get(BASE_URL, path, params)
        if "error" in data:
            print(f"  ❌ {name}: 连接错误 - {data['error'][:80]}")
        elif "code" in data:
            code = data.get("code", "")
            msg = data.get("message", "")
            if code == "NO_KLINE_PERMISSION":
                print(f"  ❌ {name}: 无K线权限")
            elif code == "FREE_TIER_RESTRICTED":
                print(f"  ❌ {name}: 免费服务限制")
            else:
                print(f"  ❌ {name}: {code} - {msg[:60]}")
        elif "data" in data:
            d = data["data"]
            if isinstance(d, list):
                print(f"  ✅ {name}: {len(d)}条数据")
            elif isinstance(d, dict):
                keys = list(d.keys())[:5]
                print(f"  ✅ {name}: 字段{keys}")
            else:
                print(f"  ✅ {name}: {str(d)[:80]}")
        else:
            print(f"  ❓ {name}: {str(data)[:80]}")


def test_free_day_kline_depth() -> None:
    print("\n" + "=" * 70)
    print("测试2: 免费服务日K线深度")
    print("=" * 70)

    # 最大10000条日K线
    data = _get(FREE_URL, "/v1/klines", {
        "symbol": "600519.SH", "period": "1d", "count": 10000,
    }, use_key=False)
    if "data" in data:
        d = data["data"]
        n = len(d.get("timestamp", []))
        if n > 0:
            first = _ms_to_dt(d["timestamp"][0])
            last = _ms_to_dt(d["timestamp"][-1])
            print(f"  ✅ 日K线(10000条): {n}条, {first} ~ {last}")
        else:
            print(f"  ❌ 日K线: 无数据")
    else:
        print(f"  ❌ 日K线: {data}")

    # 指定时间范围(2020年)
    data = _get(FREE_URL, "/v1/klines", {
        "symbol": "600519.SH", "period": "1d",
        "start_time": _ts_ms("2020-01-02"),
        "end_time": _ts_ms("2020-12-31"),
    }, use_key=False)
    if "data" in data:
        d = data["data"]
        n = len(d.get("timestamp", []))
        if n > 0:
            first = _ms_to_dt(d["timestamp"][0])
            last = _ms_to_dt(d["timestamp"][-1])
            print(f"  ✅ 日K线(2020年): {n}条, {first} ~ {last}")
        else:
            print(f"  ❌ 日K线(2020年): 无数据")
    else:
        print(f"  ❌ 日K线(2020年): {data}")


def test_free_kline_periods() -> None:
    print("\n" + "=" * 70)
    print("测试3: 免费服务支持的K线周期")
    print("=" * 70)

    for period in ["1m", "5m", "15m", "30m", "60m",
                   "1d", "1w", "1M", "1Q", "1Y"]:
        data = _get(FREE_URL, "/v1/klines", {
            "symbol": "600519.SH", "period": period, "count": 5,
        }, use_key=False)
        if "data" in data:
            d = data["data"]
            n = len(d.get("timestamp", []))
            if n > 0:
                print(f"  ✅ {period:4s}: {n}条")
            else:
                print(f"  ❌ {period:4s}: 无数据")
        elif "code" in data:
            print(f"  ❌ {period:4s}: {data.get('code', '')} - "
                  f"{data.get('message', '')[:60]}")
        else:
            print(f"  ❌ {period:4s}: {data}")
        time.sleep(0.2)


def test_paid_day_kline() -> None:
    print("\n" + "=" * 70)
    print("测试4: 付费服务日K线(用API Key)")
    print("=" * 70)

    data = _get(BASE_URL, "/v1/klines", {
        "symbol": "600519.SH", "period": "1d", "count": 5,
    })
    if "data" in data:
        d = data["data"]
        n = len(d.get("timestamp", []))
        if n > 0:
            print(f"  ✅ 付费日K线: {n}条")
            for i in range(n):
                ts = _ms_to_dt(d["timestamp"][i])[:10]
                o = d["open"][i]
                h = d["high"][i]
                l = d["low"][i]
                c = d["close"][i]
                v = d["volume"][i]
                print(f"    {ts}: O={o:.2f} H={h:.2f} L={l:.2f} "
                      f"C={c:.2f} V={v}")
        else:
            print(f"  ❌ 付费日K线: 无数据")
    else:
        print(f"  ❌ 付费日K线: {data}")


def test_free_universes() -> None:
    print("\n" + "=" * 70)
    print("测试5: 免费服务标的池")
    print("=" * 70)

    data = _get(FREE_URL, "/v1/universes", None, use_key=False)
    if "data" in data:
        universes = data["data"]
        main_pools = [u for u in universes
                      if u.get("id", "").startswith("CN_Equity_A")
                      or u.get("id", "").startswith("CN_ETF")
                      or u.get("id", "").startswith("CN_Index")]
        print(f"  ✅ 总标的池: {len(universes)}个")
        print(f"  主要标的池:")
        for u in main_pools:
            print(f"    {u.get('id')}: {u.get('name')} "
                  f"({u.get('symbol_count', 0)}只)")
    else:
        print(f"  ❌ 失败: {data}")


def test_free_instruments() -> None:
    print("\n" + "=" * 70)
    print("测试6: 免费服务标的信息")
    print("=" * 70)

    data = _get(FREE_URL, "/v1/instruments/600519.SH", None, use_key=False)
    if "data" in data:
        d = data["data"]
        print(f"  ✅ 茅台: {d.get('name', 'N/A')} "
              f"市场={d.get('region', 'N/A')} "
              f"类型={d.get('type', 'N/A')}")
    else:
        print(f"  ❌ 失败: {data}")


def test_free_ex_factors() -> None:
    print("\n" + "=" * 70)
    print("测试7: 免费服务除权因子")
    print("=" * 70)

    data = _get(FREE_URL, "/v1/klines/ex-factors", {
        "symbols": "600519.SH",
    }, use_key=False)
    if "data" in data:
        d = data["data"]
        print(f"  ✅ 除权因子: {str(d)[:200]}")
    else:
        print(f"  ❌ 失败: {data}")


def test_hk_endpoint() -> None:
    print("\n" + "=" * 70)
    print("测试8: 备用端点 hk-api.tickflow.org")
    print("=" * 70)

    data = _get("https://hk-api.tickflow.org", "/v1/klines", {
        "symbol": "600519.SH", "period": "1d", "count": 5,
    })
    if "data" in data:
        d = data["data"]
        n = len(d.get("timestamp", []))
        print(f"  ✅ HK端点日K线: {n}条")
    else:
        print(f"  ❌ HK端点: {data}")


import time


def main() -> None:
    print("╔" + "═" * 68 + "╗")
    print("║" + " TickFlow 权限与深度验证".center(50) + "║")
    print("╚" + "═" * 68 + "╝")

    test_api_key_permissions()
    test_free_day_kline_depth()
    test_free_kline_periods()
    test_paid_day_kline()
    test_free_universes()
    test_free_instruments()
    test_free_ex_factors()
    test_hk_endpoint()

    print("\n" + "=" * 70)
    print("✅ TickFlow 权限与深度验证完成")
    print("=" * 70)


if __name__ == "__main__":
    main()
