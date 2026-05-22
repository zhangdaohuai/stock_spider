"""通达信历史分时数据深度精确验证

对之前测试中返回"无数据"的日期进行精确验证，
区分"非交易日"和"服务器无数据"两种情况。
"""

import os

for _proxy_key in [
    "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
    "ALL_PROXY", "all_proxy",
]:
    os.environ.pop(_proxy_key, None)

import datetime

from mootdx.quotes import Quotes


def is_weekend(date_str: str) -> bool:
    dt = datetime.datetime.strptime(date_str, "%Y%m%d")
    return dt.weekday() >= 5


def main() -> None:
    print("=" * 70)
    print("通达信历史分时数据深度精确验证")
    print("=" * 70)

    client = Quotes.factory(market="std")

    # 之前返回"无数据"的日期
    failed_dates: list[str] = [
        "20260505", "20260315", "20250615", "20250315",
        "20241215", "20240915", "20240615", "20230115",
        "20220115", "20200315", "20190615", "20140615",
        "20130615", "20100615",
    ]

    # 用BaoStock获取交易日历验证
    import baostock as bs

    bs.login()

    print("\n验证'无数据'日期是否为非交易日:")
    print("-" * 70)

    for date_str in failed_dates:
        is_we = is_weekend(date_str)
        dt = datetime.datetime.strptime(date_str, "%Y%m%d")
        weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][dt.weekday()]

        # BaoStock查询是否交易日
        bs_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        rs = bs.query_trade_dates(start_date=bs_date, end_date=bs_date)
        is_trading = False
        while rs.next():
            if rs.get_row_data()[1] == "1":
                is_trading = True

        # 尝试获取前后最近的交易日
        nearby_trading = ""
        for delta in range(-5, 6):
            if delta == 0:
                continue
            check_date = dt + datetime.timedelta(days=delta)
            check_str = check_date.strftime("%Y%m%d")
            rs2 = bs.query_trade_dates(
                start_date=check_date.strftime("%Y-%m-%d"),
                end_date=check_date.strftime("%Y-%m-%d"),
            )
            while rs2.next():
                if rs2.get_row_data()[1] == "1":
                    # 尝试获取这个交易日的分时数据
                    try:
                        df = client.minutes(symbol="600519", date=check_str)
                        if df is not None and len(df) > 0:
                            nearby_trading = f"✅ {check_str}有数据({len(df)}条)"
                            break
                    except Exception:
                        pass
            if nearby_trading:
                break

        status = "周末" if is_we else ("交易日" if is_trading else "非交易日(节假日)")
        print(f"  {date_str}({weekday}): {status}")
        if nearby_trading:
            print(f"    附近交易日: {nearby_trading}")

    bs.logout()

    # 深度验证: 逐月获取2020-2026年所有可用分时数据
    print("\n" + "=" * 70)
    print("逐月验证2020-2026年分时数据可用性")
    print("=" * 70)

    # 每月15日前后找交易日测试
    for year in range(2020, 2027):
        available_months = 0
        total_months = 0
        for month in range(1, 13):
            if year == 2026 and month > 5:
                continue
            total_months += 1
            # 测试每月15日
            test_date = f"{year}{month:02d}15"
            try:
                df = client.minutes(symbol="600519", date=test_date)
                if df is not None and len(df) > 0:
                    available_months += 1
                else:
                    # 尝试20日
                    test_date = f"{year}{month:02d}20"
                    df = client.minutes(symbol="600519", date=test_date)
                    if df is not None and len(df) > 0:
                        available_months += 1
            except Exception:
                pass

        print(f"  {year}: {available_months}/{total_months}个月有分时数据")

    # 最早可获取日期精确探测
    print("\n" + "=" * 70)
    print("最早可获取分时日期精确探测")
    print("=" * 70)

    # 测试2010-2012年
    for year in range(2010, 2013):
        for month in range(1, 13):
            for day in [5, 10, 15, 20, 25]:
                test_date = f"{year}{month:02d}{day:02d}"
                try:
                    df = client.minutes(symbol="600519", date=test_date)
                    if df is not None and len(df) > 0:
                        print(f"  ✅ {test_date}: {len(df)}条")
                except Exception:
                    pass

    print("\n✅ 精确验证完成")


if __name__ == "__main__":
    main()
