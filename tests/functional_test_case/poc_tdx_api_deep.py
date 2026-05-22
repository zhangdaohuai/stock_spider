"""tdx-api 关键接口深度验证

针对全量验证中发现的问题进行深度测试：
1. kline-all接口为何返回空数据
2. 1分钟K线深度是否真的有5个月
3. 历史分时哪些日期无数据(是否为非交易日)
4. trade-history/full接口
5. workday/range参数格式
"""

import os

for _proxy_key in [
    "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
    "ALL_PROXY", "all_proxy",
]:
    os.environ.pop(_proxy_key, None)

import json
import time

import requests

BASE_URL = "http://localhost:8080"


def _get(path: str, params: dict | None = None) -> dict:
    resp = requests.get(f"{BASE_URL}{path}", params=params, timeout=60)
    return resp.json()


def _post(path: str, data: dict | None = None) -> dict:
    resp = requests.post(f"{BASE_URL}{path}", json=data, timeout=60)
    return resp.json()


def test_kline_minute1_depth() -> None:
    print("=" * 70)
    print("测试1: 1分钟K线深度精确验证")
    print("=" * 70)

    data = _get("/api/kline", {"code": "600519", "type": "minute1"})
    if data.get("code") == 0:
        items = data.get("data", {}).get("List", [])
        count = data.get("data", {}).get("Count", 0)
        print(f"  总条数: {count}")

        if items:
            # 按日统计
            dates: dict[str, int] = {}
            for item in items:
                dt = item.get("Time", "")[:10]
                dates[dt] = dates.get(dt, 0) + 1

            print(f"  覆盖天数: {len(dates)}")
            print(f"  最早日期: {sorted(dates.keys())[0]}")
            print(f"  最新日期: {sorted(dates.keys())[-1]}")

            # 显示每天的条数
            print(f"\n  每日条数统计:")
            for dt in sorted(dates.keys()):
                print(f"    {dt}: {dates[dt]}条")


def test_kline_minute5_depth() -> None:
    print("\n" + "=" * 70)
    print("测试2: 5分钟K线深度精确验证")
    print("=" * 70)

    data = _get("/api/kline", {"code": "600519", "type": "minute5"})
    if data.get("code") == 0:
        items = data.get("data", {}).get("List", [])
        count = data.get("data", {}).get("Count", 0)
        print(f"  总条数: {count}")

        if items:
            dates: dict[str, int] = {}
            for item in items:
                dt = item.get("Time", "")[:10]
                dates[dt] = dates.get(dt, 0) + 1

            print(f"  覆盖天数: {len(dates)}")
            print(f"  最早日期: {sorted(dates.keys())[0]}")
            print(f"  最新日期: {sorted(dates.keys())[-1]}")


def test_minute_non_trading_days() -> None:
    print("\n" + "=" * 70)
    print("测试3: 分时数据'无数据'日期分析(是否为非交易日)")
    print("=" * 70)

    # 之前返回无数据的日期
    failed_dates = [
        "20240615", "20230115", "20190615", "20100615",
    ]

    for date in failed_dates:
        # 先查是否交易日
        wd = _get("/api/workday", {"date": date})
        is_workday = wd.get("data", {}).get("is_workday", None)

        # 获取分时数据
        minute = _get("/api/minute", {"code": "600519", "date": date})
        items = minute.get("data", {}).get("List") or []
        actual_date = minute.get("data", {}).get("date", "N/A")

        # 尝试前后5天
        nearby = ""
        if not items:
            import datetime
            dt = datetime.datetime.strptime(date, "%Y%m%d")
            for delta in range(-5, 6):
                if delta == 0:
                    continue
                check = dt + datetime.timedelta(days=delta)
                check_str = check.strftime("%Y%m%d")
                m = _get("/api/minute", {"code": "600519", "date": check_str})
                m_items = m.get("data", {}).get("List", [])
                if m_items:
                    nearby = f"附近有数据: {check_str}({len(m_items)}条)"
                    break

        print(f"  {date}: 交易日={is_workday}, 分时={len(items)}条, "
              f"实际日期={actual_date}")
        if nearby:
            print(f"    {nearby}")
        time.sleep(0.2)


def test_workday_range_formats() -> None:
    print("\n" + "=" * 70)
    print("测试4: workday/range 不同参数格式")
    print("=" * 70)

    formats = [
        {"start": "20260501", "end": "20260515"},
        {"start": "2026-05-01", "end": "2026-05-15"},
    ]

    for params in formats:
        data = _get("/api/workday/range", params)
        wd_data = data.get("data", {})
        days = wd_data.get("workdays", [])
        count = wd_data.get("count", 0)
        print(f"  参数{params}: {count}个交易日, workdays={days[:5]}")


def test_pull_kline_and_check() -> None:
    print("\n" + "=" * 70)
    print("测试5: pull-kline任务 + kline-all验证")
    print("=" * 70)

    # 尝试不同的tables参数格式
    table_formats = [
        ["minute1"],
        ["1minute"],
        ["minute"],
        ["m1"],
    ]

    for tables in table_formats:
        data = _post("/api/tasks/pull-kline", {
            "codes": ["600519"],
            "tables": tables,
            "limit": 1,
        })
        status = "✅" if data.get("code") == 0 else "❌"
        print(f"  tables={tables}: {status} {data.get('message', data.get('data', 'N/A'))}")
        time.sleep(0.3)

    # 尝试日K线
    data = _post("/api/tasks/pull-kline", {
        "codes": ["600519"],
        "tables": ["day"],
        "limit": 1,
    })
    if data.get("code") == 0:
        task_id = data.get("data", {}).get("task_id", "")
        print(f"  ✅ 日K线任务创建: {task_id}")

        # 等待任务完成
        for _ in range(10):
            time.sleep(3)
            task = _get(f"/api/tasks/{task_id}")
            task_data = task.get("data", {})
            status = task_data.get("status", "N/A")
            print(f"    状态: {status}")
            if status in ("success", "failed", "cancelled"):
                break

        # 检查kline-all是否可用
        data2 = _get("/api/kline-all", {"code": "600519", "type": "day"})
        items2 = data2.get("data", {}).get("List", [])
        count2 = data2.get("data", {}).get("Count", 0)
        print(f"  kline-all(day)结果: {count2}条")
    else:
        print(f"  ❌ 日K线任务: {data.get('message', 'N/A')}")


