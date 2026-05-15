"""
Baostock API 能力验证 PoC 脚本
用于验证 Baostock 各核心接口的实际能力和边界
"""
import baostock as bs
import pandas as pd
import time


def test_login() -> None:
    """测试登录"""
    print("=" * 60)
    print("1. 登录测试")
    print("=" * 60)
    lg = bs.login()
    print(f"  error_code: {lg.error_code}")
    print(f"  error_msg: {lg.error_msg}")
    assert lg.error_code == "0", "登录失败"


def test_all_stock() -> None:
    """测试获取全量股票列表"""
    print()
    print("=" * 60)
    print("2. 获取全量股票列表 (query_all_stock)")
    print("=" * 60)
    rs = bs.query_all_stock(day="2025-05-13")
    df = rs.get_data()
    print(f"  总记录数: {len(df)}")
    print(f"  字段: {df.columns.tolist()}")
    sh_count = len(df[df["code"].str.startswith("sh.")])
    sz_count = len(df[df["code"].str.startswith("sz.")])
    bj_count = len(df[df["code"].str.startswith("bj.")])
    print(f"  沪市(sh): {sh_count}, 深市(sz): {sz_count}, 北交所(bj): {bj_count}")
    a_stock = df[df["code"].str.match(r"(sh\.6|sz\.0|sz\.3)")]
    print(f"  A股股票数量(6/0/3开头): {len(a_stock)}")
    print("  前5条数据:")
    print(df.head())


def test_daily_kline() -> None:
    """测试日线K线数据"""
    print()
    print("=" * 60)
    print("3. 日线K线数据测试 (query_history_k_data_plus)")
    print("=" * 60)
    rs = bs.query_history_k_data_plus(
        "sh.600000",
        "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
        start_date="2025-05-01",
        end_date="2025-05-13",
        frequency="d",
        adjustflag="3",
    )
    df = rs.get_data()
    print(f"  error_code: {rs.error_code}")
    print(f"  error_msg: {rs.error_msg}")
    print(f"  字段: {df.columns.tolist()}")
    print(f"  记录数: {len(df)}")
    print(df)


def test_5min_kline() -> None:
    """测试5分钟K线数据"""
    print()
    print("=" * 60)
    print("4. 5分钟K线数据测试")
    print("=" * 60)
    rs = bs.query_history_k_data_plus(
        "sh.600000",
        "date,time,code,open,high,low,close,volume,amount,adjustflag",
        start_date="2025-05-13",
        end_date="2025-05-13",
        frequency="5",
        adjustflag="3",
    )
    df = rs.get_data()
    print(f"  error_code: {rs.error_code}")
    print(f"  error_msg: {rs.error_msg}")
    print(f"  字段: {df.columns.tolist()}")
    print(f"  记录数: {len(df)}")
    print(df.head(10))


def test_minute_backtrack_2016() -> None:
    """测试分钟线数据回溯到2016年"""
    print()
    print("=" * 60)
    print("5. 分钟线最早数据回溯测试 (2016年)")
    print("=" * 60)
    rs = bs.query_history_k_data_plus(
        "sh.600000",
        "date,time,code,open,high,low,close,volume,amount,adjustflag",
        start_date="2016-01-04",
        end_date="2016-01-04",
        frequency="5",
        adjustflag="3",
    )
    df = rs.get_data()
    print(f"  error_code: {rs.error_code}")
    print(f"  记录数: {len(df)}")
    if len(df) > 0:
        print(f"  最早数据: {df.iloc[0].to_dict()}")
    else:
        print("  2016年分钟线数据不可用!")


def test_minute_backtrack_2019() -> None:
    """测试分钟线数据回溯到2019年"""
    print()
    print("=" * 60)
    print("6. 分钟线最早数据回溯测试 (2019年)")
    print("=" * 60)
    rs = bs.query_history_k_data_plus(
        "sh.600000",
        "date,time,code,open,high,low,close,volume,amount,adjustflag",
        start_date="2019-01-02",
        end_date="2019-01-02",
        frequency="5",
        adjustflag="3",
    )
    df = rs.get_data()
    print(f"  error_code: {rs.error_code}")
    print(f"  记录数: {len(df)}")
    if len(df) > 0:
        print(f"  最早数据: {df.iloc[0].to_dict()}")
    else:
        print("  2019年分钟线数据不可用!")


