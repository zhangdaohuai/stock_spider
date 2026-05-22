"""通达信(TDX)分钟K线数据深度全量验证脚本

验证mootdx/pytdx通过通达信协议获取各周期分钟K线的数据深度。
重点验证1分钟线和5分钟线的历史可回溯范围。
"""

import os

for _proxy_key in [
    "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
    "ALL_PROXY", "all_proxy",
]:
    os.environ.pop(_proxy_key, None)

import time
from typing import Any

from mootdx.quotes import Quotes


_FREQUENCY_MAP: dict[int, str] = {
    0: "5分钟",
    1: "15分钟",
    2: "30分钟",
    3: "60分钟",
    4: "日K",
    5: "周K",
    6: "月K",
    7: "1分钟",
    8: "1分钟(备选)",
    9: "日K(备选)",
    10: "季K",
    11: "年K",
}

# 主板测试股票: (symbol, market, name)
# market: 0=深圳, 1=上海
_TEST_STOCKS: list[tuple[str, int, str]] = [
    ("600519", 1, "贵州茅台"),
    ("000858", 0, "五粮液"),
    ("603288", 1, "海天味业"),
    ("000001", 0, "平安银行"),
]


def test_connection() -> Quotes:
    print("=" * 70)
    print("测试1: 通达信服务器连接")
    print("=" * 70)

    client = Quotes.factory(market="std")
    print(f"  ✅ 标准行情服务器连接成功: {type(client)}")
    return client


def test_all_frequencies(client: Quotes) -> None:
    print("\n" + "=" * 70)
    print("测试2: 所有K线周期可用性验证")
    print("=" * 70)

    symbol, market, name = "600519", 1, "贵州茅台"

    for freq, freq_name in _FREQUENCY_MAP.items():
        try:
            df = client.bars(symbol=symbol, frequency=freq, offset=10)
            if df is not None and len(df) > 0:
                first_dt = str(df.index[0])
                last_dt = str(df.index[-1])
                print(f"  ✅ freq={freq:2d}({freq_name:8s}): {len(df)}条, "
                      f"{first_dt} ~ {last_dt}")
            else:
                print(f"  ❌ freq={freq:2d}({freq_name:8s}): 无数据")
        except Exception as e:
            print(f"  ❌ freq={freq:2d}({freq_name:8s}): {type(e).__name__}: {e}")
        time.sleep(0.1)


def test_minute_depth_1min(client: Quotes) -> None:
    print("\n" + "=" * 70)
    print("测试3: 1分钟K线历史深度探测(freq=8)")
    print("=" * 70)

    symbol, market, name = "600519", 1, "贵州茅台"

    # 逐步增大offset，探测数据边界
    offsets = [0, 100, 200, 400, 600, 800, 1000, 1200, 1400, 1600,
              2000, 3000, 5000, 8000, 10000, 15000, 20000]

    print(f"  {name}({symbol}) 1分钟线深度:")
    last_first_dt = ""

    for offset in offsets:
        try:
            df = client.bars(symbol=symbol, frequency=8, offset=offset + 10)
            if df is not None and len(df) > 0:
                first_dt = str(df.index[0])
                last_dt = str(df.index[-1])
                is_dup = "⚠️重复" if first_dt == last_first_dt else ""
                print(f"    offset={offset:6d}: {first_dt} ~ {last_dt} "
                      f"({len(df)}条) {is_dup}")
                if is_dup:
                    break
                last_first_dt = first_dt
            else:
                print(f"    offset={offset:6d}: 无数据(已到边界)")
                break
        except Exception as e:
            print(f"    offset={offset:6d}: ❌ {type(e).__name__}: {e}")
            break
        time.sleep(0.1)


def test_minute_depth_5min(client: Quotes) -> None:
    print("\n" + "=" * 70)
    print("测试4: 5分钟K线历史深度探测(freq=0)")
    print("=" * 70)

    symbol, market, name = "600519", 1, "贵州茅台"

    offsets = [0, 800, 1600, 3200, 6400, 12800, 25600, 51200, 102400]

    print(f"  {name}({symbol}) 5分钟线深度:")
    last_first_dt = ""

    for offset in offsets:
        try:
            df = client.bars(symbol=symbol, frequency=0, offset=offset + 10)
            if df is not None and len(df) > 0:
                first_dt = str(df.index[0])
                last_dt = str(df.index[-1])
                is_dup = "⚠️重复" if first_dt == last_first_dt else ""
                print(f"    offset={offset:7d}: {first_dt} ~ {last_dt} "
                      f"({len(df)}条) {is_dup}")
                if is_dup:
                    break
                last_first_dt = first_dt
            else:
                print(f"    offset={offset:7d}: 无数据(已到边界)")
                break
        except Exception as e:
            print(f"    offset={offset:7d}: ❌ {type(e).__name__}: {e}")
            break
        time.sleep(0.1)


