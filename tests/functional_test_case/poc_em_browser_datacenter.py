"""东方财富数据中心浏览器模式验证脚本 (PoC)

使用 DrissionPage 浏览器模式访问东方财富数据中心9个模块页面，
验证表格数据提取、搜索筛选、翻页等功能的可用性。
"""

import time
from collections.abc import Callable
from dataclasses import dataclass

from DrissionPage import ChromiumPage, ChromiumOptions

STOCK_CODE = "603288"
STOCK_NAME = "海天味业"
WAIT_TIMEOUT = 15
MODULE_INTERVAL = 3
MAX_PREVIEW_ROWS = 3


@dataclass(frozen=True)
class DataModule:
    """数据中心模块定义"""

    name: str
    url: str
    func_name: str


DATA_MODULES: list[DataModule] = [
    DataModule("龙虎榜", "https://data.eastmoney.com/stock/lhb/", "test_lhb"),
    DataModule("融资融券", "https://data.eastmoney.com/rzrq/", "test_margin"),
    DataModule("大宗交易", "https://data.eastmoney.com/dzjy/", "test_block_trade"),
    DataModule("股权质押", "https://data.eastmoney.com/gpzy/", "test_pledge"),
    DataModule("股东分析", "https://data.eastmoney.com/gdfx/", "test_shareholder"),
    DataModule("业绩报表", "https://data.eastmoney.com/bbsj/", "test_finance"),
    DataModule("分红送配", "https://data.eastmoney.com/yjfp/", "test_dividend"),
    DataModule("沪深港通", "https://data.eastmoney.com/hsgt/", "test_hsgt"),
    DataModule("研究报告", "https://data.eastmoney.com/report/", "test_research"),
]


