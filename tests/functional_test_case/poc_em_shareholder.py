"""东方财富股东分析+十大股东+机构持仓接口验证 (PoC)"""

import os
import time

import requests

# 清除代理设置，直连东方财富
for _key in [
    "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
    "ALL_PROXY", "all_proxy",
]:
    os.environ.pop(_key, None)

# 请求间隔(秒)
_REQUEST_INTERVAL: float = 1.5

# 目标股票代码
_STOCK_CODE: str = "603288"

# datacenter 通用基础URL
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
    sort_columns: str = "END_DATE",
    sort_types: int = -1,
) -> dict[str, object]:
    """请求 datacenter 通用接口并打印结果摘要"""
    params: dict[str, object] = {
        "reportName": report_name,
        "columns": "ALL",
        "filter": filter_expr,
        "pageNumber": 1,
        "pageSize": page_size,
        "sortTypes": sort_types,
        "sortColumns": sort_columns,
    }
    url = _DC_BASE
    print(f"\n{'=' * 60}")
    print(f"接口: {report_name}")
    print(f"URL: {url}")
    print(f"参数: {params}")
    print("=" * 60)

    start = time.time()
    try:
        resp = session.get(url, params=params, timeout=15)
        elapsed = time.time() - start
        print(f"HTTP状态码: {resp.status_code}")
        print(f"响应时间: {elapsed:.3f}s")

        data = resp.json()
        result = data.get("result") or {}
        rows = result.get("data", []) or []
        print(f"数据行数: {len(rows)}")

        # 打印关键字段
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
    """根据不同 reportName 打印关键字段"""
    if report_name == "RPT_F10_EH_HOLDERSNUM":
        # 十大流通股东 / 股东户数
        for row in rows[:3]:
            date_ = row.get("END_DATE", "")
            code = row.get("SECURITY_CODE", "")
            holders = row.get("HOLDER_NUM", "")
            print(
                f"  日期={date_}, 代码={code}, "
                f"股东户数={holders}"
            )
    elif report_name == "RPT_F10_EH_INSTITUTION":
        # 机构持仓
        for row in rows[:3]:
            date_ = row.get("END_DATE", "")
            code = row.get("SECURITY_CODE", "")
            inst = row.get("INSTITUTION_NAME", "")
            hold = row.get("HOLD_AMOUNT", "")
            print(
                f"  日期={date_}, 代码={code}, "
                f"机构={inst}, 持仓量={hold}"
            )
    elif report_name == "RPT_F10_EH_HOLDERSCHG":
        # 股东增减持
        for row in rows[:3]:
            date_ = row.get("END_DATE", "")
            name = row.get("HOLDER_NAME", "")
            chg = row.get("CHANGE_AMOUNT", "")
            print(
                f"  日期={date_}, 股东={name}, "
                f"增减量={chg}"
            )
    else:
        # 通用: 打印第一条的所有键
        print(f"  字段列表: {list(rows[0].keys())[:10]}...")


def test_top10_holders(session: requests.Session) -> None:
    """1. 十大流通股东"""
    _fetch_dc(
        session,
        report_name="RPT_F10_EH_HOLDERSNUM",
        filter_expr=f'(SECURITY_CODE="{_STOCK_CODE}")',
        page_size=5,
    )
    time.sleep(_REQUEST_INTERVAL)


def test_holder_count(session: requests.Session) -> None:
    """2. 股东户数"""
    _fetch_dc(
        session,
        report_name="RPT_F10_EH_HOLDERSNUM",
        filter_expr=f'(SECURITY_CODE="{_STOCK_CODE}")',
        page_size=5,
    )
    time.sleep(_REQUEST_INTERVAL)


def test_institution_hold(session: requests.Session) -> None:
    """3. 机构持仓"""
    _fetch_dc(
        session,
        report_name="RPT_F10_EH_INSTITUTION",
        filter_expr=f'(SECURITY_CODE="{_STOCK_CODE}")',
        page_size=5,
    )
    time.sleep(_REQUEST_INTERVAL)


def test_holder_change(session: requests.Session) -> None:
    """4. 股东增减持"""
    _fetch_dc(
        session,
        report_name="RPT_F10_EH_HOLDERSCHG",
        filter_expr=f'(SECURITY_CODE="{_STOCK_CODE}")',
        page_size=5,
    )
    time.sleep(_REQUEST_INTERVAL)


def test_f10_shareholder_research(session: requests.Session) -> None:
    """5. F10股东研究(PageAjax)"""
    url = (
        "https://emweb.securities.eastmoney.com/"
        "PC_HSF10/ShareholderResearch/PageAjax"
    )
    params = {"code": f"SH{_STOCK_CODE}"}
    print(f"\n{'=' * 60}")
    print(f"接口: F10股东研究")
    print(f"URL: {url}")
    print(f"参数: {params}")
    print("=" * 60)

    start = time.time()
    try:
        resp = session.get(url, params=params, timeout=15)
        elapsed = time.time() - start
        print(f"HTTP状态码: {resp.status_code}")
        print(f"响应时间: {elapsed:.3f}s")

        data = resp.json()
        # F10接口返回多个子对象，遍历打印各模块行数
        for key, val in data.items():
            if isinstance(val, list):
                print(f"  {key}: {len(val)}行")
            elif isinstance(val, dict) and "data" in val:
                rows = val.get("data", []) or []
                print(f"  {key}: {len(rows)}行")
            else:
                print(f"  {key}: {type(val).__name__}")

    except requests.RequestException as exc:
        elapsed = time.time() - start
        print(f"请求失败({elapsed:.3f}s): {exc}")


def main() -> None:
    """主入口: 依次验证5个股东相关API"""
    session = _create_session()

    test_top10_holders(session)
    test_holder_count(session)
    test_institution_hold(session)
    test_holder_change(session)
    test_f10_shareholder_research(session)

    session.close()
    print("\n全部验证完成")


if __name__ == "__main__":
    main()
