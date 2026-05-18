"""东方财富资金流向接口验证脚本 — 个股/大盘/板块资金流"""

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

SECID = "1.603288"  # 海天味业
STOCK_CODE = "603288"
STOCK_NAME = "海天味业"
UT = "fa5fd1943c7b386f172d6893dbfba10b"
REQUEST_INTERVAL = 1.5  # 请求间隔(秒)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://quote.eastmoney.com/",
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
        rc = data.get("rc", data.get("result", {}).get("code", "N/A"))
        print(f"  返回码 rc: {rc}")

        # 统计数据行数
        inner = data.get("data", data.get("result", {}))
        row_count = 0
        if isinstance(inner, dict):
            for _key in ("klines", "trends", "diff"):
                rows = inner.get(_key)
                if isinstance(rows, list):
                    row_count = len(rows)
                    print(f"  数据行数({_key}): {row_count}")
                    break
            else:
                if inner:
                    row_count = 1
                    print("  数据行数: 1 (单条记录)")
        print(f"  总数据行数: {row_count}")
        return data

    except Exception as exc:
        elapsed = time.time() - start
        print(f"  请求失败 ({elapsed:.3f}s): {exc}")
        return {}


# ---------- 验证函数 ----------

def test_stock_fund_flow_daily(session: requests.Session) -> None:
    """验证1: 个股资金流日K"""
    _print_banner(f"验证1: 个股资金流日K — {STOCK_NAME}({STOCK_CODE})")

    url = "https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get"
    params = {
        "fields1": "f1,f2,f3,f7",
        "fields2": (
            "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,"
            "f61,f62,f63,f64,f65"
        ),
        "secid": SECID,
        "lmt": "0",
        "klt": "101",  # 日线
        "ut": UT,
        "_": _timestamp(),
    }

    data = _request_and_report(session, url, params, "个股资金流日K")
    klines = data.get("data", {}).get("klines", [])
    if klines:
        # 格式: 日期,主力净流入,小单净流入,中单净流入,大单净流入,超大单净流入...
        print(f"  最早: {klines[0]}")
        print(f"  最新: {klines[-1]}")


def test_stock_fund_flow_minute(session: requests.Session) -> None:
    """验证2: 个股资金流分钟级 (最近5条)"""
    _print_banner(f"验证2: 个股资金流分钟级 — {STOCK_NAME}({STOCK_CODE})")

    url = "https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get"
    params = {
        "fields1": "f1,f2,f3,f7",
        "fields2": (
            "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,"
            "f61,f62,f63,f64,f65"
        ),
        "secid": SECID,
        "lmt": "5",
        "klt": "1",  # 1分钟
        "ut": UT,
        "_": _timestamp(),
    }

    data = _request_and_report(session, url, params, "个股资金流分钟")
    klines = data.get("data", {}).get("klines", [])
    if klines:
        for kline in klines:
            print(f"  {kline}")


def test_market_fund_flow(session: requests.Session) -> None:
    """验证3: 大盘资金流 (上证指数)"""
    _print_banner("验证3: 大盘资金流 — 上证指数(1.000001)")

    url = "https://push2.eastmoney.com/api/qt/ulist.np/get"
    params = {
        "fields": (
            "f1,f2,f3,f4,f6,f12,f13,f14,f152,f168,"
            "f169,f170,f171"
        ),
        "fltt": "2",
        "secids": "1.000001",
        "_": _timestamp(),
    }

    data = _request_and_report(session, url, params, "大盘资金流")
    diff = data.get("data", {}).get("diff", [])
    if diff:
        item = diff[0]
        # f14=名称, f2=最新价, f3=涨跌幅, f6=成交额, f62=主力净流入
        print(
            f"  关键字段 — 名称: {item.get('f14')}, "
            f"最新: {item.get('f2')}, "
            f"涨跌幅: {item.get('f3')}%, "
            f"成交额: {item.get('f6')}"
        )


def test_sector_fund_flow(session: requests.Session) -> None:
    """验证4: 板块资金流 (行业板块TOP20)"""
    _print_banner("验证4: 板块资金流 — 行业板块TOP20")

    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": "1",
        "pz": "20",
        "po": "1",
        "np": "1",
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": "2",
        "invt": "2",
        "fid": "f62",
        "fs": "m:90+t:2+f:!50",
        "fields": (
            "f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f14,"
            "f62,f184,f66,f69,f72,f75,f78,f164"
        ),
    }

    data = _request_and_report(session, url, params, "板块资金流")
    diff = data.get("data", {}).get("diff", [])
    if diff:
        # f14=板块名称, f3=涨跌幅, f62=主力净流入, f164=主力净流入占比
        for item in diff[:5]:
            print(
                f"  {item.get('f14', ''):8s} | "
                f"涨跌幅: {item.get('f3', 'N/A')}% | "
                f"主力净流入: {item.get('f62', 'N/A')} | "
                f"主力净占比: {item.get('f164', 'N/A')}%"
            )


# ---------- 主入口 ----------

def main() -> None:
    """依次执行全部4项验证，每项之间间隔1.5秒"""
    session = requests.Session()
    session.headers.update(HEADERS)

    tests = [
        test_stock_fund_flow_daily,
        test_stock_fund_flow_minute,
        test_market_fund_flow,
        test_sector_fund_flow,
    ]

    print(f"开始验证东方财富资金流向接口 — 标的: {STOCK_NAME}({STOCK_CODE})")
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
