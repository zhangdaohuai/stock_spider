"""东方财富行情主页浏览器模式验证脚本 — 替代被IP封锁的push2 API

使用 DrissionPage 浏览器模式访问东方财富行情页，验证能否通过
DOM提取 + JS执行的方式获取实时行情、K线、分时、盘口、资金流向数据。
"""

import os
import time

# 清除代理设置，直连东方财富
for _key in [
    "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
    "ALL_PROXY", "all_proxy",
]:
    os.environ.pop(_key, None)

from DrissionPage import ChromiumPage, ChromiumOptions  # noqa: E402


# ---------- 常量 ----------

STOCK_CODE = "603288"
STOCK_NAME = "海天味业"
QUOTE_URL = "https://quote.eastmoney.com/sh603288.html"
WAIT_SECONDS = 2


# ---------- 工具函数 ----------

def _print_banner(title: str) -> None:
    """打印分隔线和标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def _safe_text(page: ChromiumPage, selector: str) -> str:
    """安全获取元素文本，失败返回空字符串"""
    try:
        ele = page.ele(selector, timeout=5)
        return ele.text.strip() if ele else ""
    except Exception:
        return ""


def _safe_click(page: ChromiumPage, selector: str) -> bool:
    """安全点击元素，返回是否成功"""
    try:
        ele = page.ele(selector, timeout=5)
        if ele:
            ele.click()
            time.sleep(WAIT_SECONDS)
            return True
        return False
    except Exception:
        return False


# ---------- 验证1: 实时行情数据提取 ----------

def test_realtime_quote(page: ChromiumPage) -> None:
    """验证1: 从行情页提取实时行情数据

    行情页为SPA，数据通过JS动态加载，需等待元素出现。
    尝试多种选择器策略定位关键数据字段。
    """
    _print_banner(f"验证1: 实时行情 — {STOCK_NAME}({STOCK_CODE})")

    try:
        # 提取股票名称 — 通常在页面顶部标题区域
        name_selectors = [
            ".stock-name",
            ".quote-title_name",
            "[class*='stockName']",
            ".title_name",
        ]
        name = ""
        for sel in name_selectors:
            name = _safe_text(page, sel)
            if name:
                print(f"  [成功] 股票名称: {name} (选择器: {sel})")
                break
        if not name:
            print("  [失败] 未能提取股票名称，尝试JS方式...")
            name = page.run_js(
                "return document.querySelector('.stock-name, .quote-title_name, "
                "[class*=\"stockName\"]')?.textContent?.trim() || ''"
            ) or ""
            if name:
                print(f"  [成功-JS] 股票名称: {name}")
            else:
                print("  [失败] JS方式也未提取到股票名称")

        # 提取当前价格 — 通常为醒目的大字体数字
        price_selectors = [
            ".last-price",
            ".quote-current_price",
            "[class*='currentPrice']",
            ".price",
        ]
        price = ""
        for sel in price_selectors:
            price = _safe_text(page, sel)
            if price:
                print(f"  [成功] 当前价格: {price} (选择器: {sel})")
                break
        if not price:
            # 尝试通过JS获取所有疑似价格的大字体元素
            price = page.run_js(
                "return document.querySelector('.last-price, .quote-current_price, "
                "[class*=\"currentPrice\"]')?.textContent?.trim() || ''"
            ) or ""
            if price:
                print(f"  [成功-JS] 当前价格: {price}")
            else:
                print("  [失败] 未能提取当前价格")

        # 提取涨跌额和涨跌幅
        _extract_change_info(page)

        # 提取成交量和成交额
        _extract_volume_info(page)

        # 提取换手率等指标
        _extract_extra_indicators(page)

    except Exception as exc:
        print(f"  [异常] 实时行情提取失败: {exc}")


def _extract_change_info(page: ChromiumPage) -> None:
    """提取涨跌额、涨跌幅信息"""
    change_selectors = [
        ".quote-change",
        "[class*='change']",
        ".price-change",
    ]
    for sel in change_selectors:
        text = _safe_text(page, sel)
        if text:
            print(f"  [成功] 涨跌信息: {text} (选择器: {sel})")
            return

    # JS兜底: 查找包含"涨跌"或百分号的元素
    js_result = page.run_js(
        "const els = document.querySelectorAll('[class*=\"change\"], [class*=\"Change\"]');"
        "let texts = [];"
        "els.forEach(e => { if(e.textContent.trim()) texts.push(e.textContent.trim()); });"
        "return texts.slice(0, 5);"
    )
    if js_result:
        print(f"  [成功-JS] 涨跌相关文本: {js_result}")
    else:
        print("  [失败] 未能提取涨跌信息")


def _extract_volume_info(page: ChromiumPage) -> None:
    """提取成交量、成交额信息"""
    # 东方财富行情页通常在详情区域显示成交量/额
    js_result = page.run_js(
        "const items = document.querySelectorAll('.quote-detail_item, "
        ".detail-item, [class*=\"detail\"]');"
        "let result = {};"
        "items.forEach(e => {"
        "  const label = e.querySelector('.label, [class*=\"label\"]');"
        "  const value = e.querySelector('.value, [class*=\"value\"]');"
        "  if(label && value) result[label.textContent.trim()] = value.textContent.trim();"
        "});"
        "return result;"
    )
    if js_result:
        print(f"  [成功-JS] 详情指标: {js_result}")
    else:
        print("  [失败] 未能提取成交量/成交额")


def _extract_extra_indicators(page: ChromiumPage) -> None:
    """提取换手率、市盈率等额外指标"""
    js_result = page.run_js(
        "const allLabels = document.querySelectorAll('*');"
        "let indicators = {};"
        "allLabels.forEach(e => {"
        "  const t = e.textContent.trim();"
        "  if(t.includes('换手率') || t.includes('市盈率') || t.includes('市净率') "
        "     || t.includes('总市值') || t.includes('流通市值')) {"
        "    const parent = e.closest('.quote-detail_item, .detail-item, tr, [class*=\"item\"]');"
        "    if(parent) indicators[t] = parent.textContent.trim();"
        "  }"
        "});"
        "return indicators;"
    )
    if js_result:
        print(f"  [成功-JS] 额外指标: {js_result}")
    else:
        print("  [失败] 未能提取换手率等指标")


# ---------- 验证2: K线数据探索 ----------

def test_kline_data(page: ChromiumPage) -> None:
    """验证2: K线数据探索

    点击"日K"标签，检查K线数据渲染方式:
    - Canvas绘制: 需通过JS拦截或调用内部接口获取数据
    - 表格/SVG: 可直接从DOM提取
    """
    _print_banner(f"验证2: K线数据探索 — {STOCK_NAME}({STOCK_CODE})")

    try:
        # 尝试点击日K标签
        k_tab_selectors = [
            "text:日K",
            "text:日k",
            "[data-type='101']",
            ".kline-tab li:first-child",
        ]
        clicked = False
        for sel in k_tab_selectors:
            if _safe_click(page, sel):
                print(f"  [成功] 点击日K标签 (选择器: {sel})")
                clicked = True
                break
        if not clicked:
            print("  [警告] 未能点击日K标签，尝试继续探索...")

        time.sleep(WAIT_SECONDS)

        # 检查K线区域是否使用Canvas绘制
        _check_kline_canvas(page)

        # 尝试通过JS获取K线数据源
        _try_extract_kline_via_js(page)

    except Exception as exc:
        print(f"  [异常] K线数据探索失败: {exc}")


def _check_kline_canvas(page: ChromiumPage) -> None:
    """检查K线是否为Canvas绘制"""
    canvas_count = page.run_js(
        "return document.querySelectorAll('canvas').length;"
    )
    print(f"  [发现] 页面Canvas元素数量: {canvas_count}")

    # 检查K线区域是否有Canvas
    kline_canvas = page.run_js(
        "const klineArea = document.querySelector("
        "'.kline, [class*=\"kline\"], [class*=\"Kline\"], [id*=\"kline\"]"
        ");"
        "if(!klineArea) return {found: false, reason: '未找到K线容器'};"
        "const canvases = klineArea.querySelectorAll('canvas');"
        "return {found: canvases.length > 0, canvasCount: canvases.length, "
        "containerClass: klineArea.className};"
    )
    if isinstance(kline_canvas, dict):
        if kline_canvas.get("found"):
            print(
                f"  [发现] K线使用Canvas绘制 "
                f"(数量: {kline_canvas.get('canvasCount')}, "
                f"容器: {kline_canvas.get('containerClass')})"
            )
            print("  [结论] Canvas绘制无法直接从DOM提取K线数据，需通过JS接口获取")
        else:
            print(f"  [发现] K线区域未使用Canvas: {kline_canvas.get('reason')}")
            # 检查是否有SVG或表格
            _check_kline_svg_or_table(page)


def _check_kline_svg_or_table(page: ChromiumPage) -> None:
    """检查K线是否使用SVG或表格渲染"""
    svg_count = page.run_js(
        "const klineArea = document.querySelector("
        "'.kline, [class*=\"kline\"], [class*=\"Kline\"]');"
        "return klineArea ? klineArea.querySelectorAll('svg').length : 0;"
    )
    table_count = page.run_js(
        "const klineArea = document.querySelector("
        "'.kline, [class*=\"kline\"], [class*=\"Kline\"]');"
        "return klineArea ? klineArea.querySelectorAll('table').length : 0;"
    )
    if svg_count and svg_count > 0:
        print(f"  [发现] K线使用SVG绘制 (数量: {svg_count})")
    elif table_count and table_count > 0:
        print(f"  [发现] K线使用表格渲染 (数量: {table_count})")
    else:
        print("  [发现] K线区域未检测到SVG或表格元素")


def _try_extract_kline_via_js(page: ChromiumPage) -> None:
    """尝试通过JS获取K线数据源（页面内部可能缓存了数据）"""
    # 尝试访问页面JS变量中的K线数据
    js_attempts = [
        # 尝试1: 查找全局变量中的K线数据
        (
            "return typeof window.klineData !== 'undefined' "
            "? JSON.stringify(window.klineData).substring(0, 500) : 'not_found';",
            "window.klineData"
        ),
        # 尝试2: 查找常见的数据存储变量
        (
            "const keys = Object.keys(window).filter("
            "k => k.toLowerCase().includes('kline') || k.toLowerCase().includes('chart')"
            "); return keys;",
            "window全局变量搜索"
        ),
        # 尝试3: 检查是否有Vue/React实例数据
        (
            "const app = document.querySelector('#app, [data-v-app], [id*=\"app\"]');"
            "return app ? 'found_app_container' : 'no_app';",
            "前端框架容器"
        ),
    ]

    for js_code, desc in js_attempts:
        try:
            result = page.run_js(js_code)
            print(f"  [探索] {desc}: {result}")
        except Exception as exc:
            print(f"  [探索] {desc} 执行失败: {exc}")


# ---------- 验证3: 分时线数据探索 ----------

def test_trends_data(page: ChromiumPage) -> None:
    """验证3: 分时线数据探索

    点击"分时"标签，检查分时数据是否可从DOM提取。
    """
    _print_banner(f"验证3: 分时线数据探索 — {STOCK_NAME}({STOCK_CODE})")

    try:
        # 点击分时标签
        trend_tab_selectors = [
            "text:分时",
            "[data-type='trends']",
            ".kline-tab li:nth-child(2)",
        ]
        clicked = False
        for sel in trend_tab_selectors:
            if _safe_click(page, sel):
                print(f"  [成功] 点击分时标签 (选择器: {sel})")
                clicked = True
                break
        if not clicked:
            print("  [警告] 未能点击分时标签，尝试继续探索...")

        time.sleep(WAIT_SECONDS)

        # 检查分时区域渲染方式
        trend_canvas = page.run_js(
            "const trendArea = document.querySelector("
            "'.trend, [class*=\"trend\"], [class*=\"Trend\"], [id*=\"trend\"]"
            ");"
            "if(!trendArea) return {found: false, reason: '未找到分时容器'};"
            "const canvases = trendArea.querySelectorAll('canvas');"
            "const svgs = trendArea.querySelectorAll('svg');"
            "return {"
            "  found: true,"
            "  canvasCount: canvases.length,"
            "  svgCount: svgs.length,"
            "  containerClass: trendArea.className"
            "};"
        )
        if isinstance(trend_canvas, dict):
            if trend_canvas.get("found"):
                print(
                    f"  [发现] 分时区域: "
                    f"Canvas={trend_canvas.get('canvasCount')}, "
                    f"SVG={trend_canvas.get('svgCount')}, "
                    f"容器={trend_canvas.get('containerClass')}"
                )
            else:
                print(f"  [发现] {trend_canvas.get('reason')}")

        # 尝试通过JS获取分时数据
        trend_data = page.run_js(
            "const keys = Object.keys(window).filter("
            "k => k.toLowerCase().includes('trend') "
            "|| k.toLowerCase().includes('time')"
            "); return keys;"
        )
        print(f"  [探索] 分时相关全局变量: {trend_data}")

    except Exception as exc:
        print(f"  [异常] 分时线数据探索失败: {exc}")


# ---------- 验证4: 五档盘口数据提取 ----------

def test_order_book(page: ChromiumPage) -> None:
    """验证4: 五档盘口数据提取

    查找买卖五档盘口区域，提取买1-5价/量、卖1-5价/量。
    """
    _print_banner(f"验证4: 五档盘口 — {STOCK_NAME}({STOCK_CODE})")

    try:
        # 尝试通过结构化选择器提取盘口数据
        _extract_order_book_structured(page)

        # 尝试通过JS提取盘口数据
        _extract_order_book_via_js(page)

    except Exception as exc:
        print(f"  [异常] 五档盘口提取失败: {exc}")


def _extract_order_book_structured(page: ChromiumPage) -> None:
    """通过DOM结构提取五档盘口"""
    # 东方财富盘口区域通常有明确的买卖标识
    selectors_to_try = [
        ".quote-bid, .quote-ask",
        "[class*='bid'], [class*='ask']",
        "[class*='orderBook']",
        "[class*='order-book']",
    ]
    for sel in selectors_to_try:
        try:
            eles = page.eles(sel, timeout=3)
            if eles:
                print(f"  [发现] 盘口元素 (选择器: {sel}, 数量: {len(eles)})")
                for idx, ele in enumerate(eles[:10]):
                    text = ele.text.strip()
                    if text:
                        print(f"    元素{idx}: {text[:80]}")
                return
        except Exception:
            continue

    print("  [失败] 未能通过结构化选择器定位盘口区域")


def _extract_order_book_via_js(page: ChromiumPage) -> None:
    """通过JS提取五档盘口数据"""
    js_result = page.run_js(
        "let result = {buy: [], sell: []};"
        # 查找包含"买"或"卖"的元素
        "document.querySelectorAll('*').forEach(e => {"
        "  const t = e.textContent.trim();"
        "  if(/^买[1-5]$/.test(t) || /^卖[1-5]$/.test(t)) {"
        "    const parent = e.closest('tr, li, [class*=\"item\"], [class*=\"row\"]');"
        "    if(parent) {"
        "      const entry = parent.textContent.trim().replace(/\\s+/g, ' ');"
        "      if(t.startsWith('买')) result.buy.push(entry);"
        "      else result.sell.push(entry);"
        "    }"
        "  }"
        "});"
        "return result;"
    )
    if isinstance(js_result, dict):
        buy_data = js_result.get("buy", [])
        sell_data = js_result.get("sell", [])
        if buy_data or sell_data:
            print(f"  [成功-JS] 买盘: {buy_data}")
            print(f"  [成功-JS] 卖盘: {sell_data}")
        else:
            print("  [失败] JS方式未提取到盘口数据，尝试英文标签...")
            # 尝试英文标签 (B1-B5 / S1-S5)
            _extract_order_book_english(page)
    else:
        print("  [失败] JS返回非预期结果")


def _extract_order_book_english(page: ChromiumPage) -> None:
    """尝试英文标签提取盘口数据"""
    js_result = page.run_js(
        "let result = {buy: [], sell: []};"
        "document.querySelectorAll('*').forEach(e => {"
        "  const t = e.textContent.trim();"
        "  if(/^[Bs][1-5]$/i.test(t)) {"
        "    const parent = e.closest('tr, li, [class*=\"item\"], [class*=\"row\"]');"
        "    if(parent) {"
        "      const entry = parent.textContent.trim().replace(/\\s+/g, ' ');"
        "      if(t.toUpperCase().startsWith('B')) result.buy.push(entry);"
        "      else result.sell.push(entry);"
        "    }"
        "  }"
        "});"
        "return result;"
    )
    if isinstance(js_result, dict):
        buy_data = js_result.get("buy", [])
        sell_data = js_result.get("sell", [])
        if buy_data or sell_data:
            print(f"  [成功-JS] 买盘(英文标签): {buy_data}")
            print(f"  [成功-JS] 卖盘(英文标签): {sell_data}")
        else:
            print("  [失败] 英文标签也未提取到盘口数据")


# ---------- 验证5: 资金流向数据探索 ----------

def test_fund_flow(page: ChromiumPage) -> None:
    """验证5: 资金流向数据探索

    点击"资金"标签，检查资金流向数据是否可从DOM提取。
    """
    _print_banner(f"验证5: 资金流向 — {STOCK_NAME}({STOCK_CODE})")

    try:
        # 点击资金标签
        fund_tab_selectors = [
            "text:资金",
            "[data-type='fund']",
            "text:资金流向",
        ]
        clicked = False
        for sel in fund_tab_selectors:
            if _safe_click(page, sel):
                print(f"  [成功] 点击资金标签 (选择器: {sel})")
                clicked = True
                break
        if not clicked:
            print("  [警告] 未能点击资金标签，尝试继续探索...")

        time.sleep(WAIT_SECONDS)

        # 检查资金流向数据是否在DOM中
        _check_fund_flow_dom(page)

        # 尝试通过JS提取资金流向表格数据
        _extract_fund_flow_via_js(page)

    except Exception as exc:
        print(f"  [异常] 资金流向数据探索失败: {exc}")


def _check_fund_flow_dom(page: ChromiumPage) -> None:
    """检查资金流向数据DOM结构"""
    fund_elements = page.run_js(
        "const fundArea = document.querySelector("
        "'[class*=\"fund\"], [class*=\"Fund\"], [id*=\"fund\"], "
        "[class*=\"capital\"], [class*=\"Capital\"]'"
        ");"
        "if(!fundArea) return {found: false};"
        "return {"
        "  found: true,"
        "  tag: fundArea.tagName,"
        "  class: fundArea.className,"
        "  tables: fundArea.querySelectorAll('table').length,"
        "  childCount: fundArea.children.length"
        "};"
    )
    if isinstance(fund_elements, dict):
        if fund_elements.get("found"):
            print(
                f"  [发现] 资金流向区域: "
                f"标签={fund_elements.get('tag')}, "
                f"表格数={fund_elements.get('tables')}, "
                f"子元素数={fund_elements.get('childCount')}"
            )
        else:
            print("  [发现] 未找到资金流向区域")


def _extract_fund_flow_via_js(page: ChromiumPage) -> None:
    """通过JS提取资金流向表格数据"""
    js_result = page.run_js(
        "const tables = document.querySelectorAll('table');"
        "let fundTables = [];"
        "tables.forEach((table, i) => {"
        "  const text = table.textContent;"
        "  if(text.includes('主力') || text.includes('超大单') "
        "     || text.includes('大单') || text.includes('中单') "
        "     || text.includes('小单') || text.includes('净流入')) {"
        "    const rows = table.querySelectorAll('tr');"
        "    let tableData = [];"
        "    rows.forEach(row => {"
        "      const cells = row.querySelectorAll('td, th');"
        "      let rowData = [];"
        "      cells.forEach(c => rowData.push(c.textContent.trim()));"
        "      if(rowData.length > 0) tableData.push(rowData);"
        "    });"
        "    fundTables.push({index: i, data: tableData});"
        "  }"
        "});"
        "return fundTables;"
    )
    if js_result:
        for table_info in js_result:
            print(f"  [成功-JS] 资金流向表格(索引{table_info.get('index')}):")
            for row in table_info.get("data", [])[:6]:
                print(f"    {row}")
    else:
        print("  [失败] 未提取到资金流向表格数据")


# ---------- 页面结构探索 ----------

def explore_page_structure(page: ChromiumPage) -> None:
    """探索页面整体DOM结构，辅助后续选择器定位"""
    _print_banner("页面结构探索")

    try:
        # 获取页面标题确认加载成功
        title = page.title
        print(f"  页面标题: {title}")

        # 统计关键元素数量
        stats = page.run_js(
            "return {"
            "  canvas: document.querySelectorAll('canvas').length,"
            "  svg: document.querySelectorAll('svg').length,"
            "  table: document.querySelectorAll('table').length,"
            "  iframe: document.querySelectorAll('iframe').length"
            "};"
        )
        print(f"  元素统计: Canvas={stats.get('canvas')}, "
              f"SVG={stats.get('svg')}, "
              f"Table={stats.get('table')}, "
              f"IFrame={stats.get('iframe')}")

        # 检查是否有iframe（数据可能在iframe中）
        if stats.get("iframe", 0) > 0:
            _explore_iframes(page)

    except Exception as exc:
        print(f"  [异常] 页面结构探索失败: {exc}")


def _explore_iframes(page: ChromiumPage) -> None:
    """探索iframe内容，数据可能嵌套在iframe中"""
    iframe_info = page.run_js(
        "const iframes = document.querySelectorAll('iframe');"
        "let info = [];"
        "iframes.forEach((f, i) => {"
        "  info.push({index: i, src: f.src || f.getAttribute('src') || '', "
        "id: f.id || '', class: f.className || ''});"
        "});"
        "return info;"
    )
    if iframe_info:
        print("  [发现] 页面包含iframe:")
        for info in iframe_info:
            print(
                f"    iframe[{info.get('index')}]: "
                f"src={info.get('src', '')[:80]}, "
                f"id={info.get('id')}, "
                f"class={info.get('class')}"
            )


# ---------- 主入口 ----------

def main() -> None:
    """依次执行全部5项浏览器模式验证"""
    print(f"开始东方财富行情主页浏览器模式验证 — 标的: {STOCK_NAME}({STOCK_CODE})")
    print(f"目标URL: {QUOTE_URL}")

    # 配置浏览器选项
    co = ChromiumOptions()
    co.headless()
    # 禁用GPU加速，减少无头模式资源占用
    co.set_argument("--disable-gpu")
    co.set_argument("--no-sandbox")
    co.set_argument("--disable-dev-shm-usage")

    page: ChromiumPage | None = None
    try:
        page = ChromiumPage(co)
        print("  [成功] 浏览器实例创建完成")

        # 访问行情页
        page.get(QUOTE_URL)
        print(f"  [成功] 页面加载完成: {QUOTE_URL}")

        # 等待SPA动态内容加载
        page.wait.doc_loaded()
        time.sleep(WAIT_SECONDS * 3)

        # 先探索页面结构
        explore_page_structure(page)

        # 依次执行验证
        test_realtime_quote(page)
        test_kline_data(page)
        test_trends_data(page)
        test_order_book(page)
        test_fund_flow(page)

    except Exception as exc:
        print(f"\n[严重异常] 脚本执行失败: {exc}")
    finally:
        # 确保浏览器关闭，释放资源
        if page is not None:
            page.quit()
            print("\n  [完成] 浏览器已关闭")

    print("\n" + "=" * 70)
    print("  全部验证完成")
    print("=" * 70)


if __name__ == "__main__":
    main()
