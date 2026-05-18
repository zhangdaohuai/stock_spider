"""东方财富F10档案浏览器模式验证脚本 (PoC)

使用 DrissionPage 浏览器模式访问东方财富F10页面，通过点击标签页
提取9个F10模块的数据，重点验证之前API返回非JSON的4个标签：
核心题材、股本结构、公司大事、关联个股。
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

STOCK_CODE = "SH603288"
STOCK_NAME = "海天味业"
F10_URL = (
    "https://emweb.securities.eastmoney.com/pc_hsf10/pages/"
    "index.html?type=web&code=SH603288"
)
WAIT_SECONDS = 3

# F10标签页配置: (标签名, 之前API状态)
F10_TABS: list[tuple[str, str]] = [
    ("公司概况", "✅ API可用"),
    ("经营分析", "✅ API可用"),
    ("核心题材", "❌ API返回非JSON"),
    ("股本结构", "❌ API返回非JSON"),
    ("公司大事", "❌ API返回非JSON"),
    ("财务分析", "✅ API可用"),
    ("资本运作", "✅ API可用"),
    ("关联个股", "❌ API返回非JSON"),
    ("股东研究", "⚠️ API返回空数据"),
]


# ---------- 工具函数 ----------

def _print_banner(title: str) -> None:
    """打印分隔线和标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def _safe_click_tab(page: ChromiumPage, tab_name: str) -> bool:
    """点击F10页面标签，返回是否成功

    F10页面是SPA，标签切换不会刷新页面。
    使用多种选择器策略定位标签元素。
    """
    selectors = [
        f"text:{tab_name}",
        f"@text()={tab_name}",
        f"css:.f10-nav [data-key={tab_name}]",
        f"css:.tab-item:has-text({tab_name})",
    ]
    for sel in selectors:
        try:
            ele = page.ele(sel, timeout=5)
            if ele:
                ele.click()
                time.sleep(WAIT_SECONDS)
                print(f"  [成功] 点击标签: {tab_name} (选择器: {sel})")
                return True
        except Exception:
            continue

    # 选择器兜底: 通过JS查找并点击包含标签名的元素
    try:
        clicked = page.run_js(
            "const tabs = document.querySelectorAll("
            "'.f10-nav li, .tab-item, [class*=\"tab\"], "
            "[class*=\"nav\"] li, [class*=\"menu\"] li"
            ");"
            "for(const tab of tabs) {"
            f"  if(tab.textContent.trim() === '{tab_name}') {{"
            "    tab.click();"
            "    return true;"
            "  }"
            "}"
            "return false;"
        )
        if clicked:
            time.sleep(WAIT_SECONDS)
            print(f"  [成功-JS] 点击标签: {tab_name}")
            return True
    except Exception as exc:
        print(f"  [失败] JS点击标签 {tab_name} 异常: {exc}")

    print(f"  [失败] 未能点击标签: {tab_name}")
    return False


def _extract_tables_from_page(page: ChromiumPage) -> list[list[list[str]]]:
    """从当前页面提取所有表格数据

    返回三维列表: [表格索引][行索引][单元格索引]
    """
    tables_data: list[list[list[str]]] = []
    try:
        tables = page.eles("tag:table", timeout=5)
        for table in tables:
            rows_data: list[list[str]] = []
            rows = table.eles("tag:tr")
            for row in rows:
                cells = row.eles("tag:td")
                if not cells:
                    cells = row.eles("tag:th")
                cell_texts = [c.text.strip() for c in cells if c.text.strip()]
                if cell_texts:
                    rows_data.append(cell_texts)
            if rows_data:
                tables_data.append(rows_data)
    except Exception:
        pass
    return tables_data


def _extract_tables_via_js(page: ChromiumPage) -> list[list[list[str]]]:
    """通过JS提取页面所有表格数据（DOM方式兜底）

    当DrissionPage元素定位失败时使用此方法。
    """
    js_result = page.run_js(
        "const tables = document.querySelectorAll('table');"
        "let result = [];"
        "tables.forEach(table => {"
        "  let tableData = [];"
        "  const rows = table.querySelectorAll('tr');"
        "  rows.forEach(row => {"
        "    const cells = row.querySelectorAll('td, th');"
        "    let rowData = [];"
        "    cells.forEach(c => {"
        "      const t = c.textContent.trim();"
        "      if(t) rowData.push(t);"
        "    });"
        "    if(rowData.length > 0) tableData.push(rowData);"
        "  });"
        "  if(tableData.length > 0) result.push(tableData);"
        "});"
        "return result;"
    )
    if isinstance(js_result, list):
        return js_result
    return []


