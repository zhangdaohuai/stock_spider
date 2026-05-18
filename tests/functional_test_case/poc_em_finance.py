"""东方财富财务数据API接口验证脚本 (PoC) — 三表+业绩+指标+杜邦"""

import os
import time

import requests

# 清除代理设置，直连东方财富
for _key in [
    "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
    "ALL_PROXY", "all_proxy",
]:
    os.environ.pop(_key, None)

# 请求间隔（秒）
_REQUEST_INTERVAL = 1.5

# 东方财富数据中心通用基础URL
_DATACENTER_URL = "https://datacenter-web.eastmoney.com/api/data/v1/get"

# F10财务分析接口基础URL
_FINANCE_URL = "https://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis"

# 通用请求头 — 数据中心
_DATACENTER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://data.eastmoney.com/",
}

# 通用请求头 — F10财务分析
_FINANCE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://emweb.securities.eastmoney.com/",
}


def _fetch_datacenter(
    session: requests.Session,
    report_name: str,
    sort_columns: str,
    page_size: int = 5,
) -> dict[str, object]:
    """请求东方财富数据中心通用接口（固定过滤603288）"""
    params: dict[str, object] = {
        "reportName": report_name,
        "columns": "ALL",
        "filter": '(SECURITY_CODE="603288")',
        "pageNumber": 1,
        "pageSize": page_size,
        "sortTypes": -1,
        "sortColumns": sort_columns,
    }
    url = _DATACENTER_URL
    print(f"\n请求URL: {url}")
    print(f"  reportName: {report_name}")
    start = time.time()
    resp = session.get(
        url, params=params, headers=_DATACENTER_HEADERS, timeout=15,
    )
    elapsed = time.time() - start
    print(f"  HTTP状态码: {resp.status_code}")
    print(f"  响应时间: {elapsed:.3f}s")
    try:
        return resp.json()
    except requests.exceptions.JSONDecodeError:
        print(f"  返回非JSON内容(可能接口已变更): {resp.text[:200]}")
        return {}


def _fetch_finance_api(
    session: requests.Session,
    endpoint: str,
    params: dict[str, object],
) -> dict[str, object]:
    """请求F10财务分析专用接口"""
    url = f"{_FINANCE_URL}/{endpoint}"
    print(f"\n请求URL: {url}")
    print(f"  params: {params}")
    start = time.time()
    resp = session.get(
        url, params=params, headers=_FINANCE_HEADERS, timeout=15,
    )
    elapsed = time.time() - start
    print(f"  HTTP状态码: {resp.status_code}")
    print(f"  响应时间: {elapsed:.3f}s")
    try:
        return resp.json()
    except Exception:
        print(f"  返回非JSON内容(可能接口已变更): {resp.text[:200]}")
        return {}


def _print_datacenter_summary(
    data: dict[str, object],
    key_fields: list[str],
) -> None:
    """打印数据中心接口返回的数据行数及关键字段"""
    result = data.get("result")
    if result is None:
        code = data.get("code")
        message = data.get("message", "")
        print(f"  接口返回错误: code={code}, message={message}")
        return

    rows: list[dict[str, object]] = result.get("data", [])  # type: ignore[union-attr]
    print(f"  数据行数: {len(rows)}")
    for idx, row in enumerate(rows[:3]):
        fields_str = ", ".join(
            f"{k}={row.get(k, 'N/A')}" for k in key_fields
        )
        print(f"  [{idx}] {fields_str}")


def _print_finance_summary(
    data: dict[str, object],
    key_fields: list[str],
) -> None:
    """打印F10接口返回的数据摘要"""
    # F10接口返回结构可能是 {data: [...]} 或其他格式
    payload = data.get("data")
    if payload is None:
        print(f"  接口返回: {list(data.keys())}")
        return

    if isinstance(payload, list):
        print(f"  数据行数: {len(payload)}")
        for idx, row in enumerate(payload[:3]):
            if isinstance(row, dict):
                fields_str = ", ".join(
                    f"{k}={row.get(k, 'N/A')}" for k in key_fields
                )
                print(f"  [{idx}] {fields_str}")
    elif isinstance(payload, dict):
        # 单条记录或嵌套结构
        print(f"  返回字段: {list(payload.keys())[:10]}")
    else:
        print(f"  数据类型: {type(payload).__name__}")


