"""东方财富API端点全量探测脚本 (PoC)

以海天味业(603288, secid=1.603288)为基础，
验证东方财富各数据域的REST API端点可用性。
"""

import os

# 清除代理设置，确保直连东方财富
for _proxy_key in [
    "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
    "ALL_PROXY", "all_proxy", "no_proxy", "NO_PROXY",
]:
    os.environ.pop(_proxy_key, None)

import json
import time
from dataclasses import dataclass, field
from typing import Any

import requests


# 请求间隔（秒）
_REQUEST_INTERVAL: float = 1.5

# 通用请求头
_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://quote.eastmoney.com/",
}

# 海天味业基础参数
_SECID: str = "1.603288"
_CODE: str = "SH603288"
_SECURITY_CODE: str = "603288"


@dataclass
class ProbeResult:
    """单次API探测结果"""

    name: str
    url: str
    status_code: int = 0
    data_rows: int = 0
    key_fields: list[str] = field(default_factory=list)
    response_ms: float = 0.0
    success: bool = False
    error_msg: str = ""


def _extract_data_rows(data: dict[str, Any]) -> int:
    """从不同格式的响应中提取数据行数"""
    if not data or not isinstance(data, dict):
        return 0

    # push2 行情类接口: data.diff 是列表
    diff = _safe_get(data, "data", "diff")
    if isinstance(diff, list):
        return len(diff)

    # K线接口: data.klines 是列表
    klines = _safe_get(data, "data", "klines")
    if isinstance(klines, list):
        return len(klines)

    # 分时线接口: data.trends 是列表
    trends = _safe_get(data, "data", "trends")
    if isinstance(trends, list):
        return len(trends)

    # datacenter 接口: result.data 是列表
    dc_data = _safe_get(data, "result", "data")
    if isinstance(dc_data, list):
        return len(dc_data)

    # data 直接为列表（F10类接口可能返回列表）
    inner_data = data.get("data")
    if isinstance(inner_data, list):
        return len(inner_data)

    # 单条数据对象（如实时行情），算1行
    if isinstance(inner_data, dict) and inner_data:
        return 1

    return 0


def _extract_key_fields(data: dict[str, Any]) -> list[str]:
    """从响应中提取关键字段名列表"""
    fields: list[str] = []

    if not data or not isinstance(data, dict):
        return fields

    inner = data.get("data")
    if isinstance(inner, dict):
        # 取前8个字段名作为关键展示
        fields = list(inner.keys())[:8]
    elif isinstance(inner, list) and inner:
        first = inner[0]
        if isinstance(first, dict):
            fields = list(first.keys())[:8]
        elif isinstance(first, str):
            # 逗号分隔的字符串行，取前3个值
            fields = first.split(",")[:3]

    # datacenter 格式
    result = data.get("result")
    if isinstance(result, dict):
        dc_data = result.get("data")
        if isinstance(dc_data, list) and dc_data:
            first = dc_data[0]
            if isinstance(first, dict):
                fields = list(first.keys())[:8]

    return fields


def _safe_get(data: dict[str, Any], *keys: str) -> Any:
    """安全嵌套取值"""
    current: Any = data  # type: ignore[assignment]
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)  # type: ignore[assignment]
        else:
            return None
    return current


def probe_api(
    name: str,
    url: str,
    params: dict[str, str],
    session: requests.Session,
) -> ProbeResult:
    """探测单个API端点，记录状态码、数据行数、关键字段和响应时间"""
    result = ProbeResult(name=name, url=url)

    try:
        start = time.time()
        resp = session.get(url, params=params, headers=_HEADERS, timeout=15)
        elapsed_ms = (time.time() - start) * 1000

        result.status_code = resp.status_code
        result.response_ms = round(elapsed_ms, 1)

        if resp.status_code != 200:
            result.error_msg = f"HTTP {resp.status_code}"
            return result

        data = resp.json()
        result.data_rows = _extract_data_rows(data)
        result.key_fields = _extract_key_fields(data)

        # 判断业务层是否成功
        rc = _safe_get(data, "rc") or _safe_get(data, "code")
        if rc is not None and rc not in (0, "0"):
            result.error_msg = f"rc={rc}, msg={_safe_get(data, 'message', 'msg')}"
            return result

        # data 为空也视为失败
        if data.get("data") is None and data.get("result") is None:
            result.error_msg = "data/result为空"
            return result

        result.success = True

    except requests.Timeout:
        result.error_msg = "请求超时(15s)"
    except requests.ConnectionError:
        result.error_msg = "连接失败"
    except json.JSONDecodeError:
        result.error_msg = "响应非JSON"
    except Exception as exc:
        result.error_msg = str(exc)[:80]

    return result