def _print_table_summary(
    tables: list[list[list[str]]],
    max_rows: int = 8,
) -> None:
    """打印表格数据摘要，限制每张表显示行数"""
    if not tables:
        print("  [空] 未提取到表格数据")
        return

    for t_idx, table in enumerate(tables):
        print(f"  表格{t_idx + 1} (共{len(table)}行):")
        for row in table[:max_rows]:
            line = " | ".join(row[:8])
            if len(row) > 8:
                line += " ..."
            print(f"    {line}")
        if len(table) > max_rows:
            print(f"    ... 省略{len(table) - max_rows}行")


def _extract_text_blocks_via_js(page: ChromiumPage) -> list[str]:
    """通过JS提取页面中的文本内容块

    用于没有表格的标签页（如核心题材、公司大事），
    提取主要内容区域的文本段落。
    """
    js_result = page.run_js(
        "const contentArea = document.querySelector("
        "'.f10-content, [class*=\"content\"], [class*=\"detail\"], "
        "[class*=\"main\"], [class*=\"info\"]"
        ");"
        "if(!contentArea) return [];"
        "const blocks = contentArea.querySelectorAll("
        "'p, div, li, dd, span, h1, h2, h3, h4'"
        ");"
        "let texts = [];"
        "blocks.forEach(b => {"
        "  const t = b.textContent.trim();"
        "  if(t && t.length > 2 && t.length < 500) texts.push(t);"
        "});"
        "return texts.slice(0, 30);"
    )
    if isinstance(js_result, list):
        return js_result
    return []


# ---------- 标签页验证函数 ----------

def test_company_survey(page: ChromiumPage) -> dict[str, object]:
    """验证1: 公司概况 — 提取公司基本信息表格"""
    _print_banner("验证1: 公司概况")
    result: dict[str, object] = {"标签": "公司概况", "点击成功": False}

    try:
        if not _safe_click_tab(page, "公司概况"):
            return result
        result["点击成功"] = True

        # 公司概况通常包含基本信息表格
        tables = _extract_tables_from_page(page)
        if not tables:
            tables = _extract_tables_via_js(page)

        _print_table_summary(tables)
        result["表格数"] = len(tables)
        result["总行数"] = sum(len(t) for t in tables)

        # 提取关键文本: 公司名称、行业、地区等
        _extract_company_key_info(page, result)

    except Exception as exc:
        result["异常"] = str(exc)
        print(f"  [异常] 公司概况提取失败: {exc}")

    return result


def _extract_company_key_info(
    page: ChromiumPage,
    result: dict[str, object],
) -> None:
    """提取公司概况中的关键信息字段"""
    key_fields = ["公司名称", "行业", "地区", "上市时间", "注册资本"]
    js_result = page.run_js(
        "let info = {};"
        "document.querySelectorAll('td, th, span, div').forEach(el => {"
        "  const t = el.textContent.trim();"
        f"  const keys = {key_fields!r};"
        "  keys.forEach(k => {"
        "    if(t.startsWith(k) || t.includes(k)) {"
        "      info[k] = t.substring(0, 100);"
        "    }"
        "  });"
        "});"
        "return info;"
    )
    if isinstance(js_result, dict) and js_result:
        print(f"  [成功] 关键字段: {js_result}")
        result["关键字段"] = js_result
    else:
        print("  [失败] 未提取到公司关键信息")


def test_business_analysis(page: ChromiumPage) -> dict[str, object]:
    """验证2: 经营分析 — 提取主营业务收入/利润表格"""
    _print_banner("验证2: 经营分析")
    result: dict[str, object] = {"标签": "经营分析", "点击成功": False}

    try:
        if not _safe_click_tab(page, "经营分析"):
            return result
        result["点击成功"] = True

        tables = _extract_tables_from_page(page)
        if not tables:
            tables = _extract_tables_via_js(page)

        _print_table_summary(tables)
        result["表格数"] = len(tables)
        result["总行数"] = sum(len(t) for t in tables)

    except Exception as exc:
        result["异常"] = str(exc)
        print(f"  [异常] 经营分析提取失败: {exc}")

    return result