def _print_banner(title: str) -> None:
    """打印分隔线标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def _create_headless_page() -> ChromiumPage | None:
    """创建无头浏览器页面，失败返回None"""
    try:
        co = ChromiumOptions()
        co.headless()
        co.set_argument("--no-sandbox")
        co.set_argument("--disable-gpu")
        co.set_argument("--disable-dev-shm-usage")
        page = ChromiumPage(co)
        print("  无头浏览器启动成功")
        return page
    except Exception as exc:
        print(f"  [失败] 浏览器启动异常: {exc}")
        return None


def _navigate_to(page: ChromiumPage, url: str) -> bool:
    """导航到指定URL并等待页面加载"""
    try:
        page.get(url)
        page.wait.doc_loaded(timeout=WAIT_TIMEOUT)
        time.sleep(2)
        print(f"  页面标题: {page.title}")
        print(f"  当前URL:  {page.url}")
        return True
    except Exception as exc:
        print(f"  [失败] 页面加载异常: {exc}")
        return False


def _find_data_table(page: ChromiumPage) -> ChromiumPage | None:
    """在页面中查找包含数据行的表格元素

    数据中心页面通常有多个table，需要找到有td子元素的那个。
    """
    tables = page.eles("tag:table", timeout=WAIT_TIMEOUT)
    print(f"  页面共找到 {len(tables)} 个 <table> 元素")

    for table in tables:
        rows = table.eles("tag:tr")
        # 有数据行的表格至少包含表头+1行数据
        if len(rows) >= 2:
            data_rows = [
                r for r in rows if r.eles("tag:td")
            ]
            if data_rows:
                print(f"  定位到数据表格: 共 {len(rows)} 行")
                return table

    print("  [警告] 未找到包含数据的表格")
    return None


def _extract_table_headers(table: ChromiumPage) -> list[str]:
    """提取表格的表头文本列表"""
    headers: list[str] = []
    try:
        th_elements = table.eles("tag:th")
        for th in th_elements:
            text = th.text.strip()
            if text:
                headers.append(text)
    except Exception as exc:
        print(f"  [警告] 提取表头异常: {exc}")
    return headers


def _extract_table_rows(
    table: ChromiumPage, limit: int = MAX_PREVIEW_ROWS
) -> list[list[str]]:
    """提取表格前N行数据，每行为单元格文本列表"""
    rows_data: list[list[str]] = []
    try:
        tr_elements = table.eles("tag:tr")
        data_rows = [tr for tr in tr_elements if tr.eles("tag:td")]
        for tr in data_rows[:limit]:
            cells = [td.text.strip() for td in tr.eles("tag:td")]
            cells = [c for c in cells if c]
            if cells:
                rows_data.append(cells)
    except Exception as exc:
        print(f"  [警告] 提取数据行异常: {exc}")
    return rows_data


def _print_table_preview(headers: list[str], rows: list[list[str]]) -> None:
    """格式化打印表头和数据行预览"""
    if headers:
        print(f"  表头({len(headers)}列): {' | '.join(headers[:15])}")
    if rows:
        for idx, row in enumerate(rows):
            print(f"  行{idx}: {' | '.join(row[:15])}")
    if not headers and not rows:
        print("  [警告] 表格无表头和数据")


def _try_search_stock(page: ChromiumPage) -> bool:
    """尝试在页面中搜索指定股票代码

    查找常见的搜索输入框，输入股票代码后触发筛选。
    """
    search_selectors = [
        "css:input.search-input",
        "css:input[placeholder*='代码']",
        "css:input[placeholder*='搜索']",
        "css:input[placeholder*='输入']",
        "css:#search-input",
        "css:.search input",
    ]

    search_input = None
    for selector in search_selectors:
        try:
            ele = page.ele(selector, timeout=2)
            if ele:
                search_input = ele
                break
        except Exception:
            continue

    if search_input is None:
        print("  未找到搜索输入框，跳过搜索验证")
        return False

    try:
        search_input.clear()
        search_input.input(STOCK_CODE)
        time.sleep(2)
        print(f"  已输入搜索关键词: {STOCK_CODE}")
        return True
    except Exception as exc:
        print(f"  [警告] 搜索操作异常: {exc}")
        return False


def _check_pagination(page: ChromiumPage) -> bool:
    """检查页面是否存在翻页功能"""
    pagination_selectors = [
        "css:.pagerbox",
        "css:.pagination",
        "css:.page-next",
        "css:a.next",
        "css:.pages a",
    ]

    for selector in pagination_selectors:
        try:
            ele = page.ele(selector, timeout=2)
            if ele:
                print("  发现翻页组件")
                return True
        except Exception:
            continue

    print("  未发现翻页组件")
    return False


def _run_module_test(page: ChromiumPage, module: DataModule) -> dict[str, object]:
    """执行单个模块的完整验证流程

    返回各验证项的结果字典。
    """
    result: dict[str, object] = {"模块": module.name}

    # 步骤1: 访问页面
    nav_ok = _navigate_to(page, module.url)
    result["页面加载"] = nav_ok
    if not nav_ok:
        return result

    # 步骤2: 查找数据表格
    table = _find_data_table(page)
    result["表格定位"] = table is not None
    if table is None:
        return result

    # 步骤3: 提取表头
    headers = _extract_table_headers(table)
    result["表头数量"] = len(headers)

    # 步骤4: 提取数据行
    rows = _extract_table_rows(table)
    result["数据行预览"] = len(rows)

    _print_table_preview(headers, rows)

    # 步骤5: 搜索筛选
    search_ok = _try_search_stock(page)
    result["搜索功能"] = search_ok

    # 搜索后重新提取表格验证筛选效果
    if search_ok:
        table_after = _find_data_table(page)
        if table_after:
            rows_after = _extract_table_rows(table_after)
            print(f"  搜索后数据行数: {len(rows_after)}")
            for idx, row in enumerate(rows_after[:2]):
                print(f"    行{idx}: {' | '.join(row[:10])}")

    # 步骤6: 翻页检查
    has_pagination = _check_pagination(page)
    result["翻页功能"] = has_pagination

    return result


def test_lhb(page: ChromiumPage) -> dict[str, object]:
    """验证龙虎榜模块"""
    _print_banner("验证: 龙虎榜")
    return _run_module_test(page, DATA_MODULES[0])


def test_margin(page: ChromiumPage) -> dict[str, object]:
    """验证融资融券模块"""
    _print_banner("验证: 融资融券")
    return _run_module_test(page, DATA_MODULES[1])


def test_block_trade(page: ChromiumPage) -> dict[str, object]:
    """验证大宗交易模块"""
    _print_banner("验证: 大宗交易")
    return _run_module_test(page, DATA_MODULES[2])


def test_pledge(page: ChromiumPage) -> dict[str, object]:
    """验证股权质押模块"""
    _print_banner("验证: 股权质押")
    return _run_module_test(page, DATA_MODULES[3])


def test_shareholder(page: ChromiumPage) -> dict[str, object]:
    """验证股东分析模块"""
    _print_banner("验证: 股东分析")
    return _run_module_test(page, DATA_MODULES[4])


def test_finance(page: ChromiumPage) -> dict[str, object]:
    """验证业绩报表模块"""
    _print_banner("验证: 业绩报表")
    return _run_module_test(page, DATA_MODULES[5])


def test_dividend(page: ChromiumPage) -> dict[str, object]:
    """验证分红送配模块"""
    _print_banner("验证: 分红送配")
    return _run_module_test(page, DATA_MODULES[6])


def test_hsgt(page: ChromiumPage) -> dict[str, object]:
    """验证沪深港通模块"""
    _print_banner("验证: 沪深港通")
    return _run_module_test(page, DATA_MODULES[7])


def test_research(page: ChromiumPage) -> dict[str, object]:
    """验证研究报告模块"""
    _print_banner("验证: 研究报告")
    return _run_module_test(page, DATA_MODULES[8])


# 模块名 -> 验证函数 的映射表
_TEST_FUNC_MAP: dict[str, Callable[[ChromiumPage], dict[str, object]]] = {
    "test_lhb": test_lhb,
    "test_margin": test_margin,
    "test_block_trade": test_block_trade,
    "test_pledge": test_pledge,
    "test_shareholder": test_shareholder,
    "test_finance": test_finance,
    "test_dividend": test_dividend,
    "test_hsgt": test_hsgt,
    "test_research": test_research,
}


def _print_summary(all_results: list[dict[str, object]]) -> None:
    """打印所有模块验证结果汇总"""
    _print_banner("验证结果汇总")
    print(f"{'模块':<8} {'页面加载':<8} {'表格定位':<8} {'表头数':<6} {'数据行':<6} {'搜索功能':<8} {'翻页功能':<8}")
    print("-" * 70)

    for result in all_results:
        name = str(result.get("模块", ""))
        page_ok = "通过" if result.get("页面加载") else "失败"
        table_ok = "通过" if result.get("表格定位") else "失败"
        header_cnt = str(result.get("表头数量", "-"))
        row_cnt = str(result.get("数据行预览", "-"))
        search_ok = "有" if result.get("搜索功能") else "无"
        page_ok2 = "有" if result.get("翻页功能") else "无"
        print(f"{name:<8} {page_ok:<8} {table_ok:<8} {header_cnt:<6} {row_cnt:<6} {search_ok:<8} {page_ok2:<8}")

    # 统计通过率
    loaded = sum(1 for r in all_results if r.get("页面加载"))
    tabled = sum(1 for r in all_results if r.get("表格定位"))
    total = len(all_results)
    print(f"\n  页面加载: {loaded}/{total}  表格定位: {tabled}/{total}")


def main() -> None:
    """PoC主入口: 依次验证9个数据中心模块"""
    print("东方财富数据中心浏览器模式验证")
    print(f"标的: {STOCK_NAME}({STOCK_CODE})")
    print(f"共 {len(DATA_MODULES)} 个模块待验证")

    # 启动无头浏览器
    page = _create_headless_page()
    if page is None:
        print("[失败] 无法启动浏览器，验证终止")
        return

    all_results: list[dict[str, object]] = []

    try:
        for idx, module in enumerate(DATA_MODULES):
            test_func = _TEST_FUNC_MAP.get(module.func_name)
            if test_func is None:
                print(f"  [跳过] 未找到验证函数: {module.func_name}")
                continue

            try:
                result = test_func(page)
                all_results.append(result)
            except Exception as exc:
                print(f"  [异常] {module.name}验证出错: {exc}")
                all_results.append({"模块": module.name, "页面加载": False, "异常": str(exc)})

            # 模块间间隔，避免请求过快
            if idx < len(DATA_MODULES) - 1:
                time.sleep(MODULE_INTERVAL)
    finally:
        # 确保浏览器关闭
        try:
            page.quit()
            print("\n浏览器已关闭")
        except Exception as exc:
            print(f"\n关闭浏览器异常: {exc}")

    # 打印汇总
    _print_summary(all_results)


if __name__ == "__main__":
    main()
