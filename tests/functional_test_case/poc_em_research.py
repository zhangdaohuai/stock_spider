"""东方财富研报+盈利预测接口验证 (PoC)"""

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
    page_size: int = 5,
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
    if report_name == "RPT_RESEARCH_DET":
        # 个股研报
        for row in rows[:3]:
            date_ = row.get("REPORT_DATE", "")
            title = row.get("TITLE", "")
            org = row.get("ORG_CODE", "")
            print(
                f"  日期={date_}, 机构={org}, "
                f"标题={str(title)[:40]}"
            )
    elif report_name == "RPT_EARNS_FORECAST_DET":
        # 盈利预测明细
        for row in rows[:3]:
            date_ = row.get("REPORT_DATE", "")
            org = row.get("ORG_CODE", "")
            eps = row.get("FORECAST_EPS", "")
            print(
                f"  日期={date_}, 机构={org}, "
                f"预测EPS={eps}"
            )
    elif report_name == "RPT_EARNS_FORECAST_RANK":
        # 评级统计
        for row in rows[:3]:
            date_ = row.get("REPORT_DATE", "")
            buy = row.get("BUY_NUM", "")
            hold = row.get("HOLD_NUM", "")
            print(
                f"  日期={date_}, 买入={buy}, "
                f"持有={hold}"
            )
    else:
        print(f"  字段列表: {list(rows[0].keys())[:10]}...")


def test_research_report(session: requests.Session) -> None:
    """1. 个股研报"""
    _fetch_dc(
        session,
        report_name="RPT_RESEARCH_DET",
        filter_expr=f'(SECURITY_CODE="{_STOCK_CODE}")',
        page_size=5,
    )
    time.sleep(_REQUEST_INTERVAL)


def test_earnings_forecast(session: requests.Session) -> None:
    """2. 盈利预测"""
    _fetch_dc(
        session,
        report_name="RPT_EARNS_FORECAST_DET",
        filter_expr=f'(SECURITY_CODE="{_STOCK_CODE}")',
        page_size=5,
    )
    time.sleep(_REQUEST_INTERVAL)


def test_rating_statistics(session: requests.Session) -> None:
    """3. 评级统计"""
    _fetch_dc(
        session,
        report_name="RPT_EARNS_FORECAST_RANK",
        filter_expr=f'(SECURITY_CODE="{_STOCK_CODE}")',
        page_size=5,
    )


def main() -> None:
    """主入口: 依次验证3个研报相关API"""
    session = _create_session()

    test_research_report(session)
    test_earnings_forecast(session)
    test_rating_statistics(session)

    session.close()
    print("\n全部验证完成")


if __name__ == "__main__":
    main()