def test_core_subject(page: ChromiumPage) -> dict[str, object]:
    """验证3: 核心题材 — 之前API返回非JSON，重点验证

    核心题材页面通常包含概念板块、题材分类等文本信息，
    可能没有标准表格，需要提取文本内容块。
    """
    _print_banner("验证3: 核心题材 ⚠️ API失败项")
    result: dict[str, object] = {"标签": "核心题材", "点击成功": False}

    try:
        if not _safe_click_tab(page, "核心题材"):
            return result
        result["点击成功"] = True

        # 先尝试表格提取
        tables = _extract_tables_from_page(page)
        if not tables:
            tables = _extract_tables_via_js(page)

        if tables:
            print("  [发现] 核心题材包含表格数据:")
            _print_table_summary(tables)
            result["表格数"] = len(tables)
        else:
            print("  [信息] 核心题材无标准表格，尝试文本提取...")

        # 提取文本内容块（题材描述、概念板块等）
        text_blocks = _extract_text_blocks_via_js(page)
        if text_blocks:
            print(f"  [成功] 提取到{len(text_blocks)}个文本块:")
            for idx, block in enumerate(text_blocks[:10]):
                print(f"    [{idx}] {block[:100]}")
            result["文本块数"] = len(text_blocks)
        else:
            print("  [失败] 未提取到文本内容")

        # 专门提取题材/概念关键词
        _extract_concept_keywords(page, result)

    except Exception as exc:
        result["异常"] = str(exc)
        print(f"  [异常] 核心题材提取失败: {exc}")

    return result


def _extract_concept_keywords(
    page: ChromiumPage,
    result: dict[str, object],
) -> None:
    """提取核心题材中的概念板块关键词"""
    js_result = page.run_js(
        "let concepts = [];"
        "document.querySelectorAll("
        "'[class*=\"concept\"], [class*=\"tag\"], "
        "'[class*=\"theme\"], [class*=\"subject\"]'"
        ").forEach(el => {"
        "  const t = el.textContent.trim();"
        "  if(t && t.length < 30) concepts.push(t);"
        "});"
        "return concepts.slice(0, 20);"
    )
    if isinstance(js_result, list) and js_result:
        print(f"  [成功] 概念/题材标签: {js_result}")
        result["概念标签"] = js_result
    else:
        print("  [信息] 未找到概念板块标签元素")


def test_share_structure(page: ChromiumPage) -> dict[str, object]:
    """验证4: 股本结构 — 之前API返回非JSON，重点验证

    股本结构通常包含总股本、流通股等表格数据。
    """
    _print_banner("验证4: 股本结构 ⚠️ API失败项")
    result: dict[str, object] = {"标签": "股本结构", "点击成功": False}

    try:
        if not _safe_click_tab(page, "股本结构"):
            return result
        result["点击成功"] = True

        tables = _extract_tables_from_page(page)
        if not tables:
            tables = _extract_tables_via_js(page)

        _print_table_summary(tables)
        result["表格数"] = len(tables)
        result["总行数"] = sum(len(t) for t in tables)

        # 提取股本关键数值
        _extract_share_key_figures(page, result)

    except Exception as exc:
        result["异常"] = str(exc)
        print(f"  [异常] 股本结构提取失败: {exc}")

    return result


def _extract_share_key_figures(
    page: ChromiumPage,
    result: dict[str, object],
) -> None:
    """提取股本结构中的关键数值"""
    js_result = page.run_js(
        "let figures = {};"
        "document.querySelectorAll('td, th, span, div').forEach(el => {"
        "  const t = el.textContent.trim();"
        "  if(t.includes('总股本') || t.includes('流通股') "
        "     || t.includes('限售股') || t.includes('总市值')) {"
        "    figures[t.substring(0, 50)] = true;"
        "  }"
        "});"
        "return Object.keys(figures);"
    )
    if isinstance(js_result, list) and js_result:
        print(f"  [成功] 股本关键字段: {js_result[:10]}")
        result["关键字段"] = js_result[:10]
    else:
        print("  [信息] 未提取到股本关键数值")


