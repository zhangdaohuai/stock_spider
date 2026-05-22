"""通达信(TDX)历史分时数据深度验证脚本

验证mootdx/pytdx的get_history_minute_time_data接口，
探测历史分时数据的可回溯范围。
这是获取1分钟线历史数据的关键接口。
"""

import os

for _proxy_key in [
    "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
    "ALL_PROXY", "all_proxy",
]:
    os.environ.pop(_proxy_key, None)

import datetime
import time

from mootdx.quotes import Quotes


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
    print(f"  ✅ 连接成功")
    return client


def test_current_minute(client: Quotes) -> None:
    print("\n" + "=" * 70)
    print("测试2: 当日分时数据(minute)")
    print("=" * 70)

    for symbol, market, name in _TEST_STOCKS:
        try:
            df = client.minute(symbol=symbol)
            if df is not None and len(df) > 0:
                print(f"  ✅ {name}({symbol}): {len(df)}条")
                print(f"    字段: {list(df.columns)}")
                print(f"    首条: {df.iloc[0].to_dict()}")
                print(f"    末条: {df.iloc[-1].to_dict()}")
            else:
                print(f"  ❌ {name}({symbol}): 无数据(非交易时间?)")
        except Exception as e:
            print(f"  ❌ {name}({symbol}): {type(e).__name__}: {e}")
        time.sleep(0.2)


def test_history_minute_recent(client: Quotes) -> None:
    print("\n" + "=" * 70)
    print("测试3: 近期历史分时数据")
    print("=" * 70)

    symbol, market, name = "600519", 1, "贵州茅台"

    # 最近10个交易日的日期
    today = datetime.date(2026, 5, 18)
    test_dates: list[str] = []

    current = today
    while len(test_dates) < 10:
        if current.weekday() < 5:
            test_dates.append(current.strftime("%Y%m%d"))
        current -= datetime.timedelta(days=1)

    for date_str in test_dates:
        try:
            df = client.minutes(symbol=symbol, date=date_str)
            if df is not None and len(df) > 0:
                print(f"  ✅ {date_str}: {len(df)}条")
            else:
                print(f"  ❌ {date_str}: 无数据")
        except Exception as e:
            print(f"  ❌ {date_str}: {type(e).__name__}: {e}")
        time.sleep(0.1)


def test_history_minute_deep(client: Quotes) -> None:
    print("\n" + "=" * 70)
    print("测试4: 历史分时数据深度探测(逐月)")
    print("=" * 70)

    symbol, market, name = "600519", 1, "贵州茅台"

    test_dates: list[str] = []
    for year in range(2026, 2019, -1):
        for month in [12, 9, 6, 3, 1]:
            if year == 2026 and month > 5:
                continue
            date_str = f"{year}{month:02d}15"
            test_dates.append(date_str)

    print(f"  {name}({symbol}) 历史分时深度:")
    earliest_success = ""

    for date_str in test_dates:
        try:
            df = client.minutes(symbol=symbol, date=date_str)
            if df is not None and len(df) > 0:
                earliest_success = date_str
                print(f"  ✅ {date_str}: {len(df)}条")
            else:
                print(f"  ❌ {date_str}: 无数据")
        except Exception as e:
            err_str = str(e)
            print(f"  ❌ {date_str}: {err_str[:80]}")
        time.sleep(0.1)

    if earliest_success:
        print(f"\n  📊 最早可获取的历史分时日期: {earliest_success}")


def test_history_minute_early_years(client: Quotes) -> None:
    print("\n" + "=" * 70)
    print("测试5: 早期年份历史分时探测(2010-2019)")
    print("=" * 70)

    symbol, market, name = "600519", 1, "贵州茅台"

    test_dates: list[str] = []
    for year in range(2019, 2009, -1):
        date_str = f"{year}0615"
        test_dates.append(date_str)

    for date_str in test_dates:
        try:
            df = client.minutes(symbol=symbol, date=date_str)
            if df is not None and len(df) > 0:
                print(f"  ✅ {date_str}: {len(df)}条")
            else:
                print(f"  ❌ {date_str}: 无数据")
        except Exception as e:
            err_str = str(e)
            print(f"  ❌ {date_str}: {err_str[:80]}")
        time.sleep(0.1)


