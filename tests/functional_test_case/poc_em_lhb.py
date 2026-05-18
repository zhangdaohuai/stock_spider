"""东方财富龙虎榜接口验证脚本 — 个股龙虎榜/机构买卖"""

import os
import time

# 清除代理设置，直连东方财富
for _key in [
    "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
    "ALL_PROXY", "all_proxy",
]:
    os.environ.pop(_key, None)

import requests  # noqa: E402


# ---------- 常量 ----------

STOCK_CODE = "603288"  # 海天味业
STOCK_NAME = "海天味业"
REQUEST_INTERVAL = 1.5  # 请求间隔(秒)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://data.eastmoney.com/",
}


# ---------- 工具函数 ----------

def _timestamp() -> str:
    """返回毫秒级时间戳字符串"""
    return str(int(time.time() * 1000))


def _print_banner(title: str) -> None:
    """打印分隔线和标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def _request_and_report(
    session: requests.Session,
    url: str,
    params: dict[str, str],
    label: str,
) -> dict:
    """发送 GET 请求并打印状态码、响应时间、数据行数等摘要信息"""
    full_url = session.prepare_request(
        requests.Request("GET", url, params=params)
    ).url
    print(f"[{label}] URL: {full_url[:120]}...")

    start = time.time()
    try:
        resp = session.get(url, params=params, timeout=10)
        elapsed = time.time() - start
        print(f"  HTTP 状态码: {resp.status_code}  |  响应时间: {elapsed:.3f}s")

        data: dict = resp.json()
        # datacenter 接口的返回码在 result.code 或直接在 code 字段
        code = data.get("code", data.get("result", {}).get("code", "N/A"))
        print(f"  返回码 code: {code}")

        # 统计数据行数
        result = data.get("result", {})
        row_count = 0
        if isinstance(result, dict):
            data_list = result.get("data", [])
            if isinstance(data_list, list):
                row_count = len(data_list)
                print(f"  数据行数: {row_count}")
        print(f"  总数据行数: {row_count}")
        return data

    except Exception as exc:
        elapsed = time.time() - start
        print(f"  请求失败 ({elapsed:.3f}s): {exc}")
        return {}


# ---------- 验证函数 ----------

def test_lhb_stock_detail(session: requests.Session) -> None:
    """验证1: 个股龙虎榜详情"""
    _print_banner(f"验证1: 个股龙虎榜 — {STOCK_NAME}({STOCK_CODE})")

    url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    params = {
        "reportName": "RDT_BILLBOARD_DAILYDETAIL",
        "columns": "ALL",
        "filter": f'(SECURITY_CODE="{STOCK_CODE}")',
        "pageNumber": "1",
        "pageSize": "10",
        "sortTypes": "-1",
        "sortColumns": "TRADE_DATE",
    }

    data = _request_and_report(session, url, params, "个股龙虎榜")
    records = data.get("result", {}).get("data", [])
    if records:
        for rec in records[:3]:
            # 关键字段: TRADE_DATE, SECURITY_CODE, SECURITY_NAME_ABBR, CLOSE_PRICE, CHANGE_RATE
            print(
                f"  日期: {rec.get('TRADE_DATE', 'N/A')}, "
                f"代码: {rec.get('SECURITY_CODE', 'N/A')}, "
                f"名称: {rec.get('SECURITY_NAME_ABBR', 'N/A')}, "
                f"收盘价: {rec.get('CLOSE_PRICE', 'N/A')}, "
                f"涨跌幅: {rec.get('CHANGE_RATE', 'N/A')}%"
            )


def test_lhb_broker_buy(session: requests.Session) -> None:
    """验证2: 龙虎榜机构买入"""
    _print_banner(f"验证2: 龙虎榜机构买入 — {STOCK_NAME}({STOCK_CODE})")

    url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    params = {
        "reportName": "RDT_BILLBOARD_BROKER_BUY",
        "columns": "ALL",
        "filter": f'(SECURITY_CODE="{STOCK_CODE}")',
        "pageNumber": "1",
        "pageSize": "10",
        "sortTypes": "-1",
        "sortColumns": "TRADE_DATE",
    }

    data = _request_and_report(session, url, params, "龙虎榜机构买入")
    records = data.get("result", {}).get("data", [])
    if records:
        for rec in records[:3]:
            print(
                f"  日期: {rec.get('TRADE_DATE', 'N/A')}, "
                f"代码: {rec.get('SECURITY_CODE', 'N/A')}, "
                f"名称: {rec.get('SECURITY_NAME_ABBR', 'N/A')}, "
                f"买入额: {rec.get('BUY_AMOUNT', 'N/A')}, "
                f"营业部: {rec.get('OPERATEDEPT_NAME', 'N/A')}"
            )


def test_lhb_broker_sell(session: requests.Session) -> None:
    """验证3: 龙虎榜机构卖出"""
    _print_banner(f"验证3: 龙虎榜机构卖出 — {STOCK_NAME}({STOCK_CODE})")

    url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    params = {
        "reportName": "RDT_BILLBOARD_BROKER_SELL",
        "columns": "ALL",
        "filter": f'(SECURITY_CODE="{STOCK_CODE}")',
        "pageNumber": "1",
        "pageSize": "10",
        "sortTypes": "-1",
        "sortColumns": "TRADE_DATE",
    }

    data = _request_and_report(session, url, params, "龙虎榜机构卖出")
    records = data.get("result", {}).get("data", [])
    if records:
        for rec in records[:3]:
            print(
                f"  日期: {rec.get('TRADE_DATE', 'N/A')}, "
                f"代码: {rec.get('SECURITY_CODE', 'N/A')}, "
                f"名称: {rec.get('SECURITY_NAME_ABBR', 'N/A')}, "
                f"卖出额: {rec.get('SELL_AMOUNT', 'N/A')}, "
                f"营业部: {rec.get('OPERATEDEPT_NAME', 'N/A')}"
            )


# ---------- 主入口 ----------

def main() -> None:
    """依次执行全部3项验证，每项之间间隔1.5秒"""
    session = requests.Session()
    session.headers.update(HEADERS)

    tests = [
        test_lhb_stock_detail,
        test_lhb_broker_buy,
        test_lhb_broker_sell,
    ]

    print(f"开始验证东方财富龙虎榜接口 — 标的: {STOCK_NAME}({STOCK_CODE})")
    print(f"共 {len(tests)} 项验证，请求间隔 {REQUEST_INTERVAL}s")

    for idx, test_fn in enumerate(tests):
        test_fn(session)
        if idx < len(tests) - 1:
            time.sleep(REQUEST_INTERVAL)

    print("\n" + "=" * 70)
    print("  全部验证完成")
    print("=" * 70)


if __name__ == "__main__":
    main()