def test_company_event(page: ChromiumPage) -> dict[str, object]:
    """验证5: 公司大事 — 之前API返回非JSON，重点验证

    公司大事通常以时间线或列表形式展示重大事件。
    """
    _print_banner("验证5: 公司大事 ⚠️ API失败项")
    result: dict[str, object] = {"标签": "公司大事", "点击成功": False}

    try:
        if not _safe_click_tab(page, "公司大事"):
            return result
        result["点击成功"] = True

        # 尝试表格提取
        tables = _extract_tables_from_page(page)
        if not tables:
            tables = _extract_tables_via_js(page)

        if tables:
            print("  [发现] 公司大事包含表格数据:")
            _print_table_summary(tables)
            result["表格数"] = len(tables)

        # 公司大事可能以列表/时间线形式展示
        text_blocks = _extract_text_blocks_via_js(page)
        if text_blocks:
            print(f"  [成功] 提取到{len(text_blocks)}个文本块:")
            for idx, block in enumerate(text_blocks[:10]):
                print(f"    [{idx}] {block[:100]}")
            result["文本块数"] = len(text_blocks)

        # 专门提取日期相关的事件条目
        _extract_event_entries(page, result)

    except Exception as exc:
        result["异常"] = str(exc)
        print(f"  [异常] 公司大事提取失败: {exc}")

    return result


def _extract_event_entries(
    page: ChromiumPage,
    result: dict[str, object],
) -> None:
    """提取公司大事中的事件条目（含日期）"""
    js_result = page.run_js(
        "let events = [];"
        "document.querySelectorAll('li, tr, [class*=\"item\"], "
        "[class*=\"event\"], [class*=\"record\"]').forEach(el => {"
        "  const t = el.textContent.trim();"
        # 匹配日期格式: YYYY-MM-DD 或 YYYY年MM月DD日
        "  if(/\\d{4}[-年]/.test(t) && t.length > 5 && t.length < 200) {"
        "    events.push(t.substring(0, 120));"
        "  }"
        "});"
        "return events.slice(0, 15);"
    )
    if isinstance(js_result, list) and js_result:
        print(f"  [成功] 事件条目({len(js_result)}条):")
        for evt in js_result[:5]:
            print(f"    {evt}")
        result["事件条目数"] = len(js_result)
    else:
        print("  [信息] 未提取到含日期的事件条目")


def test_finance_analysis(page: ChromiumPage) -> dict[str, object]:
    """验证6: 财务分析 — 提取主要财务指标表格"""
    _print_banner("验证6: 财务分析")
    result: dict[str, object] = {"标签": "财务分析", "点击成功": False}

    try:
        if not _safe_click_tab(page, "财务分析"):
            return result
        result["点击成功"] = True

        tables = _extract_tables_from_page(page)
        if not tables:
            tables = _extract_tables_via_js(page)

        _print_table_summary(tables, max_rows=6)
        result["表格数"] = len(tables)
        result["总行数"] = sum(len(t) for t in tables)

    except Exception as exc:
        result["异常"] = str(exc)
        print(f"  [异常] 财务分析提取失败: {exc}")

    return result


def test_capital_operation(page: ChromiumPage) -> dict[str, object]:
    """验证7: 资本运作 — 提取融资、投资等表格"""
    _print_banner("验证7: 资本运作")
    result: dict[str, object] = {"标签": "资本运作", "点击成功": False}

    try:
        if not _safe_click_tab(page, "资本运作"):
            return result
        result["点击成功"] = True

        tables = _extract_tables_from_page(page)
        if not tables:
            tables = _extract_tables_via_js(page)

        _print_table_summary(tables)
        result["表格数"] = len(tables)
        result["总行数"] = sum(len(t) for t in tables)

    except Exception as exc:
        result["异常"] = str(exc)
        print(f"  [异常] 资本运作提取失败: {exc}")

    return result


def test_relative_stock(page: ChromiumPage) -> dict[str, object]:
    """验证8: 关联个股 — 之前API返回非JSON，重点验证

    关联个股通常以表格展示同行业或同概念的相关股票。
    """
    _print_banner("验证8: 关联个股 ⚠️ API失败项")
    result: dict[str, object] = {"标签": "关联个股", "点击成功": False}

    try:
        if not _safe_click_tab(page, "关联个股"):
            return result
        result["点击成功"] = True

        tables = _extract_tables_from_page(page)
        if not tables:
            tables = _extract_tables_via_js(page)

        _print_table_summary(tables)
        result["表格数"] = len(tables)
        result["总行数"] = sum(len(t) for t in tables)

        # 提取关联个股的股票代码和名称
        _extract_relative_stock_codes(page, result)

    except Exception as exc:
        result["异常"] = str(exc)
        print(f"  [异常] 关联个股提取失败: {exc}")

    return result


