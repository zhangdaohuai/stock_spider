"""东方财富 datacenter-web reportName 综合探测脚本

三阶段探测:
  阶段1: 从东方财富各页面HTML及引用的JS文件中提取reportName
  阶段2: 暴力枚举可能的reportName变体，通过API验证
  阶段3: 测试项目中已知的所有reportName当前可用性
"""

import os
import re
import time
import logging

for _key in [
    "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
    "ALL_PROXY", "all_proxy",
]:
    os.environ.pop(_key, None)

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
)
logger = logging.getLogger(__name__)

_REQUEST_INTERVAL: float = 1.0
_DC_BASE: str = "https://datacenter-web.eastmoney.com/api/data/v1/get"

_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://data.eastmoney.com/",
}

_PAGES: list[dict[str, str]] = [
    {"name": "融资融券", "url": "https://data.eastmoney.com/rzrq/"},
    {"name": "龙虎榜", "url": "https://data.eastmoney.com/stock/lhb/"},
    {"name": "大宗交易", "url": "https://data.eastmoney.com/dzjy/"},
    {"name": "分红送配", "url": "https://data.eastmoney.com/yjfp/"},
    {"name": "股东分析", "url": "https://data.eastmoney.com/gdfx/"},
    {"name": "研报", "url": "https://data.eastmoney.com/report/"},
    {"name": "沪深港通", "url": "https://data.eastmoney.com/hsgt/"},
]

_CANDIDATE_REPORTS: list[str] = [
    "RPT_RZRQ_SHZJMX", "RPT_RZRQ_MRHJ", "RPT_RZRQ_SHDETAIL",
    "RPT_RZRQ_SZDETAIL", "RPT_RZRQ_DETAILNEW", "RPT_RZRQ_LSHJ_NEW",
    "RDT_BILLBOARD_DAILYSTAT", "RDT_BILLBOARD_INDUSTRY",
    "RPT_BILLBOARD_DAILYSTAT", "RPT_BILLBOARD_DAILYDETAIL_NEW",
    "RPT_DABLOCK_SELLBRANCH", "RPT_DABLOCK_DAILYSTAT",
    "RPT_DABLOCK_TRADE_NEW",
    "RPT_DIVIDEND_XRDATE", "RPT_DIVIDEND_IMPLEMENT",
    "RPT_DIVIDEND_PLAN_NEW", "RPT_DIVIDEND_YEARPLAN",
    "RPT_F10_EH_TOP10HOLDER", "RPT_F10_EH_TOP10FLOWHOLDER",
    "RPT_F10_EH_MANAGER", "RPT_F10_EH_HOLDERSNUM_NEW",
    "RPT_F10_EH_FREEHOLDER",
    "RPT_RESEARCH_RANK", "RPT_RESEARCH_ORG",
    "RPT_RESEARCH_DET_NEW", "RPT_RESEARCH_INDUSTRY",
    "RPT_HSGT_NORTHACCFLOW", "RPT_HSGT_SOUTHACCFLOW",
    "RPT_HSGT_STOCKSTAT", "RPT_MUTUAL_STOCK_SOUTH",
    "RPT_HSGT_INDIVIDUAL_INFO_NEW", "RPT_MUTUAL_STOCK_NORTH_NEW",
    "RPT_CSDC_LIST_NEW", "RPT_CSDC_DETAILED_NEW",
    "RPT_LICO_FN_CPD_NEW",
    "RPT_RESOLVE_EXPLAIN_NEW", "RPT_STOCK_ADDITIONAL_NEW",
]