# ------------------------------------------------------------------
# 20个API端点定义
# ------------------------------------------------------------------

def _build_api_specs() -> list[dict[str, Any]]:
    """构建全部20个API探测规格"""
    ts = str(int(time.time() * 1000))
    specs: list[dict[str, Any]] = []

    # 1. 实时行情
    specs.append({
        "name": "实时行情",
        "url": "https://push2.eastmoney.com/api/qt/stock/get",
        "params": {
            "ut": "fa5fd1943c7b386f172d6893dbfba10b",
            "invt": "2", "fltt": "2",
            "fields": (
                "f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,"
                "f55,f57,f58,f60,f107,f116,f117,f152,f168,"
                "f169,f170,f171"
            ),
            "secid": _SECID, "_": ts,
        },
    })

    # 2. 批量行情列表（沪深A股）
    specs.append({
        "name": "批量行情列表",
        "url": "https://push2.eastmoney.com/api/qt/clist/get",
        "params": {
            "pn": "1", "pz": "20", "po": "1", "np": "1",
            "ut": "bd1d9ddb04089700cf9c27f6f7426281",
            "fltt": "2", "invt": "2", "fid": "f3",
            "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048",
            "fields": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18",
        },
    })

    # 3. K线历史（日线）
    specs.append({
        "name": "K线历史-日线",
        "url": "https://push2his.eastmoney.com/api/qt/stock/kline/get",
        "params": {
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "klt": "101", "fqt": "1",
            "secid": _SECID,
            "beg": "0", "end": "20500000", "lmt": "10",
            "ut": "fa5fd1943c7b386f172d6893dbfba10b", "_": ts,
        },
    })

    # 4. K线历史（5分钟）
    specs.append({
        "name": "K线历史-5分钟",
        "url": "https://push2his.eastmoney.com/api/qt/stock/kline/get",
        "params": {
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "klt": "5", "fqt": "1",
            "secid": _SECID,
            "beg": "0", "end": "20500000", "lmt": "10",
            "ut": "fa5fd1943c7b386f172d6893dbfba10b", "_": ts,
        },
    })

    # 5. K线历史（1分钟）
    specs.append({
        "name": "K线历史-1分钟",
        "url": "https://push2his.eastmoney.com/api/qt/stock/kline/get",
        "params": {
            "fields1": "f1,f2,f3,f4,f5,f6",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
            "klt": "1", "fqt": "1",
            "secid": _SECID,
            "beg": "0", "end": "20500000", "lmt": "10",
            "ut": "fa5fd1943c7b386f172d6893dbfba10b", "_": ts,
        },
    })

    # 6. 分时线
    specs.append({
        "name": "分时线",
        "url": "https://push2his.eastmoney.com/api/qt/stock/trends2/get",
        "params": {
            "fields1": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58",
            "iscr": "0", "secid": _SECID, "ndays": "1",
            "ut": "fa5fd1943c7b386f172d6893dbfba10b", "_": ts,
        },
    })

    # 7. 五档盘口（含买卖盘字段）
    specs.append({
        "name": "五档盘口",
        "url": "https://push2.eastmoney.com/api/qt/stock/get",
        "params": {
            "ut": "fa5fd1943c7b386f172d6893dbfba10b",
            "invt": "2", "fltt": "2",
            "fields": (
                "f19,f20,f21,f22,f23,f24,f25,f26,f27,f28,"
                "f29,f30,f31,f32,f33,f34,f35,f36,f37,f38,"
                "f39,f40,f41,f42,f43,f44,f45,f46,f47,f48"
            ),
            "secid": _SECID, "_": ts,
        },
    })

    # 8. 资金流向（日K线）
    specs.append({
        "name": "资金流向",
        "url": "https://push2.eastmoney.com/api/qt/stock/fflow/daykline/get",
        "params": {
            "fields1": "f1,f2,f3,f7",
            "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63",
            "secid": _SECID,
            "ut": "fa5fd1943c7b386f172d6893dbfba10b", "_": ts,
        },
    })

    # 9. 数据中心-业绩报表
    specs.append({
        "name": "业绩报表",
        "url": "https://datacenter-web.eastmoney.com/api/data/v1/get",
        "params": {
            "reportName": "RPT_LICO_FN_CPD",
            "columns": "ALL",
            "filter": f'(SECURITY_CODE="{_SECURITY_CODE}")',
            "pageNumber": "1", "pageSize": "5",
            "sortColumns": "REPORT_DATE", "sortTypes": "-1",
        },
    })

    # 10. F10公司概况
    specs.append({
        "name": "F10公司概况",
        "url": (
            "https://emweb.securities.eastmoney.com/"
            "PC_HSF10/CompanySurvey/PageAjax"
        ),
        "params": {"code": _CODE},
    })

    # 11. F10财务分析
    specs.append({
        "name": "F10财务分析",
        "url": (
            "https://emweb.securities.eastmoney.com/"
            "PC_HSF10/NewFinanceAnalysis/ZYZBAjaxNew"
        ),
        "params": {"type": "0", "code": _CODE},
    })

    # 12. F10股东研究
    specs.append({
        "name": "F10股东研究",
        "url": (
            "https://emweb.securities.eastmoney.com/"
            "PC_HSF10/ShareholderResearch/PageAjax"
        ),
        "params": {"code": _CODE},
    })

    # 13. 龙虎榜
    specs.append({
        "name": "龙虎榜",
        "url": "https://datacenter-web.eastmoney.com/api/data/v1/get",
        "params": {
            "reportName": "RDT_BILLBOARD_DAILYDETAIL",
            "columns": "ALL",
            "filter": f'(SECURITY_CODE="{_SECURITY_CODE}")',
            "pageNumber": "1", "pageSize": "5",
            "sortColumns": "TRADE_DATE", "sortTypes": "-1",
        },
    })

    # 14. 融资融券
    specs.append({
        "name": "融资融券",
        "url": "https://datacenter-web.eastmoney.com/api/data/v1/get",
        "params": {
            "reportName": "RPT_RZRQ_LSHJ",
            "columns": "ALL",
            "filter": f'(SECURITY_CODE="{_SECURITY_CODE}")',
            "pageNumber": "1", "pageSize": "5",
            "sortColumns": "TRADE_DATE", "sortTypes": "-1",
        },
    })

    # 15. 股权质押
    specs.append({
        "name": "股权质押",
        "url": "https://datacenter-web.eastmoney.com/api/data/v1/get",
        "params": {
            "reportName": "RPT_CSDC_LIST",
            "columns": "ALL",
            "filter": f'(SECURITY_CODE="{_SECURITY_CODE}")',
            "pageNumber": "1", "pageSize": "5",
            "sortColumns": "END_DATE", "sortTypes": "-1",
        },
    })

    # 16. 大宗交易
    specs.append({
        "name": "大宗交易",
        "url": "https://datacenter-web.eastmoney.com/api/data/v1/get",
        "params": {
            "reportName": "RPT_DABLOCK_TRADE",
            "columns": "ALL",
            "filter": f'(SECURITY_CODE="{_SECURITY_CODE}")',
            "pageNumber": "1", "pageSize": "5",
            "sortColumns": "TRADE_DATE", "sortTypes": "-1",
        },
    })

    # 17. 分红送配
    specs.append({
        "name": "分红送配",
        "url": "https://datacenter-web.eastmoney.com/api/data/v1/get",
        "params": {
            "reportName": "RPT_DIVIDEND_PLAN",
            "columns": "ALL",
            "filter": f'(SECURITY_CODE="{_SECURITY_CODE}")',
            "pageNumber": "1", "pageSize": "5",
            "sortColumns": "REPORT_DATE", "sortTypes": "-1",
        },
    })

    # 18. 限售解禁
    specs.append({
        "name": "限售解禁",
        "url": "https://datacenter-web.eastmoney.com/api/data/v1/get",
        "params": {
            "reportName": "RPT_RESOLVE_EXPLAIN",
            "columns": "ALL",
            "filter": f'(SECURITY_CODE="{_SECURITY_CODE}")',
            "pageNumber": "1", "pageSize": "5",
            "sortColumns": "END_DATE", "sortTypes": "-1",
        },
    })

    # 19. 公告
    specs.append({
        "name": "公告",
        "url": "https://np-anotice-stock.eastmoney.com/api/security/ann",
        "params": {
            "page_size": "5", "page_index": "1",
            "ann_type": "A", "stock_list": _SECURITY_CODE,
            "f_node": "0", "s_node": "0",
        },
    })

    # 20. 沪深港通资金
    specs.append({
        "name": "沪深港通",
        "url": "https://push2his.eastmoney.com/api/qt/kamtbs.wss/get",
        "params": {
            "fields1": "f1,f2,f3,f4",
            "fields2": "f51,f52,f53,f54,f55,f56",
            "ut": "fa5fd1943c7b386f172d6893dbfba10b", "_": ts,
        },
    })

    return specs