def test_minute_depth_others(client: Quotes) -> None:
    print("\n" + "=" * 70)
    print("测试5: 15/30/60分钟K线历史深度")
    print("=" * 70)

    symbol, market, name = "600519", 1, "贵州茅台"

    for freq, freq_name in [(1, "15分钟"), (2, "30分钟"), (3, "60分钟")]:
        offsets = [0, 800, 3200, 12800, 51200]
        print(f"\n  {name} {freq_name}线深度:")
        last_first_dt = ""

        for offset in offsets:
            try:
                df = client.bars(symbol=symbol, frequency=freq, offset=offset + 10)
                if df is not None and len(df) > 0:
                    first_dt = str(df.index[0])
                    last_dt = str(df.index[-1])
                    is_dup = "⚠️重复" if first_dt == last_first_dt else ""
                    print(f"    offset={offset:7d}: {first_dt} ~ {last_dt} "
                          f"({len(df)}条) {is_dup}")
                    if is_dup:
                        break
                    last_first_dt = first_dt
                else:
                    print(f"    offset={offset:7d}: 无数据")
                    break
            except Exception as e:
                print(f"    offset={offset:7d}: ❌ {e}")
                break
            time.sleep(0.1)


def test_multi_stock_1min(client: Quotes) -> None:
    print("\n" + "=" * 70)
    print("测试6: 多股票1分钟线对比")
    print("=" * 70)

    for symbol, market, name in _TEST_STOCKS:
        try:
            df = client.bars(symbol=symbol, frequency=8, offset=800)
            if df is not None and len(df) > 0:
                first_dt = str(df.index[0])
                last_dt = str(df.index[-1])
                print(f"  ✅ {name}({symbol}): {len(df)}条, "
                      f"{first_dt} ~ {last_dt}")
            else:
                print(f"  ❌ {name}({symbol}): 无数据")
        except Exception as e:
            print(f"  ❌ {name}({symbol}): {type(e).__name__}: {e}")
        time.sleep(0.2)


def test_data_quality(client: Quotes) -> None:
    print("\n" + "=" * 70)
    print("测试7: 分钟线数据质量验证")
    print("=" * 70)

    symbol, market, name = "600519", 1, "贵州茅台"

    # 1分钟线数据字段
    try:
        df = client.bars(symbol=symbol, frequency=8, offset=100)
        if df is not None and len(df) > 0:
            print(f"  1分钟线字段: {list(df.columns)}")
            print(f"  数据类型:")
            for col in df.columns:
                print(f"    {col}: {df[col].dtype}")
            print(f"\n  前3条数据:")
            print(df.head(3).to_string())
            print(f"\n  末3条数据:")
            print(df.tail(3).to_string())

            # 验证每日条数
            dates = [str(idx)[:10] for idx in df.index]
            unique_dates = sorted(set(dates))
            print(f"\n  覆盖交易日: {len(unique_dates)}天")
            for d in unique_dates:
                day_count = dates.count(d)
                print(f"    {d}: {day_count}条")
        else:
            print("  ❌ 无数据")
    except Exception as e:
        print(f"  ❌ {type(e).__name__}: {e}")


def test_freq7_vs_freq8(client: Quotes) -> None:
    print("\n" + "=" * 70)
    print("测试8: freq=7 vs freq=8 对比(1分钟线)")
    print("=" * 70)

    symbol, market, name = "600519", 1, "贵州茅台"

    for freq in [7, 8]:
        try:
            df = client.bars(symbol=symbol, frequency=freq, offset=100)
            if df is not None and len(df) > 0:
                first_dt = str(df.index[0])
                last_dt = str(df.index[-1])
                print(f"  freq={freq}: {len(df)}条, {first_dt} ~ {last_dt}")
                print(f"    字段: {list(df.columns)}")
            else:
                print(f"  freq={freq}: 无数据")
        except Exception as e:
            print(f"  freq={freq}: ❌ {e}")
        time.sleep(0.2)


def main() -> None:
    print("╔" + "═" * 68 + "╗")
    print("║" + " 通达信分钟K线数据深度全量验证".center(58) + "║")
    print("║" + f" 验证日期: 2026-05-18".center(58) + "║")
    print("╚" + "═" * 68 + "╝")

    client = test_connection()
    test_all_frequencies(client)
    test_minute_depth_1min(client)
    test_minute_depth_5min(client)
    test_minute_depth_others(client)
    test_multi_stock_1min(client)
    test_data_quality(client)
    test_freq7_vs_freq8(client)

    print("\n" + "=" * 70)
    print("✅ 通达信分钟K线深度验证完成")
    print("=" * 70)


if __name__ == "__main__":
    main()
