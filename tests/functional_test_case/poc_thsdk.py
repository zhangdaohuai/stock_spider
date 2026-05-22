"""THSDK (同花顺C库Python封装) 验证脚本 (PoC)

验证thsdk库的安装和基本功能，重点测试分钟线数据获取。
项目地址: https://github.com/panghu11033/thsdk
"""

import os
import sys

for _proxy_key in [
    "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
    "ALL_PROXY", "all_proxy", "no_proxy", "NO_PROXY",
]:
    os.environ.pop(_proxy_key, None)


def test_install() -> None:
    print("=" * 80)
    print("📊 测试1: THSDK 安装验证")
    print("=" * 80)

    try:
        import thsdk
        print(f"  ✅ thsdk 已安装, 版本: {thsdk.__version__ if hasattr(thsdk, '__version__') else '未知'}")
    except ImportError:
        print("  ❌ thsdk 未安装")
        print("  安装命令: pip install --upgrade thsdk")
        return False

    try:
        from thsdk import THS
        print("  ✅ THS 类导入成功")
    except ImportError as e:
        print(f"  ❌ THS 类导入失败: {e}")
        return False

    return True


def test_connection() -> None:
    print("\n" + "=" * 80)
    print("📊 测试2: THS 连接验证(游客模式)")
    print("=" * 80)

    try:
        from thsdk import THS

        ths = THS()
        print("  ✅ THS 实例创建成功")

        ths.connect()
        print("  ✅ 连接成功(游客模式)")

        ths.disconnect()
        print("  ✅ 断开连接成功")

    except Exception as e:
        print(f"  ❌ 连接失败: {type(e).__name__}: {e}")


def test_minute_klines() -> None:
    print("\n" + "=" * 80)
    print("📊 测试3: 分钟K线数据获取")
    print("=" * 80)

    try:
        from thsdk import THS

        with THS() as ths:
            for interval, name in [
                ("1m", "1分钟"), ("5m", "5分钟"),
                ("15m", "15分钟"), ("30m", "30分钟"), ("60m", "60分钟"),
            ]:
                try:
                    response = ths.klines("USZA600519", interval=interval, count=10)
                    if response and hasattr(response, 'data') and response.data is not None:
                        df = response.data
                        rows = len(df) if hasattr(df, '__len__') else 0
                        print(f"  ✅ {name}线: {rows}条数据")
                        if rows > 0 and hasattr(df, 'head'):
                            print(f"    列: {list(df.columns)[:8]}")
                            print(f"    首行: {df.iloc[0].to_dict() if rows > 0 else 'N/A'}")
                    elif response and hasattr(response, 'error') and response.error:
                        print(f"  ❌ {name}线: {response.error}")
                    else:
                        print(f"  ⚠️ {name}线: 无数据返回")
                except Exception as e:
                    print(f"  ❌ {name}线: {type(e).__name__}: {e}")

    except Exception as e:
        print(f"  ❌ THS初始化失败: {type(e).__name__}: {e}")


def test_intraday_data() -> None:
    print("\n" + "=" * 80)
    print("📊 测试4: 日内分时数据")
    print("=" * 80)

    try:
        from thsdk import THS

        with THS() as ths:
            for code, name in [
                ("USZA600519", "贵州茅台"),
                ("USZA000858", "五粮液"),
            ]:
                try:
                    response = ths.intraday_data(code)
                    if response and hasattr(response, 'data') and response.data is not None:
                        df = response.data
                        rows = len(df) if hasattr(df, '__len__') else 0
                        print(f"  ✅ {name} 分时: {rows}条数据")
                        if rows > 0 and hasattr(df, 'columns'):
                            print(f"    列: {list(df.columns)[:8]}")
                    else:
                        print(f"  ⚠️ {name} 分时: 无数据")
                except Exception as e:
                    print(f"  ❌ {name} 分时: {type(e).__name__}: {e}")

    except Exception as e:
        print(f"  ❌ THS初始化失败: {type(e).__name__}: {e}")


def test_min_snapshot() -> None:
    print("\n" + "=" * 80)
    print("📊 测试5: 历史分时快照")
    print("=" * 80)

    try:
        from thsdk import THS

        with THS() as ths:
            for date in ["20250516", "20250515", "20250512"]:
                try:
                    response = ths.min_snapshot("USZA600519", date=date)
                    if response and hasattr(response, 'data') and response.data is not None:
                        df = response.data
                        rows = len(df) if hasattr(df, '__len__') else 0
                        print(f"  ✅ {date}: {rows}条数据")
                        if rows > 0 and hasattr(df, 'columns'):
                            print(f"    列: {list(df.columns)[:8]}")
                    else:
                        print(f"  ⚠️ {date}: 无数据")
                except Exception as e:
                    print(f"  ❌ {date}: {type(e).__name__}: {e}")

    except Exception as e:
        print(f"  ❌ THS初始化失败: {type(e).__name__}: {e}")


def test_realtime_quote() -> None:
    print("\n" + "=" * 80)
    print("📊 测试6: 实时行情数据")
    print("=" * 80)

    try:
        from thsdk import THS

        with THS() as ths:
            try:
                response = ths.quote("USZA600519")
                if response and hasattr(response, 'data') and response.data is not None:
                    df = response.data
                    rows = len(df) if hasattr(df, '__len__') else 0
                    print(f"  ✅ 贵州茅台实时行情: {rows}条")
                    if rows > 0 and hasattr(df, 'columns'):
                        print(f"    列: {list(df.columns)[:15]}")
                else:
                    print("  ⚠️ 实时行情: 无数据")
            except Exception as e:
                print(f"  ❌ 实时行情: {type(e).__name__}: {e}")

    except Exception as e:
        print(f"  ❌ THS初始化失败: {type(e).__name__}: {e}")


def main() -> None:
    if not test_install():
        print("\n⚠️ THSDK 未安装，跳过后续测试")
        print("安装命令: pip install --upgrade thsdk")
        return

    test_connection()
    test_minute_klines()
    test_intraday_data()
    test_min_snapshot()
    test_realtime_quote()

    print("\n" + "=" * 80)
    print("✅ THSDK 验证完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