def test_history_minute_data_quality(client: Quotes) -> None:
    print("\n" + "=" * 70)
    print("测试6: 历史分时数据质量分析")
    print("=" * 70)

    symbol, market, name = "600519", 1, "贵州茅台"

    # 取一个确定有数据的日期
    test_date = "20260515"

    try:
        df = client.minutes(symbol=symbol, date=test_date)
        if df is not None and len(df) > 0:
            print(f"  {name} {test_date} 分时数据:")
            print(f"    总条数: {len(df)}")
            print(f"    字段: {list(df.columns)}")
            print(f"    数据类型:")
            for col in df.columns:
                print(f"      {col}: {df[col].dtype}")
            print(f"\n    前5条:")
            print(df.head(5).to_string())
            print(f"\n    末5条:")
            print(df.tail(5).to_string())

            # 与1分钟K线对比
            print(f"\n  与1分钟K线对比:")
            df_kline = client.bars(symbol=symbol, frequency=8, offset=240)
            if df_kline is not None and len(df_kline) > 0:
                kline_dates = [str(idx)[:10] for idx in df_kline.index]
                target_klines = df_kline[[str(idx)[:10] == "2026-05-15"
                                          for idx in df_kline.index]]
                if len(target_klines) > 0:
                    print(f"    1分钟K线({test_date}): {len(target_klines)}条")
                    print(f"    K线字段: {list(target_klines.columns)}")
                    print(f"    K线首条: {target_klines.iloc[0].to_dict()}")
                else:
                    print(f"    1分钟K线无{test_date}数据")
        else:
            print(f"  ❌ {test_date}: 无数据")
    except Exception as e:
        print(f"  ❌ {type(e).__name__}: {e}")


def test_multi_stock_history(client: Quotes) -> None:
    print("\n" + "=" * 70)
    print("测试7: 多股票历史分时对比")
    print("=" * 70)

    test_date = "20260515"

    for symbol, market, name in _TEST_STOCKS:
        try:
            df = client.minutes(symbol=symbol, date=test_date)
            if df is not None and len(df) > 0:
                print(f"  ✅ {name}({symbol}) {test_date}: {len(df)}条")
            else:
                print(f"  ❌ {name}({symbol}) {test_date}: 无数据")
        except Exception as e:
            print(f"  ❌ {name}({symbol}): {type(e).__name__}: {e}")
        time.sleep(0.1)


def test_ext_market(client: Quotes) -> None:
    print("\n" + "=" * 70)
    print("测试8: 扩展行情服务器(7727端口)分钟线深度")
    print("=" * 70)

    try:
        ext_client = Quotes.factory(market="ext")
        print(f"  ✅ 扩展行情连接成功: {type(ext_client)}")

        # 对比1分钟线深度
        symbol, market, name = "600519", 1, "贵州茅台"

        print(f"\n  扩展行情1分钟线:")
        for offset in [0, 800, 1600, 3200]:
            try:
                df = ext_client.bars(symbol=symbol, frequency=8, offset=offset + 10)
                if df is not None and len(df) > 0:
                    first_dt = str(df.index[0])
                    print(f"    offset={offset}: {first_dt} ({len(df)}条)")
                else:
                    print(f"    offset={offset}: 无数据")
                    break
            except Exception as e:
                print(f"    offset={offset}: ❌ {e}")
                break
            time.sleep(0.1)

    except Exception as e:
        print(f"  ❌ 扩展行情连接失败: {type(e).__name__}: {e}")


def main() -> None:
    print("╔" + "═" * 68 + "╗")
    print("║" + " 通达信历史分时数据深度验证".center(58) + "║")
    print("║" + f" 验证日期: 2026-05-18".center(58) + "║")
    print("╚" + "═" * 68 + "╝")

    client = test_connection()
    test_current_minute(client)
    test_history_minute_recent(client)
    test_history_minute_deep(client)
    test_history_minute_early_years(client)
    test_history_minute_data_quality(client)
    test_multi_stock_history(client)
    test_ext_market(client)

    print("\n" + "=" * 70)
    print("✅ 通达信历史分时深度验证完成")
    print("=" * 70)


if __name__ == "__main__":
    main()