def run_all_probes() -> list[ProbeResult]:
    """依次探测全部API端点，返回结果列表"""
    specs = _build_api_specs()
    results: list[ProbeResult] = []
    session = requests.Session()

    total = len(specs)
    for idx, spec in enumerate(specs, 1):
        print(f"[{idx}/{total}] 探测: {spec['name']} ...", end=" ", flush=True)
        result = probe_api(
            name=spec["name"],
            url=spec["url"],
            params=spec["params"],
            session=session,
        )
        results.append(result)

        # 实时输出单条结果
        status = "OK" if result.success else "FAIL"
        print(
            f"[{status}] "
            f"HTTP={result.status_code} "
            f"rows={result.data_rows} "
            f"耗时={result.response_ms:.0f}ms"
        )
        if not result.success and result.error_msg:
            print(f"         错误: {result.error_msg}")

        # 请求间隔，最后一条不等
        if idx < total:
            time.sleep(_REQUEST_INTERVAL)

    session.close()
    return results


def print_summary_table(results: list[ProbeResult]) -> None:
    """输出格式化的验证结果汇总表"""
    passed = sum(1 for r in results if r.success)
    failed = len(results) - passed

    # 表头
    header = (
        f"{'序号':>4}  {'API名称':<14} {'状态':<6} "
        f"{'HTTP':>4} {'行数':>5} {'耗时ms':>8}  {'关键字段'}"
    )
    sep = "-" * len(header)

    print("\n" + "=" * 80)
    print("东方财富API端点探测结果汇总")
    print(f"目标: 海天味业(603288, secid={_SECID})")
    print("=" * 80)
    print(header)
    print(sep)

    for idx, r in enumerate(results, 1):
        status = "PASS" if r.success else "FAIL"
        fields_str = ",".join(r.key_fields[:5]) if r.key_fields else "-"
        print(
            f"{idx:>4}  {r.name:<14} {status:<6} "
            f"{r.status_code:>4} {r.data_rows:>5} {r.response_ms:>8.0f}  {fields_str}"
        )

    print(sep)
    print(f"验证通过: {passed}  |  验证失败: {failed}  |  总计: {len(results)}")
    print("=" * 80)

    # 失败详情
    if failed > 0:
        print("\n失败详情:")
        for idx, r in enumerate(results, 1):
            if not r.success:
                print(f"  [{idx}] {r.name}: {r.error_msg}")
                print(f"       URL: {r.url}")


def main() -> None:
    """主入口"""
    print("东方财富API端点全量探测")
    print(f"目标股票: 海天味业(603288, secid={_SECID})")
    print(f"请求间隔: {_REQUEST_INTERVAL}s")
    print(f"探测端点数: 20")
    print()

    results = run_all_probes()
    print_summary_table(results)


if __name__ == "__main__":
    main()
