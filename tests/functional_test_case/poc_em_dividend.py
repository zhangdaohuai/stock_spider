"""东方财富分红送配接口验证 (PoC)"""

import os
import time

import requests

# 清除代理设置
for _key in [
    "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
    "ALL_PROXY", "all_proxy",
]:
    os.environ.pop(_key, None)

_REQUEST_INTERVAL: float = 1.5
_STOCK_CODE: str = "603288"
_DC_BASE: str = (
    "https://datacenter-web.eastmoney.com/api/data/v1/get"
)


def _create_session() -> requests.Session:
    """创建带默认头部的请求会话"""
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36"
        ),
        "Referer": "https://data.eastmoney.com/",
    })
    return session


def _fetch_dc(
    session: requests.Session,
    report_name: str,
    filter_expr: str,
    page_size: int = 10,
    sort_columns: str = "REPORT_DATE",
    sort_types: int = -1,
) -> dict[str, object]:
    """请求 datacenter 通用接口并打印摘要"""
    params: dict[str, object] = {
        "reportName": report_name,
        "columns": "ALL",
        "filter": filter_expr,
        "pageNumber": 1,
        "pageSize": page_size,
        "sortTypes": sort_types,
        "sortColumns": sort_columns,
    }
    print(f"\n{'=' * 60}")
    print(f"接口: {report_name}")
    print(f"URL: {_DC_BASE}")
    print(f"参数: {params}")
    print("=" * 60)

    start = time.time()
    try:
        resp = session.get(
            _DC_BASE, params=params, timeout=15
        )
        elapsed = time.time() - start
        print(f"HTTP状态码: {resp.status_code}")
        print(f"响应时间: {elapsed:.3f}s")

        data = resp.json()
        result = data.get("result") or {}
        rows = result.get("data", []) or []
        print(f"数据行数: {len(rows)}")

        if rows:
            _print_key_fields(report_name, rows)
        else:
            code = data.get("code", "")
            msg = data.get("message", "")
            print(f"无数据 | code={code}, message={msg}")

        return data  # type: ignore[return-value]

    except requests.RequestException as exc:
        elapsed = time.time() - start
        print(f"请求失败({elapsed:.3f}s): {exc}")
        return {}


def _print_key_fields(
    report_name: str, rows: list[dict[str, object]]
) -> None:
    """按 reportName 打印关键字段"""
    if report_name == "RPT_DIVIDEND_PLAN":
        # 分红送配
        for row in rows[:3]:
            date_ = row.get("REPORT_DATE", "")
            bonus = row.get("BONUS_SHARE_RATIO", "")
            cash = row.get("CASH_DIVIDEND_RATIO", "")
            print(
                f"  报告期={date_}, "
                f"送股比例={bonus}, "
                f"每股派现={cash}"
            )
    elif report_name == "RPT_RESOLVE_EXPLAIN":
        # 限售解禁
        for row in rows[:3]:
            date_ = row.get("END_DATE", "")
            vol = row.get("RESOLVE_VOL", "")
            ratio = row.get("RESOLVE_RATIO", "")
            print(
                f"  解禁日期={date_}, "
                f"解禁数量={vol}, "
                f"解禁比例={ratio}"
            )
    elif report_name == "RPT_STOCK_ADDITIONAL":
        # 增发
        for row in rows[:3]:
            date_ = row.get("REPORT_DATE", "")
            price = row.get("ADD_PRICE", "")
            vol = row.get("ADD_VOL", "")
            print(
                f"  报告期={date_}, "
                f"增发价={price}, "
                f"增发数量={vol}"
            )
    else:
        print(f"  字段列表: {list(rows[0].keys())[:10]}...")


def test_dividend_plan(session: requests.Session) -> None:
    """1. 分红送配"""
    _fetch_dc(
        session,
        report_name="RPT_DIVIDEND_PLAN",
        filter_expr=f'(SECURITY_CODE="{_STOCK_CODE}")',
        page_size=10,
    )
    time.sleep(_REQUEST_INTERVAL)


def test_restricted_unlock(session: requests.Session) -> None:
    """2. 限售解禁"""
    _fetch_dc(
        session,
        report_name="RPT_RESOLVE_EXPLAIN",
        filter_expr=f'(SECURITY_CODE="{_STOCK_CODE}")',
        page_size=10,
    )
    time.sleep(_REQUEST_INTERVAL)


def test_stock_additional(session: requests.Session) -> None:
    """3. 增发"""
    _fetch_dc(
        session,
        report_name="RPT_STOCK_ADDITIONAL",
        filter_expr=f'(SECURITY_CODE="{_STOCK_CODE}")',
        page_size=10,
    )


def main() -> None:
    """主入口: 依次验证3个分红送配相关API"""
    session = _create_session()

    test_dividend_plan(session)
    test_restricted_unlock(session)
    test_stock_additional(session)

    session.close()
    print("\n全部验证完成")


if __name__ == "__main__":
    main()
