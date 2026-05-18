"""东方财富 XHR 请求拦截 PoC — Playwright 浏览器级 API 端点发现

三大拦截场景:
  1. 龙虎榜: 拦截 datacenter-web 请求，提取 reportName
  2. 行情页: 拦截 push2 / push2his 请求，发现K线/分时/盘口 API
  3. F10档案: 拦截 emweb.securities 请求，定位核心题材等接口
"""

import os
from urllib.parse import urlparse, parse_qs
from typing import Any, Callable, Optional

for _key in [
    "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
    "ALL_PROXY", "all_proxy",
]:
    os.environ.pop(_key, None)

from playwright.sync_api import sync_playwright  # type: ignore


STOCK_CODE: str = "603288"
STOCK_NAME: str = "海天味业"

TARGET_DOMAINS_DATACENTER: list[str] = ["datacenter-web.eastmoney.com"]
TARGET_DOMAINS_PUSH2: list[str] = [
    "push2.eastmoney.com",
    "push2his.eastmoney.com",
]
TARGET_DOMAINS_F10: list[str] = ["emweb.securities.eastmoney.com"]

_RESPONSE_SUMMARY_LEN: int = 200
_URL_DISPLAY_LEN: int = 150
_PAGE_WAIT_MS: int = 5000


def _print_banner(title: str) -> None:
    """打印场景分隔横幅"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def _match_domain(url: str, domains: list[str]) -> bool:
    """判断URL是否命中任一目标域名"""
    return any(domain in url for domain in domains)


def _extract_report_name(url: str) -> str:
    """从URL查询参数中提取 reportName 值"""
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    values = params.get("reportName", [])
    return values[0] if values else ""


def _extract_query_params(url: str) -> dict[str, list[str]]:
    """从URL中提取全部查询参数"""
    parsed = urlparse(url)
    return parse_qs(parsed.query)


def _truncate(text: str, max_len: int) -> str:
    """截断文本并在超出时追加省略号"""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def _build_request_record(request: Any) -> dict[str, object]:
    """从 Request 对象构建拦截记录"""
    return {
        "url": request.url,
        "method": request.method,
        "resource_type": request.resource_type,
    }


def _attach_response_summary(
    record: dict[str, object],
    response: Any,
) -> None:
    """尝试读取响应体并附加摘要到记录中"""
    try:
        body = response.text()
        record["status"] = response.status
        record["response_summary"] = _truncate(body, _RESPONSE_SUMMARY_LEN)
    except Exception:
        record["status"] = response.status
        record["response_summary"] = "<无法读取响应体>"


def _intercept_xhr(
    url: str,
    target_domains: list[str],
    wait_ms: int = _PAGE_WAIT_MS,
    extra_actions: Optional[Callable[[Any], None]] = None,
) -> list[dict[str, object]]:
    """访问指定URL并拦截目标域名的XHR请求与响应

    Args:
        url: 待访问的页面地址
        target_domains: 需要拦截的域名关键字列表
        wait_ms: 页面加载后额外等待毫秒数
        extra_actions: 可选的回调，签名为 (page) -> None，
                       用于在页面加载后执行额外交互（如点击标签页）

    Returns:
        拦截到的请求记录列表，每条包含 url/method/status/response_summary
    """
    captured: list[dict[str, object]] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 请求拦截：记录命中的请求元信息
        def on_request(request: Any) -> None:
            if _match_domain(request.url, target_domains):
                record = _build_request_record(request)
                captured.append(record)

        # 响应拦截：为已记录的请求补充状态码和响应摘要
        def on_response(response: Any) -> None:
            if not _match_domain(response.url, target_domains):
                return
            for record in captured:
                if record["url"] == response.url:
                    _attach_response_summary(record, response)
                    break

        page.on("request", on_request)
        page.on("response", on_response)

        # 导航到目标页面，使用domcontentloaded避免SPA页面超时
        page.goto(url, wait_until="domcontentloaded")

        # 执行额外交互（如切换F10标签页）
        if extra_actions is not None:
            extra_actions(page)  # type: ignore[misc]

        # 额外等待，确保延迟加载的请求也能被捕获
        page.wait_for_timeout(wait_ms)
        browser.close()

    return captured


def _print_captured_summary(
    label: str,
    captured: list[dict[str, object]],
) -> None:
    """打印拦截结果的汇总信息"""
    print(f"\n[{label}] 拦截到 {len(captured)} 个请求")

    for idx, record in enumerate(captured, 1):
        url = str(record["url"])
        method = str(record.get("method", "?"))
        status = record.get("status", "N/A")
        summary = str(record.get("response_summary", ""))

        print(f"\n  --- 请求 #{idx} ---")
        print(f"  方法: {method}  状态码: {status}")
        print(f"  URL: {_truncate(url, _URL_DISPLAY_LEN)}")

        # 提取并高亮 reportName 参数
        report_name = _extract_report_name(url)
        if report_name:
            print(f"  >>> reportName: {report_name}")

        # 打印关键查询参数（排除过长的值）
        params = _extract_query_params(url)
        if params:
            key_params: list[str] = []
            for key, vals in params.items():
                val = vals[0] if len(vals) == 1 else str(vals)
                key_params.append(f"{key}={_truncate(val, 40)}")
            print(f"  参数: {', '.join(key_params[:8])}")

        # 响应摘要
        if summary:
            print(f"  响应摘要: {_truncate(summary, 120)}")


def _collect_report_names(captured: list[dict[str, object]]) -> list[str]:
    """从拦截记录中提取所有不重复的 reportName"""
    names: list[str] = []
    seen: set[str] = set()
    for record in captured:
        name = _extract_report_name(str(record["url"]))
        if name and name not in seen:
            seen.add(name)
            names.append(name)
    return names


def scenario_lhb() -> list[dict[str, object]]:
    """场景1: 龙虎榜API发现 — 拦截 datacenter-web 请求"""
    _print_banner("场景1: 龙虎榜API发现")
    url = "https://data.eastmoney.com/stock/lhb/"
    print(f"目标页面: {url}")
    print(f"拦截域名: {TARGET_DOMAINS_DATACENTER}")

    captured = _intercept_xhr(url, TARGET_DOMAINS_DATACENTER)
    _print_captured_summary("龙虎榜", captured)

    # 汇总发现的 reportName
    report_names = _collect_report_names(captured)
    if report_names:
        print(f"\n  ★ 发现 reportName ({len(report_names)}个):")
        for name in report_names:
            print(f"    - {name}")
    else:
        print("\n  未发现 reportName 参数")

    return captured


def scenario_quote() -> list[dict[str, object]]:
    """场景2: 行情页API发现 — 拦截 push2 / push2his 请求"""
    _print_banner("场景2: 行情页API发现")
    url = f"https://quote.eastmoney.com/sh{STOCK_CODE}.html"
    print(f"目标页面: {url}")
    print(f"拦截域名: {TARGET_DOMAINS_PUSH2}")

    captured = _intercept_xhr(url, TARGET_DOMAINS_PUSH2)
    _print_captured_summary("行情页", captured)

    # 按API端点分类
    endpoint_map: dict[str, list[str]] = {}
    for record in captured:
        parsed = urlparse(str(record["url"]))
        path = parsed.path
        endpoint_map.setdefault(path, []).append(str(record["url"]))

    if endpoint_map:
        print(f"\n  ★ API端点分类 ({len(endpoint_map)}个):")
        for path, urls in endpoint_map.items():
            print(f"    {path} — {len(urls)}次请求")

    return captured


def _click_f10_tabs(page: Any) -> None:
    """在F10页面中依次点击各标签页以触发XHR请求"""
    # F10页面标签选择器（常见标签文本）
    tab_texts: list[str] = [
        "公司概况", "经营分析", "核心题材",
        "股本结构", "公司大事", "财务分析",
        "资本运作", "关联个股",
    ]
    for text in tab_texts:
        try:
            # 尝试点击标签页链接
            locator = page.locator(f"text={text}").first
            locator.click(timeout=3000)
            page.wait_for_timeout(1500)
        except Exception:
            pass


def scenario_f10() -> list[dict[str, object]]:
    """场景3: F10 API发现 — 拦截 emweb.securities 请求"""
    _print_banner("场景3: F10 API发现")
    # 直接访问F10主页，更可靠地加载完整页面
    f10_entry = (
        f"https://emweb.securities.eastmoney.com/PC_HSF10/"
        f"NewFinanceAnalysis/Index?type=web&code=SH{STOCK_CODE}"
    )
    print(f"目标页面: {f10_entry}")
    print(f"拦截域名: {TARGET_DOMAINS_F10}")

    # 之前返回非JSON的4个接口，用于标注
    problematic_paths: list[str] = [
        "Operations/SubjectDetailAjax",
        "ShareStructure/PageAjax",
        "CompanyEvent/PageAjax",
        "RelativeStock/PageAjax",
    ]

    captured = _intercept_xhr(
        f10_entry,
        TARGET_DOMAINS_F10,
        extra_actions=_click_f10_tabs,
    )
    _print_captured_summary("F10档案", captured)

    # 检查问题接口是否被拦截到
    found_problematic: list[str] = []
    for record in captured:
        url_str = str(record["url"])
        for path in problematic_paths:
            if path in url_str and path not in found_problematic:
                found_problematic.append(path)

    print(f"\n  ★ 问题接口拦截情况:")
    for path in problematic_paths:
        status = "已拦截" if path in found_problematic else "未拦截"
        print(f"    {path}: {status}")

    return captured


def _print_final_summary(
    lhb: list[dict[str, object]],
    quote: list[dict[str, object]],
    f10: list[dict[str, object]],
) -> None:
    """打印三个场景的最终汇总"""
    _print_banner("最终汇总")

    print(f"  龙虎榜: 拦截 {len(lhb)} 个请求")
    report_names = _collect_report_names(lhb)
    if report_names:
        print(f"    reportName: {', '.join(report_names)}")

    print(f"  行情页: 拦截 {len(quote)} 个请求")
    endpoint_map: dict[str, int] = {}
    for record in quote:
        parsed = urlparse(str(record["url"]))
        endpoint_map[parsed.path] = endpoint_map.get(parsed.path, 0) + 1
    if endpoint_map:
        for path, count in endpoint_map.items():
            print(f"    {path}: {count}次")

    print(f"  F10档案: 拦截 {len(f10)} 个请求")

    total = len(lhb) + len(quote) + len(f10)
    print(f"\n  合计拦截: {total} 个XHR请求")


def main() -> None:
    """主入口: 依次执行三大场景的XHR拦截"""
    print("东方财富 XHR 请求拦截 PoC")
    print(f"标的: {STOCK_NAME}({STOCK_CODE})")
    print(f"Playwright 浏览器级拦截，headless模式")

    lhb = scenario_lhb()
    quote = scenario_quote()
    f10 = scenario_f10()

    _print_final_summary(lhb, quote, f10)
    print("\n拦截完成")


if __name__ == "__main__":
    main()
