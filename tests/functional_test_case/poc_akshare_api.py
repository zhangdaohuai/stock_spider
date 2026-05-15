"""
AkShare API 能力验证 PoC 脚本
用于验证 AkShare 关键接口的能力和边界限制
"""
import os
import time

# 清除代理设置，直连东方财富（AkShare底层调用东方财富API）
# 必须在 import akshare 之前清除，因此 noqa 抑制 E402 检查
for proxy_key in [
    "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
    "ALL_PROXY", "all_proxy",
]:
    os.environ.pop(proxy_key, None)

import akshare as ak  # noqa: E402  # type: ignore[import-untyped]


def test_stock_list() -> None:
    """测试 A 股全量股票列表获取"""
    print("\n[1] A股全量股票列表 - stock_info_a_code_name()")
    try:
        t0 = time.time()
        df = ak.stock_info_a_code_name()
        t1 = time.time()
        print(f"  获取成功! 股票数量: {len(df)}, 耗时: {t1-t0:.2f}s")
        print(f"  列名: {list(df.columns)}")
        print(f"  前3行:\n{df.head(3).to_string()}")
    except Exception as e:
        print(f"  失败: {e}")


def test_realtime_quote() -> None:
    """测试沪深京 A 股实时行情"""
    print("\n[2] 沪深京A股实时行情 - stock_zh_a_spot_em()")
    try:
        t0 = time.time()
        df = ak.stock_zh_a_spot_em()
        t1 = time.time()
        print(f"  获取成功! 股票数量: {len(df)}, 耗时: {t1-t0:.2f}s")
        print(f"  列名: {list(df.columns)}")
    except Exception as e:
        print(f"  失败: {e}")


def test_minute_recent() -> None:
    """测试分钟 K 线数据（近期）"""
    print("\n[3] 分钟K线数据(近期) - stock_zh_a_hist_min_em()")
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
        print(f"  列名: {list(df.columns)}")
        if len(df) > 0:
            print(f"  时间范围: {df.iloc[0, 0]} ~ {df.iloc[-1, 0]}")
    except Exception as e:
        print(f"  失败: {e}")


def test_minute_2016() -> None:
    """测试分钟 K 线数据（2016年回溯）"""
    print("\n[4] 分钟K线数据(2016年回溯) - stock_zh_a_hist_min_em()")
    try:
        t0 = time.time()
        df = ak.stock_zh_a_hist_min_em(
            symbol="000001",
            period="1",
            start_date="2016-01-04 09:30:00",
            end_date="2016-01-08 15:00:00",
            adjust=""
        )
        t1 = time.time()
        print(f"  获取成功! 数据行数: {len(df)}, 耗时: {t1-t0:.2f}s")
        if len(df) > 0:
            print(f"  时间范围: {df.iloc[0, 0]} ~ {df.iloc[-1, 0]}")
        else:
            print("  返回空数据 - 2016年分钟数据不可获取")
    except Exception as e:
        print(f"  失败(预期): {e}")


def test_daily_2016() -> None:
    """测试日线历史数据（2016年回溯）"""
    print("\n[5] 日线历史数据(2016年回溯) - stock_zh_a_hist()")
    try:
        t0 = time.time()
        df = ak.stock_zh_a_hist(
            symbol="000001",
            period="daily",
            start_date="20160101",
            end_date="20160131",
            adjust="qfq"
        )
        t1 = time.time()
        print(f"  获取成功! 数据行数: {len(df)}, 耗时: {t1-t0:.2f}s")
        if len(df) > 0:
            print(f"  前2行:\n{df.head(2).to_string()}")
    except Exception as e:
        print(f"  失败: {e}")


def test_bid_ask() -> None:
    """测试五档盘口数据"""
    print("\n[6] 五档盘口数据 - stock_bid_ask_em()")
    try:
        t0 = time.time()
        df = ak.stock_bid_ask_em(symbol="000001")
        t1 = time.time()
        print(f"  获取成功! 数据行数: {len(df)}, 耗时: {t1-t0:.2f}s")
        print(f"  列名: {list(df.columns)}")
        if len(df) > 0:
            print(f"  数据:\n{df.to_string()}")
    except Exception as e:
        print(f"  失败: {e}")


