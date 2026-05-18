"""东方财富沪深港通接口验证 (PoC)"""

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


def _fetch_and_print(
    session: requests.Session,
    url: str,
    params: dict[str, object],
    label: str,
) -> dict[str, object]:
    """通用请求+打印摘要"""
    print(f"\n{'=' * 60}")
    print(f"接口: {label}")
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
        return data  # type: ignore[return-value]

    except requests.RequestException as exc:
        elapsed = time.time() - start
        print(f"请求失败({elapsed:.3f}s): {exc}")
        return {}


def test_kamtbs(session: requests.Session) -> None:
    """1. 沪深港通资金(K线推送接口)"""
    url = (
        "https://push2his.eastmoney.com/"
        "api/qt/kamtbs.wss/get"
    )
    params: dict[str, object] = {
        "fields1": "f1,f2,f3,f4",
        "fields2": "f51,f52,f53,f54,f55,f56",
        "ut": "fa5fd1943c7b386f172d6893dbfba10b",
        "_": str(int(time.time() * 1000)),
    }
    data = _fetch_and_print(
        session, url, params, "沪深港通资金"
    )

    # 解析推送数据
    result = data.get("data", {}) or {}
    # data可能包含多个子字段，遍历打印行数
    if isinstance(result, dict):
        for key, val in result.items():
            if isinstance(val, list):
                print(f"  {key}: {len(val)}行")
                # 打印最近2条
                for item in val[-2:]:
                    print(f"    {item}")
            elif isinstance(val, dict):
                inner = val.get("data", []) or []
                print(f"  {key}: {len(inner)}行")
            else:
                print(f"  {key}: {val}")

    time.sleep(_REQUEST_INTERVAL)


def test_north_hold(session: requests.Session) -> None:
    """2. 北向资金持股"""
    params: dict[str, object] = {
        "reportName": "RPT_MUTUAL_STOCK_NORTH",
        "columns": "ALL",
        "filter": f'(SECURITY_CODE="{_STOCK_CODE}")',
        "pageNumber": 1,
        "pageSize": 5,
    }
    data = _fetch_and_print(
        session, _DC_BASE, params, "北向资金持股"
    )

    result = data.get("result") or {}
    rows = result.get("data", []) or []
    print(f"数据行数: {len(rows)}")
    for row in rows[:3]:
        date_ = row.get("END_DATE", "")
        vol = row.get("HOLD_VOL", "")
        ratio = row.get("HOLD_RATIO", "")
        print(
            f"  日期={date_}, "
            f"持股量={vol}, "
            f"持股比例={ratio}"
        )

    time.sleep(_REQUEST_INTERVAL)


def test_hsgt_individual(session: requests.Session) -> None:
    """3. 沪深港通持股"""
    params: dict[str, object] = {
        "reportName": "RPT_HSGT_INDIVIDUAL_INFO",
        "columns": "ALL",
        "filter": f'(SECURITY_CODE="{_STOCK_CODE}")',
        "pageNumber": 1,
        "pageSize": 5,
    }
    data = _fetch_and_print(
        session, _DC_BASE, params, "沪深港通持股"
    )

    result = data.get("result", {})
    rows = result.get("data", []) or []
    print(f"数据行数: {len(rows)}")
    for row in rows[:3]:
        date_ = row.get("END_DATE", "")
        vol = row.get("HOLD_VOL", "")
        ratio = row.get("HOLD_RATIO", "")
        print(
            f"  日期={date_}, "
            f"持股量={vol}, "
            f"持股比例={ratio}"
        )


def main() -> None:
    """主入口: 依次验证3个沪深港通相关API"""
    session = _create_session()

    test_kamtbs(session)
    test_north_hold(session)
    test_hsgt_individual(session)

    session.close()
    print("\n全部验证完成")


if __name__ == "__main__":
    main()
