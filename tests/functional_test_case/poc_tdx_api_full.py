"""tdx-api开源项目全量API验证脚本

验证 https://github.com/oficcejo/tdx-api 的所有RESTful API接口，
重点关注历史分钟线数据的获取能力和数据深度。
"""

import os

for _proxy_key in [
    "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
    "ALL_PROXY", "all_proxy",
]:
    os.environ.pop(_proxy_key, None)

import json
import time
from typing import Any

import requests

BASE_URL = "http://localhost:8080"

_TEST_STOCKS: list[tuple[str, str]] = [
    ("600519", "贵州茅台"),
    ("000858", "五粮液"),
    ("603288", "海天味业"),
    ("000001", "平安银行"),
]


def _get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    resp = requests.get(f"{BASE_URL}{path}", params=params, timeout=30)
    return resp.json()


def _post(path: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    resp = requests.post(f"{BASE_URL}{path}", json=data, timeout=30)
    return resp.json()


def test_health() -> None:
    print("=" * 70)
    print("测试1: 健康检查 /api/health")
    print("=" * 70)
    data = _get("/api/health")
    print(f"  结果: {json.dumps(data, ensure_ascii=False)}")
    status = "✅" if data.get("status") == "healthy" else "❌"
    print(f"  {status} 服务状态: {data.get('status', 'N/A')}")


def test_server_status() -> None:
    print("\n" + "=" * 70)
    print("测试2: 服务器状态 /api/server-status")
    print("=" * 70)
    data = _get("/api/server-status")
    result = data.get("data", {})
    print(f"  状态: {result.get('status', 'N/A')}")
    print(f"  连接: {result.get('connected', 'N/A')}")
    print(f"  版本: {result.get('version', 'N/A')}")


def test_quote() -> None:
    print("\n" + "=" * 70)
    print("测试3: 五档行情 /api/quote")
    print("=" * 70)

    codes = ",".join([c for c, _ in _TEST_STOCKS])
    data = _get("/api/quote", {"code": codes})

    if data.get("code") == 0:
        quotes = data.get("data", [])
        print(f"  ✅ 获取 {len(quotes)} 只股票行情")
        for q in quotes:
            code = q.get("Code", "N/A")
            close = q.get("K", {}).get("Close", 0) / 1000
            vol = q.get("TotalHand", 0)
            buy1 = q.get("BuyLevel", [{}])[0].get("Price", 0) / 1000
            sell1 = q.get("SellLevel", [{}])[0].get("Price", 0) / 1000
            print(f"    {code}: 最新{close:.2f} 买一{buy1:.2f} 卖一{sell1:.2f} 成交量{vol}手")
    else:
        print(f"  ❌ 失败: {data.get('message', 'N/A')}")


def test_kline_types() -> None:
    print("\n" + "=" * 70)
    print("测试4: 所有K线类型 /api/kline")
    print("=" * 70)

    kline_types = [
        "minute1", "minute5", "minute15", "minute30", "hour",
        "day", "week", "month",
    ]

    for ktype in kline_types:
        data = _get("/api/kline", {"code": "600519", "type": ktype})
        if data.get("code") == 0:
            kline_data = data.get("data", {})
            count = kline_data.get("Count", 0)
            items = kline_data.get("List", [])
            if items:
                first_time = items[0].get("Time", "N/A")[:19]
                last_time = items[-1].get("Time", "N/A")[:19]
                print(f"  ✅ {ktype:10s}: {count}条, {first_time} ~ {last_time}")
            else:
                print(f"  ❌ {ktype:10s}: 无数据")
        else:
            print(f"  ❌ {ktype:10s}: {data.get('message', 'N/A')}")
        time.sleep(0.3)


def test_minute_history() -> None:
    print("\n" + "=" * 70)
    print("测试5: 历史分时数据深度 /api/minute")
    print("=" * 70)

    # 近期日期
    recent_dates = [
        "20260515", "20260514", "20260513", "20260512", "20260508",
        "20260430", "20260428",
    ]
    print("  近期分时数据:")
    for date in recent_dates:
        data = _get("/api/minute", {"code": "600519", "date": date})
        if data.get("code") == 0:
            minute_data = data.get("data", {})
            actual_date = minute_data.get("date", "N/A")
            items = minute_data.get("List", [])
            count = minute_data.get("Count", 0)
            if items:
                first_price = items[0].get("Price", 0) / 1000
                last_price = items[-1].get("Price", 0) / 1000
                print(f"    ✅ {date}(实际{actual_date}): {count}条, "
                      f"首价{first_price:.2f} 末价{last_price:.2f}")
            else:
                print(f"    ❌ {date}(实际{actual_date}): 无数据")
        else:
            print(f"    ❌ {date}: {data.get('message', 'N/A')}")
        time.sleep(0.1)

    # 深度回溯
    deep_dates = [
        "20250115", "20240615", "20230115", "20220615",
        "20210115", "20200615", "20190615", "20150615",
        "20120615", "20100615",
    ]
    print("\n  深度回溯:")
    earliest = ""
    for date in deep_dates:
        data = _get("/api/minute", {"code": "600519", "date": date})
        if data.get("code") == 0:
            minute_data = data.get("data", {})
            items = minute_data.get("List", [])
            actual_date = minute_data.get("date", "N/A")
            if items:
                earliest = actual_date
                print(f"    ✅ {date}(实际{actual_date}): {len(items)}条")
            else:
                print(f"    ❌ {date}(实际{actual_date}): 无数据")
        else:
            print(f"    ❌ {date}: {data.get('message', 'N/A')}")
        time.sleep(0.1)

    if earliest:
        print(f"\n  📊 最早可获取分时日期: {earliest}")


def test_kline_history() -> None:
    print("\n" + "=" * 70)
    print("测试6: 历史K线 /api/kline-history")
    print("=" * 70)

    # 1分钟K线历史
    data = _get("/api/kline-history", {
        "code": "600519", "type": "minute1", "limit": 800,
    })
    if data.get("code") == 0:
        items = data.get("data", {}).get("List", [])
        if items:
            first_time = items[0].get("Time", "N/A")[:19]
            last_time = items[-1].get("Time", "N/A")[:19]
            print(f"  1分钟K线(800条): {first_time} ~ {last_time}")
        else:
            print(f"  1分钟K线: 无数据")
    else:
        print(f"  ❌ 1分钟K线: {data.get('message', 'N/A')}")

    # 5分钟K线历史
    data = _get("/api/kline-history", {
        "code": "600519", "type": "minute5", "limit": 800,
    })
    if data.get("code") == 0:
        items = data.get("data", {}).get("List", [])
        if items:
            first_time = items[0].get("Time", "N/A")[:19]
            last_time = items[-1].get("Time", "N/A")[:19]
            print(f"  5分钟K线(800条): {first_time} ~ {last_time}")
        else:
            print(f"  5分钟K线: 无数据")

    # 日K线历史(指定日期范围)
    data = _get("/api/kline-history", {
        "code": "600519", "type": "day",
        "start_date": "20200101", "end_date": "20200131",
    })
    if data.get("code") == 0:
        items = data.get("data", {}).get("List", [])
        if items:
            first_time = items[0].get("Time", "N/A")[:10]
            last_time = items[-1].get("Time", "N/A")[:10]
            print(f"  日K线(2020-01): {len(items)}条, {first_time} ~ {last_time}")
        else:
            print(f"  日K线(2020-01): 无数据")


def test_kline_all() -> None:
    print("\n" + "=" * 70)
    print("测试7: 全量K线 /api/kline-all")
    print("=" * 70)

    for ktype in ["minute1", "minute5", "day"]:
        data = _get("/api/kline-all", {"code": "600519", "type": ktype})
        if data.get("code") == 0:
            kline_data = data.get("data", {})
            items = kline_data.get("List", [])
            count = kline_data.get("Count", 0)
            if items:
                first_time = items[0].get("Time", "N/A")[:19]
                last_time = items[-1].get("Time", "N/A")[:19]
                print(f"  ✅ {ktype:10s}: {count}条, {first_time} ~ {last_time}")
            else:
                print(f"  ❌ {ktype:10s}: 无数据")
        else:
            print(f"  ❌ {ktype:10s}: {data.get('message', 'N/A')}")
        time.sleep(0.5)


def test_kline_all_tdx_ths() -> None:
    print("\n" + "=" * 70)
    print("测试8: TDX/THS源K线 /api/kline-all/tdx 和 /api/kline-all/ths")
    print("=" * 70)

    for endpoint in ["/api/kline-all/tdx", "/api/kline-all/ths"]:
        data = _get(endpoint, {"code": "600519", "type": "day"})
        if data.get("code") == 0:
            kline_data = data.get("data", {})
            items = kline_data.get("List", [])
            count = kline_data.get("Count", 0)
            if items:
                first_time = items[0].get("Time", "N/A")[:10]
                last_time = items[-1].get("Time", "N/A")[:10]
                print(f"  ✅ {endpoint:25s}: {count}条, {first_time} ~ {last_time}")
            else:
                print(f"  ❌ {endpoint:25s}: 无数据")
        else:
            print(f"  ❌ {endpoint:25s}: {data.get('message', 'N/A')}")
        time.sleep(0.5)


def test_trade() -> None:
    print("\n" + "=" * 70)
    print("测试9: 分时成交 /api/trade")
    print("=" * 70)

    data = _get("/api/trade", {"code": "600519"})
    if data.get("code") == 0:
        trade_data = data.get("data", {})
        items = trade_data.get("List", [])
        count = trade_data.get("Count", 0)
        if items:
            print(f"  ✅ 当日分时成交: {count}条")
            print(f"    首条: 价格{items[0].get('Price', 0)/1000:.2f} "
                  f"量{items[0].get('Volume', 0)}手 "
                  f"方向{items[0].get('Status', 'N/A')}")
        else:
            print(f"  ❌ 当日无成交数据(非交易时间?)")
    else:
        print(f"  ❌ 失败: {data.get('message', 'N/A')}")


def test_trade_history() -> None:
    print("\n" + "=" * 70)
    print("测试10: 历史分时成交 /api/trade-history")
    print("=" * 70)

    data = _get("/api/trade-history", {
        "code": "600519", "date": "20260515", "count": 100,
    })
    if data.get("code") == 0:
        trade_data = data.get("data", {})
        items = trade_data.get("List", [])
        count = trade_data.get("Count", 0)
        if items:
            print(f"  ✅ 20260515分时成交: {count}条")
            print(f"    首条: 价格{items[0].get('Price', 0)/1000:.2f} "
                  f"量{items[0].get('Volume', 0)}手")
        else:
            print(f"  ❌ 无数据")
    else:
        print(f"  ❌ 失败: {data.get('message', 'N/A')}")


def test_minute_trade_all() -> None:
    print("\n" + "=" * 70)
    print("测试11: 全天分时成交 /api/minute-trade-all")
    print("=" * 70)

    data = _get("/api/minute-trade-all", {
        "code": "600519", "date": "20260515",
    })
    if data.get("code") == 0:
        trade_data = data.get("data", {})
        items = trade_data.get("List", [])
        count = trade_data.get("Count", 0)
        if items:
            print(f"  ✅ 20260515全天成交: {count}条")
        else:
            print(f"  ❌ 无数据")
    else:
        print(f"  ❌ 失败: {data.get('message', 'N/A')}")


def test_trade_history_full() -> None:
    print("\n" + "=" * 70)
    print("测试12: 上市以来分时成交 /api/trade-history/full")
    print("=" * 70)

    data = _get("/api/trade-history/full", {
        "code": "600519", "limit": 50,
    })
    if data.get("code") == 0:
        trade_data = data.get("data", {})
        items = trade_data.get("List", [])
        count = trade_data.get("Count", 0)
        if items:
            first_time = items[0].get("Time", "N/A")[:19]
            last_time = items[-1].get("Time", "N/A")[:19]
            print(f"  ✅ 上市以来成交(limit=50): {count}条, "
                  f"{first_time} ~ {last_time}")
        else:
            print(f"  ❌ 无数据")
    else:
        print(f"  ❌ 失败: {data.get('message', 'N/A')}")


def test_codes() -> None:
    print("\n" + "=" * 70)
    print("测试13: 股票列表 /api/codes")
    print("=" * 70)

    for exchange in ["sh", "sz", "all"]:
        data = _get("/api/codes", {"exchange": exchange})
        if data.get("code") == 0:
            code_data = data.get("data", {})
            total = code_data.get("total", 0)
            exchanges = code_data.get("exchanges", {})
            print(f"  ✅ {exchange:3s}: 总计{total}只, {exchanges}")
        else:
            print(f"  ❌ {exchange}: {data.get('message', 'N/A')}")
        time.sleep(0.2)


def test_search() -> None:
    print("\n" + "=" * 70)
    print("测试14: 搜索股票 /api/search")
    print("=" * 70)

    for keyword in ["茅台", "平安", "600519"]:
        data = _get("/api/search", {"keyword": keyword})
        if data.get("code") == 0:
            items = data.get("data", [])
            print(f"  ✅ '{keyword}': 找到{len(items)}只")
            for item in items[:3]:
                print(f"    {item.get('code', 'N/A')} - {item.get('name', 'N/A')}")
        else:
            print(f"  ❌ '{keyword}': {data.get('message', 'N/A')}")
        time.sleep(0.1)


def test_index() -> None:
    print("\n" + "=" * 70)
    print("测试15: 指数数据 /api/index")
    print("=" * 70)

    indices = [
        ("sh000001", "上证指数"),
        ("sz399001", "深证成指"),
        ("sh000300", "沪深300"),
    ]
    for code, name in indices:
        data = _get("/api/index", {"code": code, "type": "day"})
        if data.get("code") == 0:
            items = data.get("data", {}).get("List", [])
            if items:
                first_time = items[0].get("Time", "N/A")[:10]
                print(f"  ✅ {name}({code}): {len(items)}条, 最新{first_time}")
            else:
                print(f"  ❌ {name}({code}): 无数据")
        else:
            print(f"  ❌ {name}({code}): {data.get('message', 'N/A')}")
        time.sleep(0.2)


def test_workday() -> None:
    print("\n" + "=" * 70)
    print("测试16: 交易日查询 /api/workday")
    print("=" * 70)

    data = _get("/api/workday", {"date": "20260515", "count": 3})
    if data.get("code") == 0:
        wd = data.get("data", {})
        is_wd = wd.get("is_workday", False)
        next_days = wd.get("next", [])
        prev_days = wd.get("previous", [])
        print(f"  20260515是否交易日: {is_wd}")
        print(f"  后续交易日: {[d.get('iso', '') for d in next_days]}")
        print(f"  之前交易日: {[d.get('iso', '') for d in prev_days]}")
    else:
        print(f"  ❌ 失败: {data.get('message', 'N/A')}")


def test_workday_range() -> None:
    print("\n" + "=" * 70)
    print("测试17: 交易日范围 /api/workday/range")
    print("=" * 70)

    data = _get("/api/workday/range", {"start": "20260501", "end": "20260515"})
    if data.get("code") == 0:
        wd_data = data.get("data", {})
        days = wd_data.get("workdays", [])
        print(f"  2026-05-01 ~ 2026-05-15: {len(days)}个交易日")
        for d in days[:10]:
            print(f"    {d}")
    else:
        print(f"  ❌ 失败: {data.get('message', 'N/A')}")


def test_market_count() -> None:
    print("\n" + "=" * 70)
    print("测试18: 市场统计 /api/market-count")
    print("=" * 70)

    data = _get("/api/market-count")
    if data.get("code") == 0:
        mc = data.get("data", {})
        total = mc.get("total", 0)
        exchanges = mc.get("exchanges", [])
        print(f"  总计: {total}只")
        for ex in exchanges:
            print(f"    {ex.get('exchange', 'N/A')}: {ex.get('count', 0)}只")
    else:
        print(f"  ❌ 失败: {data.get('message', 'N/A')}")


def test_income() -> None:
    print("\n" + "=" * 70)
    print("测试19: 收益分析 /api/income")
    print("=" * 70)

    data = _get("/api/income", {
        "code": "600519", "start_date": "20260101", "days": "5,10,20",
    })
    if data.get("code") == 0:
        inc = data.get("data", {})
        print(f"  结果: {json.dumps(inc, ensure_ascii=False)[:200]}")
    else:
        print(f"  ❌ 失败: {data.get('message', 'N/A')}")


def test_stock_info() -> None:
    print("\n" + "=" * 70)
    print("测试20: 综合信息 /api/stock-info")
    print("=" * 70)

    data = _get("/api/stock-info", {"code": "600519"})
    if data.get("code") == 0:
        info = data.get("data", {})
        quote = info.get("quote", [])
        kline = info.get("kline_day", {})
        minute = info.get("minute", {})
        print(f"  行情: {len(quote)}只")
        print(f"  日K线: {kline.get('Count', 0)}条")
        print(f"  分时: {minute.get('Count', 0)}条, 日期{minute.get('date', 'N/A')}")
    else:
        print(f"  ❌ 失败: {data.get('message', 'N/A')}")


def test_batch_quote() -> None:
    print("\n" + "=" * 70)
    print("测试21: 批量行情 /api/batch-quote")
    print("=" * 70)

    data = _post("/api/batch-quote", {
        "codes": [c for c, _ in _TEST_STOCKS],
    })
    if data.get("code") == 0:
        quotes = data.get("data", [])
        print(f"  ✅ 批量获取 {len(quotes)} 只股票行情")
        for q in quotes:
            code = q.get("Code", "N/A")
            close = q.get("K", {}).get("Close", 0) / 1000
            print(f"    {code}: {close:.2f}元")
    else:
        print(f"  ❌ 失败: {data.get('message', 'N/A')}")


def test_etf() -> None:
    print("\n" + "=" * 70)
    print("测试22: ETF列表 /api/etf")
    print("=" * 70)

    data = _get("/api/etf", {"limit": 5})
    if data.get("code") == 0:
        etf_data = data.get("data", {})
        total = etf_data.get("total", 0)
        items = etf_data.get("list", [])
        print(f"  ✅ ETF总计{total}只, 显示前5只:")
        for item in items[:5]:
            print(f"    {item.get('code', 'N/A')} - {item.get('name', 'N/A')} "
                  f"最新{item.get('last_price', 0):.3f}")
    else:
        print(f"  ❌ 失败: {data.get('message', 'N/A')}")


def test_minute1_depth() -> None:
    print("\n" + "=" * 70)
    print("测试23: 1分钟K线深度探测(kline-all)")
    print("=" * 70)

    data = _get("/api/kline-all", {"code": "600519", "type": "minute1"})
    if data.get("code") == 0:
        items = data.get("data", {}).get("List", [])
        count = data.get("data", {}).get("Count", 0)
        if items:
            first_time = items[0].get("Time", "N/A")[:19]
            last_time = items[-1].get("Time", "N/A")[:19]
            print(f"  ✅ 1分钟K线全量: {count}条")
            print(f"    最新: {first_time}")
            print(f"    最早: {last_time}")

            # 按日统计
            dates = {}
            for item in items:
                dt = item.get("Time", "")[:10]
                dates[dt] = dates.get(dt, 0) + 1
            print(f"    覆盖天数: {len(dates)}")
            for dt in sorted(dates.keys())[:5]:
                print(f"      {dt}: {dates[dt]}条")
            if len(dates) > 5:
                print(f"      ...")
                for dt in sorted(dates.keys())[-3:]:
                    print(f"      {dt}: {dates[dt]}条")
        else:
            print(f"  ❌ 无数据")
    else:
        print(f"  ❌ 失败: {data.get('message', 'N/A')}")


def test_pull_kline_task() -> None:
    print("\n" + "=" * 70)
    print("测试24: K线入库任务 /api/tasks/pull-kline")
    print("=" * 70)

    data = _post("/api/tasks/pull-kline", {
        "codes": ["600519"],
        "tables": ["minute1"],
        "limit": 1,
    })
    if data.get("code") == 0:
        task_id = data.get("data", {}).get("task_id", "N/A")
        print(f"  ✅ 任务创建成功: {task_id}")

        # 查询任务状态
        time.sleep(2)
        task_data = _get(f"/api/tasks/{task_id}")
        if task_data.get("code") == 0:
            task = task_data.get("data", {})
            print(f"    状态: {task.get('status', 'N/A')}")
        else:
            print(f"    查询失败: {task_data.get('message', 'N/A')}")
    else:
        print(f"  ❌ 失败: {data.get('message', 'N/A')}")


def main() -> None:
    print("╔" + "═" * 68 + "╗")
    print("║" + " tdx-api 开源项目全量API验证".center(50) + "║")
    print("║" + " https://github.com/oficcejo/tdx-api".center(50) + "║")
    print("║" + f" 验证日期: 2026-05-18".center(50) + "║")
    print("╚" + "═" * 68 + "╝")

    test_health()
    test_server_status()
    test_quote()
    test_kline_types()
    test_minute_history()
    test_kline_history()
    test_kline_all()
    test_kline_all_tdx_ths()
    test_trade()
    test_trade_history()
    test_minute_trade_all()
    test_trade_history_full()
    test_codes()
    test_search()
    test_index()
    test_workday()
    test_workday_range()
    test_market_count()
    test_income()
    test_stock_info()
    test_batch_quote()
    test_etf()
    test_minute1_depth()
    test_pull_kline_task()

    print("\n" + "=" * 70)
    print("✅ tdx-api 全量API验证完成")
    print("=" * 70)


if __name__ == "__main__":
    main()