def _extract_relative_stock_codes(
    page: ChromiumPage,
    result: dict[str, object],
) -> None:
    """提取关联个股中的股票代码和名称"""
    js_result = page.run_js(
        "let stocks = [];"
        "document.querySelectorAll('a, td, span').forEach(el => {"
        "  const t = el.textContent.trim();"
        # 匹配6位数字股票代码
        "  if(/^\\d{6}$/.test(t) || /^[SZSH]\\d{6}$/.test(t)) {"
        "    const parent = el.closest('tr, li, [class*=\"item\"]');"
        "    if(parent) {"
        "      stocks.push(parent.textContent.trim().substring(0, 80));"
        "    }"
        "  }"
        "});"
        "return stocks.slice(0, 15);"
    )
    if isinstance(js_result, list) and js_result:
        print(f"  [成功] 关联个股({len(js_result)}条):")
        for stock in js_result[:5]:
            print(f"    {stock}")
        result["关联股票数"] = len(js_result)
    else:
        print("  [信息] 未提取到关联个股代码")


def test_shareholder_research(page: ChromiumPage) -> dict[str, object]:
    """验证9: 股东研究 — 之前API返回空数据

    股东研究通常包含十大股东、股东变化等表格。
    """
    _print_banner("验证9: 股东研究 ⚠️ API空数据项")
    result: dict[str, object] = {"标签": "股东研究", "点击成功": False}

    try:
        if not _safe_click_tab(page, "股东研究"):
            return result
        result["点击成功"] = True

        tables = _extract_tables_from_page(page)
        if not tables:
            tables = _extract_tables_via_js(page)

        _print_table_summary(tables)
        result["表格数"] = len(tables)
        result["总行数"] = sum(len(t) for t in tables)

        # 提取股东名称等关键信息
        _extract_shareholder_names(page, result)

    except Exception as exc:
        result["异常"] = str(exc)
        print(f"  [异常] 股东研究提取失败: {exc}")

    return result


def _extract_shareholder_names(
    page: ChromiumPage,
    result: dict[str, object],
) -> None:
    """提取股东研究中的股东名称"""
    js_result = page.run_js(
        "let names = [];"
        "document.querySelectorAll('td, th').forEach(el => {"
        "  const t = el.textContent.trim();"
        "  if(t.includes('股东') && t.length < 50) {"
        "    const row = el.closest('tr');"
        "    if(row) {"
        "      const cells = row.querySelectorAll('td, th');"
        "      let rowData = [];"
        "      cells.forEach(c => rowData.push(c.textContent.trim()));"
        "      names.push(rowData.join(' | '));"
        "    }"
        "  }"
        "});"
        "return names.slice(0, 10);"
    )
    if isinstance(js_result, list) and js_result:
        print(f"  [成功] 股东相关行({len(js_result)}条):")
        for name in js_result[:5]:
            print(f"    {name[:100]}")
        result["股东行数"] = len(js_result)
    else:
        print("  [信息] 未提取到股东名称")


# ---------- 页面结构探索 ----------

def explore_f10_page_structure(page: ChromiumPage) -> None:
    """探索F10页面整体DOM结构，辅助标签定位"""
    _print_banner("F10页面结构探索")

    try:
        title = page.title
        current_url = page.url
        print(f"  页面标题: {title}")
        print(f"  当前URL:  {current_url}")

        # 统计关键元素数量
        stats = page.run_js(
            "return {"
            "  table: document.querySelectorAll('table').length,"
            "  iframe: document.querySelectorAll('iframe').length,"
            "  nav: document.querySelectorAll('[class*=\"nav\"], [class*=\"tab\"]').length"
            "};"
        )
        print(
            f"  元素统计: Table={stats.get('table')}, "
            f"IFrame={stats.get('iframe')}, "
            f"Nav/Tab={stats.get('nav')}"
        )

        # 探测标签导航结构
        _explore_tab_navigation(page)

    except Exception as exc:
        print(f"  [异常] 页面结构探索失败: {exc}")