_KNOWN_REPORTS: list[str] = [
    "RPT_RZRQ_LSHJ", "RPT_RZRQ_SHZJHZ", "RPT_RZRQ_ZHTJ",
    "RDT_BILLBOARD_DAILYDETAIL", "RDT_BILLBOARD_BROKER_BUY",
    "RDT_BILLBOARD_BROKER_SELL",
    "RPT_DABLOCK_TRADE", "RPT_DABLOCK_TRADEMKT",
    "RPT_DABLOCK_BUYBRANCH",
    "RPT_DIVIDEND_PLAN", "RPT_RESOLVE_EXPLAIN",
    "RPT_STOCK_ADDITIONAL",
    "RPT_F10_EH_HOLDERSNUM", "RPT_F10_EH_INSTITUTION",
    "RPT_F10_EH_HOLDERSCHG",
    "RPT_RESEARCH_DET", "RPT_EARNS_FORECAST_DET",
    "RPT_EARNS_FORECAST_RANK",
    "RPT_MUTUAL_STOCK_NORTH", "RPT_HSGT_INDIVIDUAL_INFO",
    "RPT_CSDC_LIST", "RPT_CSDC_DETAILED",
    "RPT_LICO_FN_CPD", "RPT_DMSK_FN_BALANCE",
    "RPT_DMSK_FN_INCOME", "RPT_DMSK_FN_CASHFLOW",
    "RPT_F10_STKCAL",
]


def _extract_report_names_from_text(text: str) -> list[str]:
    """从文本中提取所有reportName值"""
    patterns: list[str] = [
        r'reportName\s*[:=]\s*["\']([A-Z_]+)["\']',
        r'reportName\s*[:=]\s*([A-Z_]+)',
        r'"reportName"\s*:\s*"([A-Z_]+)"',
    ]
    found: set[str] = set()
    for pattern in patterns:
        matches = re.findall(pattern, text)
        found.update(matches)
    return sorted(
        name for name in found
        if re.match(r'^[A-Z]{2,5}_[A-Z_]+$', name) and len(name) > 5
    )


def _test_report_with_sorts(
    session: requests.Session,
    report_name: str,
) -> dict[str, object]:
    """测试reportName，尝试多种排序列"""
    sort_options = ["TRADE_DATE", "REPORT_DATE", "END_DATE", ""]
    for sort_col in sort_options:
        params: dict[str, object] = {
            "reportName": report_name,
            "columns": "ALL",
            "filter": '(SECURITY_CODE="603288")',
            "pageNumber": 1,
            "pageSize": 3,
            "sortTypes": -1,
        }
        if sort_col:
            params["sortColumns"] = sort_col

        try:
            resp = session.get(
                _DC_BASE, params=params, headers=_HEADERS, timeout=10,
            )
            data = resp.json()
            code = data.get("code", "")
            result = data.get("result")
            if result and isinstance(result, dict):
                rows = result.get("data", []) or []
                return {
                    "report_name": report_name,
                    "success": True,
                    "code": code,
                    "rows": len(rows),
                    "sort_columns": sort_col,
                    "fields": list(rows[0].keys())[:5] if rows else [],
                }
            else:
                msg = data.get("message", "")
                if "排序列不存在" in msg:
                    continue
                return {
                    "report_name": report_name,
                    "success": False,
                    "code": code,
                    "message": msg[:60],
                }
        except Exception as exc:
            return {
                "report_name": report_name,
                "success": False,
                "code": -1,
                "message": str(exc)[:60],
            }
    return {
        "report_name": report_name,
        "success": False,
        "code": 9501,
        "message": "所有排序列均不可用",
    }


def phase1_extract_from_pages(
    session: requests.Session,
) -> dict[str, list[str]]:
    """阶段1: 从各页面HTML及引用的JS文件中提取reportName"""
    print("\n" + "=" * 70)
    print("  阶段1: 从东方财富页面HTML/JS中提取reportName")
    print("=" * 70)

    results: dict[str, list[str]] = {}

    for page in _PAGES:
        name = page["name"]
        url = page["url"]
        print(f"\n--- {name}: {url} ---")

        try:
            resp = session.get(url, timeout=15)
            html = resp.text
        except Exception as exc:
            print(f"  无法获取页面: {exc}")
            results[name] = []
            continue

        html_reports = _extract_report_names_from_text(html)
        if html_reports:
            print(f"  HTML中发现: {html_reports}")

        soup = BeautifulSoup(html, "html.parser")
        js_urls = [
            urljoin(url, tag["src"].strip())
            for tag in soup.find_all("script", src=True)
        ]
        print(f"  发现 {len(js_urls)} 个JS文件")

        js_reports: list[str] = []
        for js_url in js_urls[:10]:
            try:
                resp = session.get(js_url, timeout=10)
                if resp.status_code == 200:
                    found = _extract_report_names_from_text(resp.text)
                    if found:
                        js_reports.extend(found)
                        print(f"    JS发现: {found}")
            except Exception:
                pass
            time.sleep(0.3)

        all_reports = sorted(set(html_reports + js_reports))
        results[name] = all_reports
        print(f"  {name} 合计: {all_reports}")
        time.sleep(_REQUEST_INTERVAL)

    return results


