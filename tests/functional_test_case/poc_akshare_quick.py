"""AkShare 关键接口快速验证脚本（带限流保护）"""
import os

for proxy_key in [
    "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
    "ALL_PROXY", "all_proxy",
]:
    os.environ.pop(proxy_key, None)

import akshare as ak
import time


def test_realtime_quote() -> None:
    print("\n[1] 沪深京A股实时行情 - stock_zh_a_spot_em()")
    try:
        t0 = time.time()
        df = ak.stock_zh_a_spot_em()
        t1 = time.time()
        print(f"  获取成功! 股票数量: {len(df)}, 耗时: {t1-t0:.2f}s")
        print(f"  列名: {list(df.columns)[:10]}...")
    except Exception as e:
        print(f"  失败: {e}")


def test_minute_recent() -> None:
    print("\n[2] 分钟K线数据(近期) - stock_zh_a_hist_min_em()")
    try:
        t0 = time.time()
        df = ak.stock_zh_a_hist_min_em(
            symbol="000001",
            period="1",
            start_date="2025-05-10 09:30:00",
            end_date="2025-05-13 15:00:00",
            adjust=""
        )
        t1 = time.time()
        print(f"  获取成功! 数据行数: {len(df)}, 耗时: {t1-t0:.2f}s")
        if len(df) > 0:
            print(f"  列名: {list(df.columns)}")
            print(f"  时间范围: {df.iloc[0, 0]} ~ {df.iloc[-1, 0]}")
        else:
            print("  返回空数据（非交易时段或超出范围）")
    except Exception as e:
        print(f"  失败: {e}")


def test_daily_recent() -> None:
    print("\n[3] 日线历史数据 - stock_zh_a_hist()")
    try:
        t0 = time.time()
        df = ak.stock_zh_a_hist(
            symbol="000001",
            period="daily",
            start_date="20260501",
            end_date="20260514",
            adjust="qfq"
        )
        t1 = time.time()
        print(f"  获取成功! 数据行数: {len(df)}, 耗时: {t1-t0:.2f}s")
        if len(df) > 0:
            print(f"  前2行:\n{df.head(2).to_string()}")
    except Exception as e:
        print(f"  失败: {e}")


def test_st_stocks() -> None:
    print("\n[4] ST风险警示板 - stock_zh_a_st_em()")
    try:
        t0 = time.time()
        df = ak.stock_zh_a_st_em()
        t1 = time.time()
        print(f"  获取成功! ST股票数量: {len(df)}, 耗时: {t1-t0:.2f}s")
    except Exception as e:
        print(f"  失败: {e}")


def test_bid_ask() -> None:
    print("\n[5] 五档盘口数据 - stock_bid_ask_em()")
    try:
        t0 = time.time()
        df = ak.stock_bid_ask_em(symbol="000001")
        t1 = time.time()
        print(f"  获取成功! 数据行数: {len(df)}, 耗时: {t1-t0:.2f}s")
    except Exception as e:
        print(f"  失败: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("AkShare 关键接口快速验证")
    print(f"AKShare 版本: {ak.__version__}")
    print("=" * 60)

    test_realtime_quote()
    time.sleep(5)
    test_minute_recent()
    time.sleep(5)
    test_daily_recent()
    time.sleep(5)
    test_st_stocks()
    time.sleep(5)
    test_bid_ask()

    print("\n" + "=" * 60)
    print("关键接口验证完成")
    print("=" * 60)
