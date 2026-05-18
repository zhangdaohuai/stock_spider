"""东方财富融资融券API接口验证脚本 (PoC)"""

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
_BASE_URL = "https://datacenter-web.eastmoney.com/api/data/v1/get"

# 通用请求头
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://data.eastmoney.com/",
}


def _fetch_datacenter(
    session: requests.Session,
    report_name: str,
    filter_expr: str,
    sort_columns: str,
    page_size: int = 10,
) -> dict[str, object]:
    """请求东方财富数据中心通用接口，返回原始JSON字典"""
    params: dict[str, object] = {
        "reportName": report_name,
        "columns": "ALL",
        "filter": filter_expr,
        "pageNumber": 1,
        "pageSize": page_size,
        "sortTypes": -1,
        "sortColumns": sort_columns,
    }
    url = _BASE_URL
    print(f"\n请求URL: {url}")
    print(f"  reportName: {report_name}")
    start = time.time()
    resp = session.get(url, params=params, headers=_HEADERS, timeout=15)
    elapsed = time.time() - start
    print(f"  HTTP状态码: {resp.status_code}")
    print(f"  响应时间: {elapsed:.3f}s")
    data: dict[str, object] = resp.json()
    return data


def _print_result_summary(
    data: dict[str, object],
    key_fields: list[str],
) -> None:
    """打印数据行数及每行关键字段摘要"""
    result = data.get("result")
    if result is None:
        code = data.get("code")
        message = data.get("message", "")
        print(f"  接口返回错误: code={code}, message={message}")
        return

    rows: list[dict[str, object]] = result.get("data", [])  # type: ignore[union-attr]
    row_count = len(rows)
    print(f"  数据行数: {row_count}")

    # 最多展示前3行关键字段
    for idx, row in enumerate(rows[:3]):
        fields_str = ", ".join(
            f"{k}={row.get(k, 'N/A')}" for k in key_fields
        )
        print(f"  [{idx}] {fields_str}")


def test_margin_stock(session: requests.Session) -> None:
    """验证1: 个股融资融券 (RPT_RZRQ_LSHJ)"""
    print("=" * 60)
    print("验证1: 个股融资融券 — 603288")
    print("=" * 60)
    data = _fetch_datacenter(
        session=session,
        report_name="RPT_RZRQ_LSHJ",
        filter_expr='(SECURITY_CODE="603288")',
        sort_columns="TRADE_DATE",
    )
    _print_result_summary(
        data,
        key_fields=[
            "TRADE_DATE", "SECURITY_CODE", "SECURITY_NAME_ABBR",
            "RZYE", "RQYE", "RZRQYE",
        ],
    )
    time.sleep(_REQUEST_INTERVAL)


def test_margin_balance(session: requests.Session) -> None:
    """验证2: 融资融券余额汇总 (RPT_RZRQ_SHZJHZ)"""
    print("=" * 60)
    print("验证2: 融资融券余额汇总")
    print("=" * 60)
    data = _fetch_datacenter(
        session=session,
        report_name="RPT_RZRQ_SHZJHZ",
        filter_expr='(SECURITY_CODE="603288")',
        sort_columns="TRADE_DATE",
    )
    _print_result_summary(
        data,
        key_fields=[
            "TRADE_DATE", "RZYE", "RQYE", "RZRQYE",
        ],
    )
    time.sleep(_REQUEST_INTERVAL)


def test_margin_account_stats(session: requests.Session) -> None:
    """验证3: 融资融券账户统计 (RPT_RZRQ_ZHTJ)"""
    print("=" * 60)
    print("验证3: 融资融券账户统计")
    print("=" * 60)
    data = _fetch_datacenter(
        session=session,
        report_name="RPT_RZRQ_ZHTJ",
        filter_expr='(SECURITY_CODE="603288")',
        sort_columns="TRADE_DATE",
    )
    _print_result_summary(
        data,
        key_fields=[
            "TRADE_DATE", "RZRQZH", "RZZH", "RQZH",
        ],
    )
    time.sleep(_REQUEST_INTERVAL)


def main() -> None:
    """运行所有融资融券验证"""
    session = requests.Session()
    test_margin_stock(session)
    test_margin_balance(session)
    test_margin_account_stats(session)
    session.close()
    print("\n融资融券验证全部完成 (3个API)")


if __name__ == "__main__":
    main()