def test_balance_sheet(session: requests.Session) -> None:
    """验证1: 资产负债表 (RPT_DMSK_FN_BALANCE)"""
    print("=" * 60)
    print("验证1: 资产负债表 — 603288")
    print("=" * 60)
    data = _fetch_datacenter(
        session=session,
        report_name="RPT_DMSK_FN_BALANCE",
        sort_columns="REPORT_DATE",
        page_size=5,
    )
    _print_datacenter_summary(
        data,
        key_fields=[
            "REPORT_DATE", "SECURITY_CODE",
            "TOTAL_ASSETS", "TOTAL_LIABILITIES", "TOTAL_EQUITY",
        ],
    )
    time.sleep(_REQUEST_INTERVAL)


def test_income_statement(session: requests.Session) -> None:
    """验证2: 利润表 (RPT_DMSK_FN_INCOME)"""
    print("=" * 60)
    print("验证2: 利润表 — 603288")
    print("=" * 60)
    data = _fetch_datacenter(
        session=session,
        report_name="RPT_DMSK_FN_INCOME",
        sort_columns="REPORT_DATE",
        page_size=5,
    )
    _print_datacenter_summary(
        data,
        key_fields=[
            "REPORT_DATE", "SECURITY_CODE",
            "OPERATE_INCOME", "OPERATE_COST", "NETPROFIT",
        ],
    )
    time.sleep(_REQUEST_INTERVAL)


def test_cashflow_statement(session: requests.Session) -> None:
    """验证3: 现金流量表 (RPT_DMSK_FN_CASHFLOW)"""
    print("=" * 60)
    print("验证3: 现金流量表 — 603288")
    print("=" * 60)
    data = _fetch_datacenter(
        session=session,
        report_name="RPT_DMSK_FN_CASHFLOW",
        sort_columns="REPORT_DATE",
        page_size=5,
    )
    _print_datacenter_summary(
        data,
        key_fields=[
            "REPORT_DATE", "SECURITY_CODE",
            "NETCASH_OPERATE", "NETCASH_INVEST", "NETCASH_FINANCE",
        ],
    )
    time.sleep(_REQUEST_INTERVAL)


def test_performance_report(session: requests.Session) -> None:
    """验证4: 业绩报表 (RPT_LICO_FN_CPD)"""
    print("=" * 60)
    print("验证4: 业绩报表 — 603288")
    print("=" * 60)
    data = _fetch_datacenter(
        session=session,
        report_name="RPT_LICO_FN_CPD",
        sort_columns="REPORT_DATE",
        page_size=5,
    )
    _print_datacenter_summary(
        data,
        key_fields=[
            "REPORT_DATE", "SECURITY_CODE", "SECURITY_NAME_ABBR",
            "BASIC_EPS", "WEIGHTAVG_ROE", "PARENT_NETPROFIT",
        ],
    )
    time.sleep(_REQUEST_INTERVAL)


def test_main_financial_indicators(session: requests.Session) -> None:
    """验证5: 主要财务指标 (ZYZBAjaxNew)"""
    print("=" * 60)
    print("验证5: 主要财务指标 — SH603288")
    print("=" * 60)
    data = _fetch_finance_api(
        session=session,
        endpoint="ZYZBAjaxNew",
        params={"type": "0", "code": "SH603288"},
    )
    _print_finance_summary(
        data,
        key_fields=[
            "REPORT_DATE", "BASIC_EPS", "WEIGHTAVG_ROE",
            "MGJYXJJE", "MGSY",
        ],
    )
    time.sleep(_REQUEST_INTERVAL)


def test_dupont_analysis(session: requests.Session) -> None:
    """验证6: 杜邦分析 (DupontAnalysisAjax)"""
    print("=" * 60)
    print("验证6: 杜邦分析 — SH603288")
    print("=" * 60)
    data = _fetch_finance_api(
        session=session,
        endpoint="DupontAnalysisAjax",
        params={"code": "SH603288"},
    )
    _print_finance_summary(
        data,
        key_fields=[
            "REPORT_DATE", "WEIGHTAVG_ROE", "XSMLL",
            "ZCZZL", "QYBZXS",
        ],
    )
    time.sleep(_REQUEST_INTERVAL)


def main() -> None:
    """运行所有财务数据验证"""
    session = requests.Session()
    test_balance_sheet(session)
    test_income_statement(session)
    test_cashflow_statement(session)
    test_performance_report(session)
    test_main_financial_indicators(session)
    test_dupont_analysis(session)
    session.close()
    print("\n财务数据验证全部完成 (6个API)")


if __name__ == "__main__":
    main()
