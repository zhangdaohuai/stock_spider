"""mootdx 分钟线数据验证脚本 (PoC)

验证mootdx库获取A股分钟线数据的能力。
"""

import os

for _proxy_key in [
    "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
    "ALL_PROXY", "all_proxy",
]:
    os.environ.pop(_proxy_key, None)

from mootdx.quotes import Quotes


def main() -> None:
    print("=" * 60)
    print("mootdx 连接与分钟线验证")
    print("=" * 60)

    client = Quotes.factory(market="std")
    print(f"连接类型: {type(client)}")

    # 1分钟线
    print("\n1分钟线 - 贵州茅台(600519):")
    try:
        df = client.bars(symbol="600519", frequency=8, offset=100)
        if df is not None and len(df) > 0:
            print(f"  ✅ {len(df)}条")
            print(f"  列: {list(df.columns)}")
            print(f"  时间范围: {df.index[0]} -> {df.index[-1]}")
        else:
            print("  ❌ 无数据")
    except Exception as e:
        print(f"  ❌ {type(e).__name__}: {e}")

    # 5分钟线
    print("\n5分钟线 - 贵州茅台(600519):")
    try:
        df = client.bars(symbol="600519", frequency=0, offset=100)
        if df is not None and len(df) > 0:
            print(f"  ✅ {len(df)}条")
            print(f"  时间范围: {df.index[0]} -> {df.index[-1]}")
        else:
            print("  ❌ 无数据")
    except Exception as e:
        print(f"  ❌ {type(e).__name__}: {e}")

    # 15/30/60分钟线
    for freq, name in [(1, "15分钟"), (2, "30分钟"), (3, "60分钟")]:
        print(f"\n{name}线 - 贵州茅台(600519):")
        try:
            df = client.bars(symbol="600519", frequency=freq, offset=100)
            if df is not None and len(df) > 0:
                print(f"  ✅ {len(df)}条")
                print(f"  时间范围: {df.index[0]} -> {df.index[-1]}")
            else:
                print("  ❌ 无数据")
        except Exception as e:
            print(f"  ❌ {type(e).__name__}: {e}")

    # 历史分时数据
    print("\n历史分时数据:")
    for date in ["20260516", "20260515", "20260102", "20250102", "20240102"]:
        try:
            df = client.minute(symbol="600519", date=date)
            if df is not None and len(df) > 0:
                print(f"  ✅ {date}: {len(df)}条")
            else:
                print(f"  ❌ {date}: 无数据")
        except Exception as e:
            print(f"  ❌ {date}: {type(e).__name__}: {e}")

    # 1分钟线历史深度
    print("\n1分钟线历史深度:")
    for offset in [0, 800, 1600, 3200, 6400, 12800, 25600]:
        try:
            df = client.bars(symbol="600519", frequency=8, offset=offset + 10)
            if df is not None and len(df) > 0:
                print(f"  offset={offset}: 首条={df.index[0]}, 末条={df.index[-1]}")
            else:
                print(f"  offset={offset}: 无数据(已到尽头)")
                break
        except Exception as e:
            print(f"  offset={offset}: ❌ {e}")
            break

    # 5分钟线历史深度
    print("\n5分钟线历史深度:")
    for offset in [0, 800, 3200, 12800, 51200, 102400]:
        try:
            df = client.bars(symbol="600519", frequency=0, offset=offset + 10)
            if df is not None and len(df) > 0:
                print(f"  offset={offset}: 首条={df.index[0]}, 末条={df.index[-1]}")
            else:
                print(f"  offset={offset}: 无数据(已到尽头)")
                break
        except Exception as e:
            print(f"  offset={offset}: ❌ {e}")
            break

    # 多股票1分钟线
    print("\n多股票1分钟线:")
    for symbol, name in [("600519", "贵州茅台"), ("000858", "五粮液"), ("603288", "海天味业")]:
        try:
            df = client.bars(symbol=symbol, frequency=8, offset=50)
            if df is not None and len(df) > 0:
                print(f"  ✅ {name}({symbol}): {len(df)}条, {df.index[0]}~{df.index[-1]}")
            else:
                print(f"  ❌ {name}({symbol}): 无数据")
        except Exception as e:
            print(f"  ❌ {name}({symbol}): {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