def _explore_tab_navigation(page: ChromiumPage) -> None:
    """探测F10页面的标签导航结构"""
    nav_info = page.run_js(
        "let tabs = [];"
        "document.querySelectorAll("
        "'[class*=\"nav\"] li, [class*=\"tab\"] li, "
        "'[class*=\"menu\"] li, [role=\"tab\"]'"
        ").forEach(el => {"
        "  const t = el.textContent.trim();"
        "  if(t && t.length < 20) {"
        "    tabs.push({"
        "      text: t,"
        "      tag: el.tagName,"
        "      class: el.className.substring(0, 50)"
        "    });"
        "  }"
        "});"
        "return tabs;"
    )
    if isinstance(nav_info, list) and nav_info:
        print(f"  [发现] 标签导航元素({len(nav_info)}个):")
        for tab in nav_info:
            print(
                f"    文本={tab.get('text')}, "
                f"标签={tab.get('tag')}, "
                f"class={tab.get('class')}"
            )
    else:
        print("  [信息] 未探测到标签导航结构")


# ---------- 结果汇总 ----------

def _print_summary(results: list[dict[str, object]]) -> None:
    """打印验证结果汇总报告"""
    _print_banner("验证结果汇总")

    print(f"{'标签':<10} {'点击':<6} {'表格数':<8} {'数据量':<8} {'状态'}")
    print("-" * 50)

    for r in results:
        label = str(r.get("标签", "?"))
        clicked = "✅" if r.get("点击成功") else "❌"
        table_count = str(r.get("表格数", r.get("文本块数", "-")))
        data_size = str(r.get("总行数", r.get("事件条目数", "-")))
        has_error = "异常" in r
        status = "❌异常" if has_error else "✅正常"

        print(f"{label:<10} {clicked:<6} {table_count:<8} {data_size:<8} {status}")

    # 重点标注API失败项的浏览器模式结果
    _print_api_failure_summary(results)


def _print_api_failure_summary(results: list[dict[str, object]]) -> None:
    """打印之前API失败项的浏览器模式验证结论"""
    print("\n  --- 之前API失败项的浏览器模式验证结论 ---")
    api_failed_tabs = {"核心题材", "股本结构", "公司大事", "关联个股"}
    api_empty_tabs = {"股东研究"}

    for r in results:
        label = str(r.get("标签", ""))
        if label in api_failed_tabs:
            has_data = (
                r.get("表格数", 0) or r.get("文本块数", 0)
                or r.get("概念标签") or r.get("关联股票数")
            )
            conclusion = "✅ 可提取数据" if has_data else "❌ 仍无法获取"
            print(f"  {label}: API非JSON -> 浏览器模式 {conclusion}")
        elif label in api_empty_tabs:
            has_data = r.get("表格数", 0) or r.get("股东行数", 0)
            conclusion = "✅ 有数据" if has_data else "⚠️ 仍为空"
            print(f"  {label}: API空数据 -> 浏览器模式 {conclusion}")


# ---------- 主入口 ----------

def main() -> None:
    """依次执行9个F10标签页的浏览器模式数据提取验证"""
    print(f"东方财富F10档案浏览器模式验证 — 标的: {STOCK_NAME}({STOCK_CODE})")
    print(f"目标URL: {F10_URL}")
    print(f"验证标签: {len(F10_TABS)}个")

    # 配置浏览器选项
    co = ChromiumOptions()
    co.headless()
    co.set_argument("--disable-gpu")
    co.set_argument("--no-sandbox")
    co.set_argument("--disable-dev-shm-usage")

    page: ChromiumPage | None = None
    results: list[dict[str, object]] = []

    try:
        page = ChromiumPage(co)
        print("  [成功] 浏览器实例创建完成")

        # 访问F10页面
        page.get(F10_URL)
        print(f"  [成功] 页面加载完成: {F10_URL}")

        # 等待SPA动态内容加载
        page.wait.doc_loaded()
        time.sleep(WAIT_SECONDS * 2)

        # 先探索页面结构
        explore_f10_page_structure(page)

        # 依次验证9个标签页
        results.append(test_company_survey(page))
        results.append(test_business_analysis(page))
        results.append(test_core_subject(page))
        results.append(test_share_structure(page))
        results.append(test_company_event(page))
        results.append(test_finance_analysis(page))
        results.append(test_capital_operation(page))
        results.append(test_relative_stock(page))
        results.append(test_shareholder_research(page))

    except Exception as exc:
        print(f"\n[严重异常] 脚本执行失败: {exc}")
    finally:
        if page is not None:
            page.quit()
            print("\n  [完成] 浏览器已关闭")

    # 打印汇总报告
    if results:
        _print_summary(results)

    print("\n" + "=" * 70)
    print("  全部F10标签页验证完成")
    print("=" * 70)


if __name__ == "__main__":
    main()
