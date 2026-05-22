"""pytdx/mootdx 分钟线数据验证脚本 (PoC)

验证通达信协议获取A股分钟线数据的能力，
作为同花顺分钟线的替代方案。
"""

import os

for _proxy_key in [
    "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
    "ALL_PROXY", "all_proxy",
]:
    os.environ.pop(_proxy_key, None)


def test_pytdx_install() -> bool:
    print("=" * 80)
    print("📊 测试1: pytdx 安装验证")
    print("=" * 80)

    try:
        from pytdx.hq import TdxHq_API
        print("  ✅ pytdx 已安装")
        return True
    except ImportError:
        print("  ❌ pytdx 未安装")
        print("  安装命令: pip install pytdx")
        return False


def test_connection() -> None:
    print("\n" + "=" * 80)
    print("📊 测试2: 通达信服务器连接")
    print("=" * 80)

    from pytdx.hq import TdxHq_API

    servers: list[tuple[str, int, str]] = [
        ("119.147.212.81", 7709, "通达信主站1"),
        ("112.74.214.43", 7727, "通达信主站2"),
        ("221.231.141.60", 7709, "通达信主站3"),
    ]

    for host, port, name in servers:
        api = TdxHq_API()
        try:
            if api.connect(host, port):
                print(f"  ✅ {name}({host}:{port}): 连接成功")
                api.disconnect()
            else:
                print(f"  ❌ {name}({host}:{port}): 连接失败")
        except Exception as e:
            print(f"  ❌ {name}({host}:{port}): {type(e).__name__}: {e}")


def test_minute_klines() -> None:
    print("\n" + "=" * 80)
    print("📊 测试3: 分钟K线数据获取")
    print("=" * 80)

    from pytdx.hq import TdxHq_API

    # category: 0=5分钟, 1=15分钟, 2=30分钟, 3=60分钟, 4=日K, 5=周K, 6=月K, 7=1分钟, 8=1分钟
    # market: 0=深圳, 1=上海
    period_map: dict[int, str] = {
        7: "1分钟",
        0: "5分钟",
        1: "15分钟",
        2: "30分钟",
        3: "60分钟",
    }

    api = TdxHq_API()
    if not api.connect("119.147.212.81", 7709):
        print("  ❌ 连接失败")
        return

    try:
        # 贵州茅台: market=1(上海), code=600519
        for category, name in period_map.items():
            try:
                df = api.to_df(api.get_security_bars(
                    category, 1, "600519", 0, 100
                ))
                if df is not None and len(df) > 0:
                    print(f"  ✅ {name}线: {len(df)}条")
                    print(f"    列: {list(df.columns)}")
                    print(f"    时间范围: {df.iloc[0].get('datetime', 'N/A')} -> {df.iloc[-1].get('datetime', 'N/A')}")
                else:
                    print(f"  ❌ {name}线: 无数据")
            except Exception as e:
                print(f"  ❌ {name}线: {type(e).__name__}: {e}")

    finally:
        api.disconnect()


def test_minute_history_depth() -> None:
    print("\n" + "=" * 80)
    print("📊 测试4: 分钟线历史深度探测")
    print("=" * 80)

    from pytdx.hq import TdxHq_API

    api = TdxHq_API()
    if not api.connect("119.147.212.81", 7709):
        print("  ❌ 连接失败")
        return

    try:
        # 1分钟线: 通过翻页获取更早的数据
        # 每页最多800条, 起始位置0=最新, 800=前一页
        print("  1分钟线历史深度:")
        for start in [0, 800, 1600, 3200, 6400, 12800, 25600]:
            try:
                df = api.to_df(api.get_security_bars(
                    7, 1, "600519", start, 10
                ))
                if df is not None and len(df) > 0:
                    first_dt = df.iloc[0].get("datetime", "N/A")
                    print(f"    start={start}: 首条时间={first_dt}")
                else:
                    print(f"    start={start}: 无数据(已到历史尽头)")
                    break
            except Exception as e:
                print(f"    start={start}: ❌ {e}")
                break

        # 5分钟线历史深度
        print("\n  5分钟线历史深度:")
        for start in [0, 800, 1600, 3200, 6400, 12800, 25600, 51200]:
            try:
                df = api.to_df(api.get_security_bars(
                    0, 1, "600519", start, 10
                ))
                if df is not None and len(df) > 0:
                    first_dt = df.iloc[0].get("datetime", "N/A")
                    print(f"    start={start}: 首条时间={first_dt}")
                else:
                    print(f"    start={start}: 无数据(已到历史尽头)")
                    break
            except Exception as e:
                print(f"    start={start}: ❌ {e}")
                break

    finally:
        api.disconnect()


def test_history_minute_time() -> None:
    print("\n" + "=" * 80)
    print("📊 测试5: 历史分时数据(get_history_minute_time_data)")
    print("=" * 80)

    from pytdx.hq import TdxHq_API

    api = TdxHq_API()
    if not api.connect("119.147.212.81", 7709):
        print("  ❌ 连接失败")
        return

    try:
        # 历史分时数据: market=1(上海), code=600519, date=20260515
        for date in [20260516, 20260515, 20260512, 20260509, 20260102, 20250102, 20240102]:
            try:
                df = api.to_df(api.get_history_minute_time_data(1, "600519", date))
                if df is not None and len(df) > 0:
                    print(f"  ✅ {date}: {len(df)}条分时数据")
                else:
                    print(f"  ❌ {date}: 无数据")
            except Exception as e:
                print(f"  ❌ {date}: {type(e).__name__}: {e}")

    finally:
        api.disconnect()


def test_multi_stock() -> None:
    print("\n" + "=" * 80)
    print("📊 测试6: 多股票分钟线对比")
    print("=" * 80)

    from pytdx.hq import TdxHq_API

    api = TdxHq_API()
    if not api.connect("119.147.212.81", 7709):
        print("  ❌ 连接失败")
        return

    stocks: list[tuple[int, str, str]] = [
        (1, "600519", "贵州茅台"),
        (0, "000858", "五粮液"),
        (1, "603288", "海天味业"),
        (0, "000001", "平安银行"),
    ]

    try:
        for market, code, name in stocks:
            try:
                df = api.to_df(api.get_security_bars(7, market, code, 0, 50))
                if df is not None and len(df) > 0:
                    first_dt = df.iloc[0].get("datetime", "N/A")
                    last_dt = df.iloc[-1].get("datetime", "N/A")
                    print(f"  ✅ {name}({code}): {len(df)}条1分钟线, {first_dt}~{last_dt}")
                else:
                    print(f"  ❌ {name}({code}): 无数据")
            except Exception as e:
                print(f"  ❌ {name}({code}): {type(e).__name__}: {e}")

    finally:
        api.disconnect()


def main() -> None:
    if not test_pytdx_install():
        print("\n⚠️ pytdx 未安装，尝试安装...")
        os.system("pip install pytdx")
        if not test_pytdx_install():
            return

    test_connection()
    test_minute_klines()
    test_minute_history_depth()
    test_history_minute_time()
    test_multi_stock()

    print("\n" + "=" * 80)
    print("✅ pytdx 分钟线验证完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
