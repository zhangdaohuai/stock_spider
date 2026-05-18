"""东方财富行情接口验证脚本 — 实时行情+K线+分时+盘口"""

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
    """发送 GET 请求并打印状态码、响应时间、数据行数等摘要信息

    返回原始 JSON 字典，便于调用方提取关键字段。
    """
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
                # 单条记录(如实时行情)
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

def test_realtime_quote(session: requests.Session) -> None:
    """验证1: 实时行情"""
    _print_banner(f"验证1: 实时行情 — {STOCK_NAME}({STOCK_CODE})")

    url = "https://push2.eastmoney.com/api/qt/stock/get"
    params = {
        "ut": UT,
        "invt": "2",
        "fltt": "2",
        "fields": (
            "f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,"
            "f55,f57,f58,f60,f107,f116,f117,f152,f168,"
            "f169,f170,f171"
        ),
        "secid": SECID,
        "_": _timestamp(),
    }

    data = _request_and_report(session, url, params, "实时行情")
    inner = data.get("data", {})
    if inner:
        # 关键字段映射: f57=代码, f58=名称, f43=最新价, f169=涨跌额, f170=涨跌幅
        print(
            f"  关键字段 — 代码: {inner.get('f57')}, "
            f"名称: {inner.get('f58')}, "
            f"最新价: {inner.get('f43')}, "
            f"涨跌额: {inner.get('f169')}, "
            f"涨跌幅: {inner.get('f170')}%"
        )


def test_daily_kline(session: requests.Session) -> None:
    """验证2: 日线K线 (最近30条)"""
    _print_banner(f"验证2: 日线K线 — {STOCK_NAME}({STOCK_CODE})")

    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": (
            "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61"
        ),
        "klt": "101",  # 日线
        "fqt": "1",     # 前复权
        "secid": SECID,
        "beg": "0",
        "end": "20500000",
        "lmt": "30",
        "ut": UT,
        "_": _timestamp(),
    }

    data = _request_and_report(session, url, params, "日线K线")
    klines = data.get("data", {}).get("klines", [])
    if klines:
        # K线格式: 日期,开盘,收盘,最高,最低,成交量,成交额,振幅,涨跌幅,涨跌额,换手率
        print(f"  最早: {klines[0]}")
        print(f"  最新: {klines[-1]}")


def test_5min_kline(session: requests.Session) -> None:
    """验证3: 5分钟K线 (最近48条)"""
    _print_banner(f"验证3: 5分钟K线 — {STOCK_NAME}({STOCK_CODE})")

    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": (
            "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61"
        ),
        "klt": "5",   # 5分钟线
        "fqt": "1",
        "secid": SECID,
        "beg": "0",
        "end": "20500000",
        "lmt": "48",
        "ut": UT,
        "_": _timestamp(),
    }

    data = _request_and_report(session, url, params, "5分钟K线")
    klines = data.get("data", {}).get("klines", [])
    if klines:
        print(f"  最早: {klines[0]}")
        print(f"  最新: {klines[-1]}")


def test_1min_kline(session: requests.Session) -> None:
    """验证4: 1分钟K线 (最近240条)"""
    _print_banner(f"验证4: 1分钟K线 — {STOCK_NAME}({STOCK_CODE})")

    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": (
            "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61"
        ),
        "klt": "1",   # 1分钟线
        "fqt": "1",
        "secid": SECID,
        "beg": "0",
        "end": "20500000",
        "lmt": "240",
        "ut": UT,
        "_": _timestamp(),
    }

    data = _request_and_report(session, url, params, "1分钟K线")
    klines = data.get("data", {}).get("klines", [])
    if klines:
        print(f"  最早: {klines[0]}")
        print(f"  最新: {klines[-1]}")


def test_trends(session: requests.Session) -> None:
    """验证5: 分时线 (当日)"""
    _print_banner(f"验证5: 分时线 — {STOCK_NAME}({STOCK_CODE})")

    url = "https://push2his.eastmoney.com/api/qt/stock/trends2/get"
    params = {
        "fields1": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58",
        "iscr": "0",
        "secid": SECID,
        "ndays": "1",
        "ut": UT,
        "_": _timestamp(),
    }

    data = _request_and_report(session, url, params, "分时线")
    trends = data.get("data", {}).get("trends", [])
    if trends:
        # 分时格式: 时间,现价,均价,成交量,成交额...
        print(f"  最早: {trends[0]}")
        print(f"  最新: {trends[-1]}")


def test_order_book(session: requests.Session) -> None:
    """验证6: 五档盘口"""
    _print_banner(f"验证6: 五档盘口 — {STOCK_NAME}({STOCK_CODE})")

    url = "https://push2.eastmoney.com/api/qt/stock/get"
    params = {
        "ut": UT,
        "fltt": "2",
        "invt": "2",
        "fields": (
            "f120,f121,f122,f174,f175,f59,f163,f43,f57,f58,"
            "f169,f170,f46,f44,f51,f168,f47,f164,f116,f60,"
            "f45,f52,f50,f48,f167,f117,f71,f161,f49,f530,"
            "f135,f136,f137,f138,f139,f141,f142,f144,f145,"
            "f147,f148,f140,f143,f146,f149,f55,f62,f162"
        ),
        "secid": SECID,
        "_": _timestamp(),
    }

    data = _request_and_report(session, url, params, "五档盘口")
    inner = data.get("data", {})
    if inner:
        # 五档买卖盘: f135~f139=买1~5量, f140~f144=买1~5价, f145~f149=卖1~5量/价
        print(
            f"  关键字段 — 代码: {inner.get('f57')}, "
            f"名称: {inner.get('f58')}, "
            f"最新价: {inner.get('f43')}, "
            f"买一价: {inner.get('f140')}, "
            f"卖一价: {inner.get('f141')}"
        )


# ---------- 主入口 ----------

def main() -> None:
    """依次执行全部6项验证，每项之间间隔1.5秒"""
    session = requests.Session()
    session.headers.update(HEADERS)

    tests = [
        test_realtime_quote,
        test_daily_kline,
        test_5min_kline,
        test_1min_kline,
        test_trends,
        test_order_book,
    ]

    print(f"开始验证东方财富行情接口 — 标的: {STOCK_NAME}({STOCK_CODE})")
    print(f"共 {len(tests)} 项验证，请求间隔 {REQUEST_INTERVAL}s")

    for idx, test_fn in enumerate(tests):
        test_fn(session)
        # 最后一项不需要等待
        if idx < len(tests) - 1:
            time.sleep(REQUEST_INTERVAL)

    print("\n" + "=" * 70)
    print("  全部验证完成")
    print("=" * 70)


if __name__ == "__main__":
    main()