def test_st_stocks() -> None:
    """测试 ST 风险警示板"""
    print("\n[7] ST风险警示板 - stock_zh_a_st_em()")
    try:
        t0 = time.time()
        df = ak.stock_zh_a_st_em()
        t1 = time.time()
        print(f"  获取成功! ST股票数量: {len(df)}, 耗时: {t1-t0:.2f}s")
        print(f"  列名: {list(df.columns)}")
        if len(df) > 0:
            print(f"  前3行:\n{df.head(3).to_string()}")
    except Exception as e:
        print(f"  失败: {e}")


def test_delisted_stocks() -> None:
    """测试退市股票"""
    print("\n[8] 退市股票 - stock_zh_a_stop_em()")
    try:
        t0 = time.time()
        df = ak.stock_zh_a_stop_em()
        t1 = time.time()
        print(f"  获取成功! 退市股票数量: {len(df)}, 耗时: {t1-t0:.2f}s")
        if len(df) > 0:
            print(f"  前2行:\n{df.head(2).to_string()}")
    except Exception as e:
        print(f"  失败: {e}")


def test_hk_realtime() -> None:
    """测试港股实时行情"""
    print("\n[9] 港股实时行情 - stock_hk_spot_em()")
    try:
        t0 = time.time()
        df = ak.stock_hk_spot_em()
        t1 = time.time()
        print(f"  获取成功! 港股数量: {len(df)}, 耗时: {t1-t0:.2f}s")
        print(f"  列名: {list(df.columns)}")
    except Exception as e:
        print(f"  失败: {e}")


def test_hk_minute() -> None:
    """测试港股分钟数据"""
    print("\n[10] 港股分钟数据 - stock_hk_hist_min_em()")
    try:
        t0 = time.time()
        df = ak.stock_hk_hist_min_em(
            symbol="00700",
            period="5",
            adjust="",
            start_date="2025-05-10 09:30:00",
            end_date="2025-05-13 16:00:00"
        )
        t1 = time.time()
        print(f"  获取成功! 数据行数: {len(df)}, 耗时: {t1-t0:.2f}s")
        if len(df) > 0:
            print(f"  时间范围: {df.iloc[0, 0]} ~ {df.iloc[-1, 0]}")
    except Exception as e:
        print(f"  失败: {e}")


def test_minute_data_limit() -> None:
    """测试分钟数据单次最大返回条数"""
    print("\n[11] 分钟数据单次最大条数测试 - stock_zh_a_hist_min_em()")
    try:
        # 尝试获取较大范围的1分钟数据
        t0 = time.time()
        df = ak.stock_zh_a_hist_min_em(
            symbol="000001",
            period="1",
            start_date="2025-01-01 09:30:00",
            end_date="2025-05-13 15:00:00",
            adjust=""
        )
        t1 = time.time()
        print(f"  获取成功! 数据行数: {len(df)}, 耗时: {t1-t0:.2f}s")
        if len(df) > 0:
            print(f"  时间范围: {df.iloc[0, 0]} ~ {df.iloc[-1, 0]}")
    except Exception as e:
        print(f"  失败: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("AkShare API 能力验证 PoC")
    print(f"AKShare 版本: {ak.__version__}")
    print("=" * 60)

    test_stock_list()
    time.sleep(3)
    test_realtime_quote()
    time.sleep(3)
    test_minute_recent()
    time.sleep(3)
    test_minute_2016()
    time.sleep(3)
    test_daily_2016()
    time.sleep(3)
    test_bid_ask()
    time.sleep(3)
    test_st_stocks()
    time.sleep(3)
    test_delisted_stocks()
    time.sleep(3)
    test_hk_realtime()
    time.sleep(3)
    test_hk_minute()
    time.sleep(3)
    test_minute_data_limit()

    print("\n" + "=" * 60)
    print("PoC 验证完成")
    print("=" * 60)