def test_isst_field() -> None:
    """测试 isST 字段"""
    print()
    print("=" * 60)
    print("7. isST 字段测试 (日线)")
    print("=" * 60)
    # 查询一只ST股票
    rs = bs.query_history_k_data_plus(
        "sh.600000",
        "date,code,close,isST",
        start_date="2025-05-01",
        end_date="2025-05-13",
        frequency="d",
        adjustflag="3",
    )
    df = rs.get_data()
    print(f"  字段: {df.columns.tolist()}")
    print(f"  isST 值分布: {df['isST'].value_counts().to_dict()}")


def test_index_no_minute() -> None:
    """测试指数是否支持分钟线"""
    print()
    print("=" * 60)
    print("8. 指数分钟线测试 (预期不支持)")
    print("=" * 60)
    rs = bs.query_history_k_data_plus(
        "sh.000001",
        "date,time,code,open,high,low,close,volume,amount,adjustflag",
        start_date="2025-05-13",
        end_date="2025-05-13",
        frequency="5",
        adjustflag="3",
    )
    df = rs.get_data()
    print(f"  error_code: {rs.error_code}")
    print(f"  error_msg: {rs.error_msg}")
    print(f"  记录数: {len(df)}")
    if len(df) == 0:
        print("  确认: 指数不支持分钟线数据")


def test_query_current_data() -> None:
    """测试实时行情接口 query_current_data"""
    print()
    print("=" * 60)
    print("9. 实时行情接口测试 (query_current_data)")
    print("=" * 60)
    # 检查是否存在该接口
    if hasattr(bs, "query_current_data"):
        rs = bs.query_current_data(code="sh.600000")
        df = rs.get_data()
        print(f"  error_code: {rs.error_code}")
        print(f"  字段: {df.columns.tolist()}")
        print(f"  记录数: {len(df)}")
        print(df)
    else:
        print("  query_current_data 接口不存在!")
        # 检查所有可用的公开方法
        public_methods = [m for m in dir(bs) if m.startswith("query_")]
        print(f"  可用的 query_ 开头的方法: {public_methods}")


def test_all_api_methods() -> None:
    """列出所有可用的 API 方法"""
    print()
    print("=" * 60)
    print("10. Baostock 所有公开 API 方法")
    print("=" * 60)
    public_methods = [m for m in dir(bs) if not m.startswith("_")]
    for m in public_methods:
        print(f"  - {m}")


def test_hk_stock() -> None:
    """测试港股数据"""
    print()
    print("=" * 60)
    print("11. 港股数据测试")
    print("=" * 60)
    # 尝试用港股代码查询
    rs = bs.query_history_k_data_plus(
        "hk.00700",
        "date,code,open,high,low,close,volume,amount",
        start_date="2025-05-01",
        end_date="2025-05-13",
        frequency="d",
        adjustflag="3",
    )
    df = rs.get_data()
    print(f"  error_code: {rs.error_code}")
    print(f"  error_msg: {rs.error_msg}")
    print(f"  记录数: {len(df)}")
    if len(df) == 0:
        print("  确认: Baostock 不支持港股数据")


def test_rate_limit() -> None:
    """测试调用频率限制"""
    print()
    print("=" * 60)
    print("12. 调用频率限制测试 (连续10次快速请求)")
    print("=" * 60)
    start_time = time.time()
    success_count = 0
    fail_count = 0
    for i in range(10):
        rs = bs.query_history_k_data_plus(
            "sh.600000",
            "date,code,close",
            start_date="2025-05-13",
            end_date="2025-05-13",
            frequency="d",
            adjustflag="3",
        )
        if rs.error_code == "0":
            success_count += 1
        else:
            fail_count += 1
            print(f"  第{i+1}次请求失败: {rs.error_msg}")
    elapsed = time.time() - start_time
    print(f"  10次请求耗时: {elapsed:.2f}秒")
    print(f"  成功: {success_count}, 失败: {fail_count}")
    print(f"  平均每次: {elapsed/10:.3f}秒")


if __name__ == "__main__":
    test_login()
    test_all_stock()
    test_daily_kline()
    test_5min_kline()
    test_minute_backtrack_2016()
    test_minute_backtrack_2019()
    test_isst_field()
    test_index_no_minute()
    test_query_current_data()
    test_all_api_methods()
    test_hk_stock()
    test_rate_limit()

    bs.logout()
    print()
    print("=" * 60)
    print("所有测试完成!")
    print("=" * 60)
