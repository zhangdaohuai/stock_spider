"""交易日历数据源验证脚本

验证BaoStock和AKShare的交易日历接口，
确认TradingCalendar对象的数据来源可靠性。
"""

import os

for _proxy_key in [
    "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
    "ALL_PROXY", "all_proxy",
]:
    os.environ.pop(_proxy_key, None)

import datetime


def test_baostock_calendar() -> None:
    print("=" * 60)
    print("BaoStock 交易日历接口验证")
    print("=" * 60)

    try:
        import baostock as bs

        lg = bs.login()
        if lg.error_code != "0":
            print(f"  ❌ BaoStock登录失败: {lg.error_msg}")
            return

        print(f"  ✅ BaoStock登录成功")

        # 查询2026年交易日历
        rs = bs.query_trade_dates(start_date="2026-01-01", end_date="2026-12-31")
        if rs.error_code != "0":
            print(f"  ❌ 查询失败: {rs.error_msg}")
            bs.logout()
            return

        trading_days: list[str] = []
        while rs.next():
            row = rs.get_row_data()
            is_trading = row[1] == "1"
            if is_trading:
                trading_days.append(row[0])

        print(f"  ✅ 2026年交易日: {len(trading_days)}天")
        print(f"    首个交易日: {trading_days[0] if trading_days else 'N/A'}")
        print(f"    最后交易日: {trading_days[-1] if trading_days else 'N/A'}")

        # 验证5月1-5日是否休市
        may_days = [d for d in trading_days if d.startswith("2026-05")]
        print(f"\n  2026年5月交易日({len(may_days)}天):")
        for d in may_days[:15]:
            dt = datetime.datetime.strptime(d, "%Y-%m-%d")
            weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][dt.weekday()]
            print(f"    {d} ({weekday})")

        # 验证劳动节休市
        may_holiday = ["2026-05-01", "2026-05-02", "2026-05-03",
                       "2026-05-04", "2026-05-05"]
        for d in may_holiday:
            is_holiday = d not in trading_days
            status = "✅休市" if is_holiday else "❌未休市"
            print(f"    {d}: {status}")

        # 验证周末
        print("\n  周末休市验证:")
        all_dates_2026 = []
        start = datetime.date(2026, 1, 1)
        end = datetime.date(2026, 12, 31)
        current = start
        while current <= end:
            all_dates_2026.append(current.strftime("%Y-%m-%d"))
            current += datetime.timedelta(days=1)

        weekend_trading = []
        for d in all_dates_2026:
            dt = datetime.datetime.strptime(d, "%Y-%m-%d")
            if dt.weekday() >= 5 and d in trading_days:
                weekend_trading.append(d)

        if weekend_trading:
            print(f"    ❌ 发现周末交易日: {weekend_trading}")
        else:
            print(f"    ✅ 所有周末均休市")

        # 查询2020-2025年交易日统计
        print("\n  历年交易日统计:")
        for year in range(2020, 2027):
            rs = bs.query_trade_dates(
                start_date=f"{year}-01-01",
                end_date=f"{year}-12-31",
            )
            year_trading = 0
            while rs.next():
                if rs.get_row_data()[1] == "1":
                    year_trading += 1
            print(f"    {year}: {year_trading}个交易日")

        bs.logout()

    except ImportError:
        print("  ❌ BaoStock未安装")
    except Exception as e:
        print(f"  ❌ 异常: {type(e).__name__}: {e}")


def test_akshare_calendar() -> None:
    print("\n" + "=" * 60)
    print("AKShare 交易日历接口验证")
    print("=" * 60)

    try:
        import akshare as ak

        # 新浪财经交易日历
        print("  获取新浪财经交易日历...")
        df = ak.tool_trade_date_hist_sina()
        if df is not None and len(df) > 0:
            print(f"  ✅ 获取成功: {len(df)}条记录")
            print(f"    列: {list(df.columns)}")
            print(f"    日期范围: {df.iloc[0, 0]} ~ {df.iloc[-1, 0]}")

            # 验证2026年交易日数
            if "trade_date" in df.columns:
                date_col = "trade_date"
            else:
                date_col = df.columns[0]

            year_2026 = df[df[date_col].astype(str).str.startswith("2026")]
            print(f"    2026年交易日: {len(year_2026)}天")
        else:
            print("  ❌ 无数据")

    except ImportError:
        print("  ❌ AKShare未安装")
    except Exception as e:
        print(f"  ❌ 异常: {type(e).__name__}: {e}")


def test_cross_verify() -> None:
    """用同花顺日K线交叉验证交易日历"""
    print("\n" + "=" * 60)
    print("同花顺日K线交叉验证交易日历")
    print("=" * 60)

    import json
    import re

    import requests

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://stockpage.10jqka.com.cn/",
    }

    def parse_jsonp(text: str) -> dict:
        m = re.search(r'\((\{.*\})\)', text, re.DOTALL)
        if m:
            return json.loads(m.group(1))
        return {}

    url = "http://d.10jqka.com.cn/v2/line/hs_600519/01/2026.js"
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        data = parse_jsonp(resp.text)
        raw_data = data.get("data", "")

        if isinstance(raw_data, str) and raw_data:
            lines = [l for l in raw_data.split(";") if l.strip()]
            ths_dates = set()
            for line in lines:
                date_str = line.split(",")[0]
                formatted = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                ths_dates.add(formatted)

            print(f"  同花顺日K线: {len(ths_dates)}个交易日")

            # 与BaoStock对比
            try:
                import baostock as bs

                bs.login()
                rs = bs.query_trade_dates(
                    start_date="2026-01-01", end_date="2026-12-31"
                )
                bs_dates = set()
                while rs.next():
                    row = rs.get_row_data()
                    if row[1] == "1":
                        bs_dates.add(row[0])
                bs.logout()

                print(f"  BaoStock交易日历: {len(bs_dates)}个交易日")

                # 差异分析
                only_ths = ths_dates - bs_dates
                only_bs = bs_dates - ths_dates
                common = ths_dates & bs_dates

                print(f"\n  交叉验证结果:")
                print(f"    共同交易日: {len(common)}天 ✅")
                if only_ths:
                    print(f"    仅同花顺有: {sorted(only_ths)[:5]}...")
                else:
                    print(f"    仅同花顺有: 无 ✅")
                if only_bs:
                    print(f"    仅BaoStock有: {sorted(only_bs)[:5]}...")
                else:
                    print(f"    仅BaoStock有: 无 ✅")

                if not only_ths and not only_bs:
                    print(f"\n  ✅ 同花顺与BaoStock交易日历完全一致！")
                else:
                    print(f"\n  ⚠️ 存在差异，需人工确认")

            except Exception as e:
                print(f"  ⚠️ BaoStock对比失败: {e}")

    except Exception as e:
        print(f"  ❌ 同花顺请求失败: {e}")


def main() -> None:
    test_baostock_calendar()
    test_akshare_calendar()
    test_cross_verify()

    print("\n" + "=" * 60)
    print("✅ 交易日历数据源验证完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
