"""东方财富公告大全+个股日历接口验证 (PoC)"""

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


def test_stock_notice(session: requests.Session) -> None:
    """1. 个股公告"""
    url = (
        "https://np-anotice-stock.eastmoney.com/"
        "api/security/ann"
    )
    params = {
        "page_size": 5,
        "page_index": 1,
        "ann_type": "A",
        "stock_list": _STOCK_CODE,
        "f_node": 0,
        "s_node": 0,
    }
    data = _fetch_and_print(session, url, params, "个股公告")

    # 解析公告列表
    ann_list = (
        data.get("data", {}).get("list", []) or []
    )
    print(f"数据行数: {len(ann_list)}")
    for item in ann_list[:3]:
        title = item.get("title", "")
        date_ = item.get("notice_date", "")
        print(f"  日期={date_}, 标题={title[:40]}")

    time.sleep(_REQUEST_INTERVAL)


def test_notice_detail(session: requests.Session) -> None:
    """2. 公告详情(按时间倒序)"""
    url = (
        "https://np-anotice-stock.eastmoney.com/"
        "api/security/ann"
    )
    params = {
        "sr": -1,
        "page_size": 5,
        "page_index": 1,
        "ann_type": "A",
        "stock_list": _STOCK_CODE,
        "f_node": 0,
        "s_node": 0,
    }
    data = _fetch_and_print(session, url, params, "公告详情(倒序)")

    ann_list = (
        data.get("data", {}).get("list", []) or []
    )
    print(f"数据行数: {len(ann_list)}")
    for item in ann_list[:3]:
        title = item.get("title", "")
        date_ = item.get("notice_date", "")
        print(f"  日期={date_}, 标题={title[:40]}")

    time.sleep(_REQUEST_INTERVAL)


def test_stock_calendar(session: requests.Session) -> None:
    """3. 个股日历"""
    params: dict[str, object] = {
        "reportName": "RPT_F10_STKCAL",
        "columns": "ALL",
        "filter": f'(SECURITY_CODE="{_STOCK_CODE}")',
        "pageNumber": 1,
        "pageSize": 10,
        "sortTypes": -1,
        "sortColumns": "EVENT_DATE",
    }
    data = _fetch_and_print(
        session, _DC_BASE, params, "个股日历"
    )

    result = data.get("result") or {}
    rows = result.get("data", []) or []
    print(f"数据行数: {len(rows)}")
    for row in rows[:3]:
        date_ = row.get("EVENT_DATE", "")
        event = row.get("EVENT_NAME", "")
        print(f"  日期={date_}, 事件={event}")


def main() -> None:
    """主入口: 依次验证3个公告相关API"""
    session = _create_session()

    test_stock_notice(session)
    test_notice_detail(session)
    test_stock_calendar(session)

    session.close()
    print("\n全部验证完成")


if __name__ == "__main__":
    main()