def phase2_test_candidates(
    session: requests.Session,
) -> list[dict[str, object]]:
    """阶段2: 测试推测的reportName候选"""
    print("\n" + "=" * 70)
    print("  阶段2: 暴力枚举验证reportName候选")
    print("=" * 70)

    results: list[dict[str, object]] = []
    all_to_test = sorted(set(_CANDIDATE_REPORTS) - set(_KNOWN_REPORTS))
    total = len(all_to_test)
    print(f"  待测试候选: {total}个")

    for idx, name in enumerate(all_to_test, 1):
        result = _test_report_with_sorts(session, name)
        status = "PASS" if result["success"] else "FAIL"
        extra = ""
        if result["success"]:
            extra = f" rows={result['rows']} sort={result['sort_columns']}"
        else:
            extra = f" msg={result.get('message', '')}"
        print(f"  [{idx}/{total}] {name}: {status}{extra}")
        results.append(result)
        time.sleep(0.8)

    return results


def phase3_test_known(
    session: requests.Session,
) -> list[dict[str, object]]:
    """阶段3: 测试已知reportName当前可用性"""
    print("\n" + "=" * 70)
    print("  阶段3: 验证已知reportName当前可用性")
    print("=" * 70)

    results: list[dict[str, object]] = []
    total = len(_KNOWN_REPORTS)
    print(f"  待验证: {total}个")

    for idx, name in enumerate(_KNOWN_REPORTS, 1):
        result = _test_report_with_sorts(session, name)
        status = "PASS" if result["success"] else "FAIL"
        extra = ""
        if result["success"]:
            extra = f" rows={result['rows']} sort={result['sort_columns']}"
        else:
            extra = f" msg={result.get('message', '')}"
        print(f"  [{idx}/{total}] {name}: {status}{extra}")
        results.append(result)
        time.sleep(0.8)

    return results


def main() -> None:
    """主入口"""
    session = requests.Session()
    session.headers.update(_HEADERS)

    print("东方财富 datacenter-web reportName 综合探测")
    print(f"已知: {len(_KNOWN_REPORTS)}个, 候选: {len(_CANDIDATE_REPORTS)}个")

    phase1_results = phase1_extract_from_pages(session)
    phase2_results = phase2_test_candidates(session)
    phase3_results = phase3_test_known(session)

    print("\n" + "=" * 70)
    print("  最终汇总")
    print("=" * 70)

    print("\n--- 阶段1: 页面提取结果 ---")
    for name, reports in phase1_results.items():
        print(f"  {name}: {reports if reports else '未找到'}")

    print("\n--- 阶段2: 候选验证结果 ---")
    new_found = [r for r in phase2_results if r["success"]]
    if new_found:
        for r in new_found:
            print(f"  新发现: {r['report_name']} rows={r['rows']}")
    else:
        print("  未发现新的可用reportName")

    print("\n--- 阶段3: 已知可用性 ---")
    passed = [r for r in phase3_results if r["success"]]
    failed = [r for r in phase3_results if not r["success"]]
    print(f"  可用: {len(passed)}/{len(phase3_results)}")
    for r in passed:
        print(f"    ✅ {r['report_name']} rows={r['rows']} sort={r['sort_columns']}")
    print(f"  不可用: {len(failed)}/{len(phase3_results)}")
    for r in failed:
        print(f"    ❌ {r['report_name']}: {r.get('message', '')}")

    session.close()
    print("\n探测完成")


if __name__ == "__main__":
    main()
