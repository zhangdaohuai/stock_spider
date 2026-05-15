"""
Baostock API 补充验证脚本
验证分钟线回溯边界、证券基本资料、行业分类等
"""
import baostock as bs
import pandas as pd


def main() -> None:
    lg = bs.login()
    assert lg.error_code == "0", "登录失败"

    # 测试分钟线数据实际最早日期
    print("分钟线数据回溯边界测试")
    for year in [2019, 2020, 2021, 2022]:
        rs = bs.query_history_k_data_plus(
            "sh.600000",
            "date,time,code,open,high,low,close,volume,amount,adjustflag",
            start_date=f"{year}-01-02",
            end_date=f"{year}-01-31",
            frequency="5",
            adjustflag="3",
        )
        df = rs.get_data()
        print(f"  {year}年1月: {len(df)}条记录")
        if len(df) > 0:
            print(f"    最早: {df.iloc[0]['date']} {df.iloc[0]['time']}")

    # 测试 query_stock_basic
    print()
    print("证券基本资料测试 (query_stock_basic)")
    rs = bs.query_stock_basic(code="sh.600000")
    df = rs.get_data()
    print(f"  字段: {df.columns.tolist()}")
    print(df)

    # 测试 query_stock_industry
    print()
    print("行业分类测试 (query_stock_industry)")
    rs = bs.query_stock_industry(code="sh.600000")
    df = rs.get_data()
    print(f"  字段: {df.columns.tolist()}")
    print(df)

    # 测试 ST 股票日线 isST 字段
    print()
    print("ST股票 isST 字段测试")
    # 先查全量股票找一只ST
    rs_all = bs.query_all_stock(day="2025-05-13")
    df_all = rs_all.get_data()
    st_stocks = df_all[df_all["code_name"].str.contains("ST", na=False)]
    print(f"  含ST字样的股票数: {len(st_stocks)}")
    if len(st_stocks) > 0:
        st_code = st_stocks.iloc[0]["code"]
        st_name = st_stocks.iloc[0]["code_name"]
        print(f"  测试股票: {st_code} ({st_name})")
        rs = bs.query_history_k_data_plus(
            st_code,
            "date,code,close,isST",
            start_date="2025-05-01",
            end_date="2025-05-13",
            frequency="d",
            adjustflag="3",
        )
        df = rs.get_data()
        print(f"  isST 值分布: {df['isST'].value_counts().to_dict()}")

    # 测试 ETF 数据
    print()
    print("ETF 数据测试")
    rs = bs.query_history_k_data_plus(
        "sh.510050",
        "date,code,open,high,low,close,volume,amount",
        start_date="2025-05-01",
        end_date="2025-05-13",
        frequency="d",
        adjustflag="3",
    )
    df = rs.get_data()
    print(f"  error_code: {rs.error_code}")
    print(f"  记录数: {len(df)}")
    if len(df) > 0:
        print(f"  ETF日线数据可用: {df.iloc[0].to_dict()}")

    bs.logout()
    print()
    print("补充测试完成!")


if __name__ == "__main__":
    main()