def test_trade_history_full() -> None:
    print("\n" + "=" * 70)
    print("测试6: trade-history/full 深度验证")
    print("=" * 70)

    # 尝试不同参数
    params_list = [
        {"code": "600519", "limit": 50},
        {"code": "600519", "before": "20260515", "limit": 50},
        {"code": "600519"},
    ]

    for params in params_list:
        data = _get("/api/trade-history/full", params)
        if data.get("code") == 0:
            items = data.get("data", {}).get("List", [])
            count = data.get("data", {}).get("Count", 0)
            if items:
                first_time = items[0].get("Time", "N/A")[:19]
                last_time = items[-1].get("Time", "N/A")[:19]
                print(f"  ✅ {params}: {count}条, {first_time} ~ {last_time}")
            else:
                print(f"  ❌ {params}: 无数据(count={count})")
        else:
            print(f"  ❌ {params}: {data.get('message', 'N/A')}")
        time.sleep(0.3)


def test_kline_history_date_range() -> None:
    print("\n" + "=" * 70)
    print("测试7: kline-history 日期范围查询")
    print("=" * 70)

    # 1分钟K线指定日期范围
    data = _get("/api/kline-history", {
        "code": "600519", "type": "minute1",
        "start_date": "20260501", "end_date": "20260515",
    })
    if data.get("code") == 0:
        items = data.get("data", {}).get("List", [])
        if items:
            first_time = items[0].get("Time", "N/A")[:19]
            last_time = items[-1].get("Time", "N/A")[:19]
            print(f"  ✅ 1分钟K线(5月1-15日): {len(items)}条, "
                  f"{first_time} ~ {last_time}")
        else:
            print(f"  ❌ 1分钟K线(5月1-15日): 无数据")

    # 5分钟K线指定日期范围
    data = _get("/api/kline-history", {
        "code": "600519", "type": "minute5",
        "start_date": "20200101", "end_date": "20200131",
    })
    if data.get("code") == 0:
        items = data.get("data", {}).get("List", [])
        if items:
            first_time = items[0].get("Time", "N/A")[:19]
            last_time = items[-1].get("Time", "N/A")[:19]
            print(f"  ✅ 5分钟K线(2020-01): {len(items)}条, "
                  f"{first_time} ~ {last_time}")
        else:
            print(f"  ❌ 5分钟K线(2020-01): 无数据")


def test_data_quality() -> None:
    print("\n" + "=" * 70)
    print("测试8: 数据质量对比(kline vs minute)")
    print("=" * 70)

    # 获取20260515的1分钟K线
    data_kline = _get("/api/kline-history", {
        "code": "600519", "type": "minute1",
        "start_date": "20260515", "end_date": "20260516",
    })
    # 获取20260515的分时数据
    data_minute = _get("/api/minute", {"code": "600519", "date": "20260515"})

    kline_items = data_kline.get("data", {}).get("List", [])
    minute_items = data_minute.get("data", {}).get("List", [])

    print(f"  1分钟K线条数: {len(kline_items)}")
    print(f"  分时数据条数: {len(minute_items)}")

    if kline_items and minute_items:
        # 对比第一条
        k_first = kline_items[-1]  # K线是倒序
        m_first = minute_items[0]
        print(f"\n  1分钟K线首条: 时间={k_first.get('Time','')[:19]}, "
              f"开={k_first.get('Open',0)/1000:.2f}, "
              f"高={k_first.get('High',0)/1000:.2f}, "
              f"低={k_first.get('Low',0)/1000:.2f}, "
              f"收={k_first.get('Close',0)/1000:.2f}, "
              f"量={k_first.get('Volume',0)}")
        print(f"  分时首条:     时间={m_first.get('Time','')}, "
              f"价={m_first.get('Price',0)/1000:.2f}, "
              f"量={m_first.get('Number',0)}")

        # 对比最后一条
        k_last = kline_items[0]
        m_last = minute_items[-1]
        print(f"\n  1分钟K线末条: 时间={k_last.get('Time','')[:19]}, "
              f"收={k_last.get('Close',0)/1000:.2f}")
        print(f"  分时末条:     时间={m_last.get('Time','')}, "
              f"价={m_last.get('Price',0)/1000:.2f}")


def main() -> None:
    print("╔" + "═" * 68 + "╗")
    print("║" + " tdx-api 关键接口深度验证".center(50) + "║")
    print("╚" + "═" * 68 + "╝")

    test_kline_minute1_depth()
    test_kline_minute5_depth()
    test_minute_non_trading_days()
    test_workday_range_formats()
    test_pull_kline_and_check()
    test_trade_history_full()
    test_kline_history_date_range()
    test_data_quality()

    print("\n" + "=" * 70)
    print("✅ tdx-api 深度验证完成")
    print("=" * 70)


if __name__ == "__main__":
    main()
