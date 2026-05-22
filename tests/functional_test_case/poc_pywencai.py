"""pywencai (同花顺问财) 验证脚本 (PoC)

验证pywencai库的安装和基本功能，测试自然语言选股查询。
项目地址: https://github.com/zsrl/pywencai
"""

import os

for _proxy_key in [
    "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
    "ALL_PROXY", "all_proxy", "no_proxy", "NO_PROXY",
]:
    os.environ.pop(_proxy_key, None)


def test_install() -> None:
    print("=" * 80)
    print("📊 测试1: pywencai 安装验证")
    print("=" * 80)

    try:
        import pywencai
        version = pywencai.__version__ if hasattr(pywencai, '__version__') else "未知"
        print(f"  ✅ pywencai 已安装, 版本: {version}")
        return True
    except ImportError:
        print("  ❌ pywencai 未安装")
        print("  安装命令: pip install pywencai")
        return False


def test_basic_query() -> None:
    print("\n" + "=" * 80)
    print("📊 测试2: 基础自然语言查询")
    print("=" * 80)

    try:
        import pywencai

        queries: list[tuple[str, str]] = [
            ("市盈率小于20", "低市盈率选股"),
            ("贵州茅台", "个股查询"),
            ("涨幅前10", "涨幅排行"),
        ]

        for query, desc in queries:
            print(f"\n  查询: {desc} -> '{query}'")
            try:
                result = pywencai.get(query=query, loop=False)
                if result is not None:
                    rows = len(result) if hasattr(result, '__len__') else 0
                    print(f"  ✅ 返回 {rows} 条数据")
                    if rows > 0 and hasattr(result, 'columns'):
                        print(f"    列: {list(result.columns)[:10]}")
                        if hasattr(result, 'head'):
                            print(f"    前3行:")
                            print(result.head(3).to_string(max_colwidth=20))
                else:
                    print("  ⚠️ 返回None")
            except Exception as e:
                print(f"  ❌ 查询失败: {type(e).__name__}: {e}")

    except ImportError:
        print("  ❌ pywencai 未安装")


def test_cookie_requirement() -> None:
    print("\n" + "=" * 80)
    print("📊 测试3: Cookie认证需求检测")
    print("=" * 80)

    try:
        import pywencai

        print("  尝试无Cookie查询...")
        try:
            result = pywencai.get(query="市盈率小于20", loop=False)
            if result is not None:
                print("  ✅ 无Cookie查询成功")
            else:
                print("  ⚠️ 无Cookie返回None，可能需要Cookie")
        except Exception as e:
            err_str = str(e)
            if "cookie" in err_str.lower() or "403" in err_str or "401" in err_str:
                print(f"  ❌ 需要Cookie认证: {err_str[:200]}")
            else:
                print(f"  ❌ 其他错误: {err_str[:200]}")

    except ImportError:
        print("  ❌ pywencai 未安装")


def test_stock_filter() -> None:
    print("\n" + "=" * 80)
    print("📊 测试4: 条件选股查询")
    print("=" * 80)

    try:
        import pywencai

        filter_queries: list[tuple[str, str]] = [
            ("连续3天涨停", "涨停选股"),
            ("换手率大于10%", "高换手率"),
            ("市净率小于1", "破净股"),
            ("ROE大于15%", "高ROE"),
        ]

        for query, desc in filter_queries:
            print(f"\n  查询: {desc} -> '{query}'")
            try:
                result = pywencai.get(query=query, loop=False)
                if result is not None:
                    rows = len(result) if hasattr(result, '__len__') else 0
                    print(f"  ✅ 返回 {rows} 条数据")
                    if rows > 0 and hasattr(result, 'columns'):
                        print(f"    列: {list(result.columns)[:8]}")
                else:
                    print("  ⚠️ 返回None")
            except Exception as e:
                print(f"  ❌ 查询失败: {type(e).__name__}: {str(e)[:100]}")

    except ImportError:
        print("  ❌ pywencai 未安装")


def main() -> None:
    if not test_install():
        print("\n⚠️ pywencai 未安装，跳过后续测试")
        print("安装命令: pip install pywencai")
        return

    test_basic_query()
    test_cookie_requirement()
    test_stock_filter()

    print("\n" + "=" * 80)
    print("✅ pywencai 验证完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
