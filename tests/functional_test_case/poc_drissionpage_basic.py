"""DrissionPage 基础功能验证脚本 (PoC)

验证 DrissionPage 能否正常启动浏览器、访问东方财富行情页并提取数据。
"""

import time

from DrissionPage import ChromiumPage, ChromiumOptions

TARGET_URL = "https://quote.eastmoney.com/sh603288.html"
STOCK_CODE = "603288"
WAIT_TIMEOUT = 10


def _print_banner(title: str) -> None:
    """打印分隔线标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def _safe_get_text(page: ChromiumPage, selector: str) -> str:
    """安全获取元素文本，失败返回空字符串"""
    try:
        ele = page.ele(selector, timeout=WAIT_TIMEOUT)
        return ele.text.strip() if ele else ""
    except Exception:
        return ""


def test_install() -> bool:
    """验证1: DrissionPage 安装及版本号"""
    _print_banner("验证1: DrissionPage 安装验证")
    try:
        import DrissionPage as dp
        version = getattr(dp, "__version__", "未知")
        print(f"  DrissionPage 版本: {version}")
        print("  核心模块导入成功: ChromiumPage, ChromiumOptions")
        print("  [通过] 安装验证通过")
        return True
    except ImportError as e:
        print(f"  [失败] 导入失败: {e}")
        return False


def test_headless_launch() -> ChromiumPage | None:
    """验证2: 无头模式启动 Chrome 浏览器"""
    _print_banner("验证2: 无头模式启动 Chrome")
    try:
        co = ChromiumOptions()
        co.headless()
        co.set_argument("--no-sandbox")
        co.set_argument("--disable-gpu")
        co.set_argument("--disable-dev-shm-usage")

        page = ChromiumPage(co)
        print(f"  浏览器启动成功, 用户代理:")
        ua = page.ele("tag:head", timeout=5)
        print(f"  页面对象已创建: {type(page).__name__}")
        print("  [通过] 无头模式启动成功")
        return page
    except Exception as e:
        print(f"  [失败] 启动失败: {e}")
        return None


def test_visit_page(page: ChromiumPage) -> bool:
    """验证3: 访问东方财富行情页"""
    _print_banner("验证3: 访问东方财富行情页")
    if page is None:
        print("  [跳过] 浏览器未启动")
        return False
    try:
        page.get(TARGET_URL)
        # 等待动态内容加载
        page.wait.doc_loaded(timeout=WAIT_TIMEOUT)
        time.sleep(2)

        title = page.title
        current_url = page.url
        print(f"  页面标题: {title}")
        print(f"  当前URL:  {current_url}")
        print("  [通过] 页面访问成功")
        return True
    except Exception as e:
        print(f"  [失败] 访问失败: {e}")
        return False


def test_extract_elements(page: ChromiumPage) -> bool:
    """验证4: 提取股票名称、当前价格等基本元素"""
    _print_banner("验证4: 提取页面基本元素")
    if page is None:
        print("  [跳过] 浏览器未启动")
        return False
    try:
        # 尝试多种选择器定位股票名称
        stock_name = _safe_get_text(page, "css:.quote_title_name")
        if not stock_name:
            stock_name = _safe_get_text(page, "css:#name")
        if not stock_name:
            # 备用: 通过 title 元素提取
            title_text = page.title
            if STOCK_CODE in title_text:
                stock_name = title_text.split("-")[0].strip()

        # 尝试提取当前价格
        current_price = _safe_get_text(page, "css:#price")
        if not current_price:
            current_price = _safe_get_text(page, "css:.quote_title_price")

        # 尝试提取涨跌幅
        change_pct = _safe_get_text(page, "css:#changepercent")
        if not change_pct:
            change_pct = _safe_get_text(page, "css:.quote_title_change")

        print(f"  股票名称: {stock_name or '未提取到'}")
        print(f"  当前价格: {current_price or '未提取到'}")
        print(f"  涨跌幅:   {change_pct or '未提取到'}")

        if stock_name or current_price:
            print("  [通过] 基本元素提取成功")
            return True
        else:
            print("  [警告] 未能提取到关键元素，页面结构可能变化")
            return False
    except Exception as e:
        print(f"  [失败] 提取失败: {e}")
        return False


def test_extract_table(page: ChromiumPage) -> bool:
    """验证5: 提取行情表格数据"""
    _print_banner("验证5: 提取行情表格数据")
    if page is None:
        print("  [跳过] 浏览器未启动")
        return False
    try:
        # 尝试定位页面中的数据表格
        tables = page.eles("tag:table", timeout=WAIT_TIMEOUT)
        print(f"  页面中共找到 {len(tables)} 个 <table> 元素")

        if tables:
            # 取第一个有内容的表格展示
            for idx, table in enumerate(tables[:3]):
                rows = table.eles("tag:tr")
                if not rows:
                    continue
                print(f"\n  表格 {idx + 1} (共 {len(rows)} 行):")
                # 只展示前5行避免输出过长
                for row in rows[:5]:
                    cells = row.eles("tag:td")
                    if not cells:
                        cells = row.eles("tag:th")
                    cell_texts = [c.text.strip() for c in cells if c.text.strip()]
                    if cell_texts:
                        print(f"    {' | '.join(cell_texts)}")

        # 尝试提取行情详情面板（东方财富常用 div 结构）
        detail_items = page.eles("css:.quote_info_detail li", timeout=5)
        if detail_items:
            print(f"\n  行情详情面板共 {len(detail_items)} 项:")
            for item in detail_items[:8]:
                print(f"    {item.text.strip()}")

        if tables or detail_items:
            print("\n  [通过] 表格数据提取成功")
            return True
        else:
            print("  [警告] 未找到表格或详情面板，页面结构可能变化")
            return False
    except Exception as e:
        print(f"  [失败] 表格提取失败: {e}")
        return False


def main() -> None:
    """PoC 主入口：依次执行5项验证"""
    results: dict[str, bool] = {}
    page: ChromiumPage | None = None

    # 验证1: 安装检查
    results["安装验证"] = test_install()
    time.sleep(1)

    # 验证2: 无头启动
    page = test_headless_launch()
    results["无头启动"] = page is not None
    time.sleep(1)

    # 验证3: 访问页面
    results["页面访问"] = test_visit_page(page)
    time.sleep(1)

    # 验证4: 提取基本元素
    results["元素提取"] = test_extract_elements(page)
    time.sleep(1)

    # 验证5: 提取表格数据
    results["表格提取"] = test_extract_table(page)

    # 关闭浏览器
    if page is not None:
        try:
            page.quit()
            print("\n  浏览器已关闭")
        except Exception as e:
            print(f"\n  关闭浏览器异常: {e}")

    # 汇总报告
    _print_banner("验证结果汇总")
    for name, passed in results.items():
        status = "通过" if passed else "失败"
        print(f"  {name}: {status}")

    total = len(results)
    passed_count = sum(1 for v in results.values() if v)
    print(f"\n  总计: {passed_count}/{total} 项通过")


if __name__ == "__main__":
    main()
