"""同花顺JSONP API端点全量探测脚本 (PoC)

以海天味业(603288)为基础，验证同花顺各数据域的JSONP API端点可用性。
重点验证分钟线数据获取能力。
"""

import os

for _proxy_key in [
    "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
    "ALL_PROXY", "all_proxy", "no_proxy", "NO_PROXY",
]:
    os.environ.pop(_proxy_key, None)

import json
import re
import time
from dataclasses import dataclass, field
from typing import Any

import requests


_REQUEST_INTERVAL: float = 1.5

_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://stockpage.10jqka.com.cn/",
}

_CODE_SH: str = "600519"
_CODE_SZ: str = "000858"
_CODE_HS_SH: str = "hs_600519"
_CODE_HS_SZ: str = "hs_000858"


@dataclass
class ProbeResult:
    name: str
    url: str
    status_code: int = 0
    data_rows: int = 0
    key_fields: list[str] = field(default_factory=list)
    response_ms: float = 0.0
    success: bool = False
    error_msg: str = ""
    sample_data: str = ""


def _parse_jsonp(text: str) -> dict[str, Any]:
    m = re.search(r'\((\{.*\})\)', text, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return {}


def _parse_csv_lines(text: str) -> int:
    lines = [l for l in text.strip().split(";") if l.strip()]
    return len(lines)


def probe_jsonp(
    name: str,
    url: str,
    session: requests.Session,
    is_jsonp: bool = True,
) -> ProbeResult:
    result = ProbeResult(name=name, url=url)

    try:
        start = time.time()
        resp = session.get(url, headers=_HEADERS, timeout=15)
        elapsed_ms = (time.time() - start) * 1000

        result.status_code = resp.status_code
        result.response_ms = round(elapsed_ms, 1)

        if resp.status_code != 200:
            result.error_msg = f"HTTP {resp.status_code}: {resp.text[:200]}"
            return result

        raw_text = resp.text

        if is_jsonp:
            data = _parse_jsonp(raw_text)
            if data:
                result.success = True
                result.data_rows = _count_json_rows(data)
                result.key_fields = _extract_json_fields(data)
                result.sample_data = json.dumps(data, ensure_ascii=False)[:300]
            else:
                csv_count = _parse_csv_lines(raw_text)
                if csv_count > 0:
                    result.success = True
                    result.data_rows = csv_count
                    result.sample_data = raw_text[:300]
                else:
                    result.error_msg = "无法解析JSONP/CSV"
                    result.sample_data = raw_text[:300]
        else:
            csv_count = _parse_csv_lines(raw_text)
            if csv_count > 0:
                result.success = True
                result.data_rows = csv_count
                result.sample_data = raw_text[:300]
            else:
                try:
                    data = json.loads(raw_text)
                    result.success = True
                    result.data_rows = _count_json_rows(data)
                    result.key_fields = _extract_json_fields(data)
                    result.sample_data = json.dumps(data, ensure_ascii=False)[:300]
                except (json.JSONDecodeError, ValueError):
                    result.error_msg = "非JSON/CSV格式"
                    result.sample_data = raw_text[:300]

    except requests.exceptions.Timeout:
        result.error_msg = "请求超时(15s)"
    except requests.exceptions.ConnectionError as e:
        result.error_msg = f"连接失败: {e}"
    except Exception as e:
        result.error_msg = f"异常: {type(e).__name__}: {e}"

    return result


def _count_json_rows(data: dict[str, Any]) -> int:
    if not isinstance(data, dict):
        return 0
    for key in ("data", "diff", "klines", "trends", "list", "items"):
        val = data.get(key)
        if isinstance(val, list):
            return len(val)
        if isinstance(val, dict):
            for sub_key in ("diff", "klines", "trends", "list", "items"):
                sub_val = val.get(sub_key)
                if isinstance(sub_val, list):
                    return len(sub_val)
    return 1 if data else 0


def _extract_json_fields(data: dict[str, Any]) -> list[str]:
    if not isinstance(data, dict):
        return []
    inner = data.get("data", data)
    if isinstance(inner, dict):
        return list(inner.keys())[:8]
    if isinstance(inner, list) and inner:
        first = inner[0]
        if isinstance(first, dict):
            return list(first.keys())[:8]
        if isinstance(first, str):
            return first.split(",")[:5]
    return []


def build_endpoints() -> list[tuple[str, str, bool]]:
    endpoints: list[tuple[str, str, bool]] = []

    # === 1. 分钟线数据 (核心目标) ===
    for period_code, period_name in [
        ("01", "1分钟"), ("05", "5分钟"),
        ("15", "15分钟"), ("30", "30分钟"), ("60", "60分钟"),
    ]:
        for year in [2024, 2025, 2026]:
            endpoints.append((
                f"分钟线-{period_name}-{year}年",
                f"http://d.10jqka.com.cn/v2/line/{_CODE_HS_SH}/{period_code}/{year}.js",
                True,
            ))

    # === 2. 实时行情头 ===
    endpoints.append((
        "实时行情-贵州茅台",
        f"http://d.10jqka.com.cn/v2/realhead/{_CODE_HS_SH}/last.js",
        True,
    ))
    endpoints.append((
        "实时行情-五粮液",
        f"http://d.10jqka.com.cn/v2/realhead/{_CODE_HS_SZ}/last.js",
        True,
    ))

    # === 3. 个股详情 ===
    endpoints.append((
        "个股详情-贵州茅台",
        f"http://d.10jqka.com.cn/v2/stockhead/{_CODE_HS_SH}/last.js",
        True,
    ))

    # === 4. 行情排行 ===
    for page in [1, 2]:
        endpoints.append((
            f"行情排行-全部A股-第{page}页",
            f"http://q.10jqka.com.cn/index/index/board/all/field/zdf/order/desc/page/{page}/ajax/1/",
            False,
        ))

    # === 5. 概念板块 ===
    endpoints.append((
        "概念板块列表",
        "http://q.10jqka.com.cn/thshy/",
        False,
    ))

    # === 6. 行业板块 ===
    endpoints.append((
        "行业板块列表",
        "http://q.10jqka.com.cn/thshy/board/",
        False,
    ))

    # === 7. 问财接口 ===
    endpoints.append((
        "问财-自然语言查询",
        "http://www.iwencai.com/customized/chart/get-robot-data",
        True,
    ))

    # === 8. 个股资金流向 ===
    endpoints.append((
        "个股资金流向-贵州茅台",
        f"http://d.10jqka.com.cn/v2/finance/hs_{_CODE_SH}/last.js",
        True,
    ))

    # === 9. 分时数据 ===
    endpoints.append((
        "分时数据-贵州茅台",
        f"http://d.10jqka.com.cn/v6/line/{_CODE_HS_SH}/01/last.js",
        True,
    ))
    endpoints.append((
        "分时数据-五粮液",
        f"http://d.10jqka.com.cn/v6/line/{_CODE_HS_SZ}/01/last.js",
        True,
    ))

    # === 10. K线数据(日/周/月) ===
    for freq_code, freq_name in [
        ("11", "日K"), ("21", "周K"), ("31", "月K"),
    ]:
        endpoints.append((
            f"K线-{freq_name}-贵州茅台",
            f"http://d.10jqka.com.cn/v2/line/{_CODE_HS_SH}/{freq_code}/2026.js",
            True,
        ))

    # === 11. 龙虎榜 ===
    endpoints.append((
        "龙虎榜",
        "http://d.10jqka.com.cn/v2/longhu/list/",
        True,
    ))

    # === 12. 大单追踪 ===
    endpoints.append((
        "大单追踪-贵州茅台",
        f"http://d.10jqka.com.cn/v2/finance/hs_{_CODE_SH}/bill/last.js",
        True,
    ))

    return endpoints


def main() -> None:
    print("=" * 80)
    print("同花顺 JSONP API 端点全量探测")
    print("=" * 80)

    session = requests.Session()
    endpoints = build_endpoints()
    results: list[ProbeResult] = []

    total = len(endpoints)
    success_count = 0

    for idx, (name, url, is_jsonp) in enumerate(endpoints, 1):
        print(f"\n[{idx}/{total}] 探测: {name}")
        print(f"  URL: {url}")

        result = probe_jsonp(name, url, session, is_jsonp)
        results.append(result)

        status_icon = "✅" if result.success else "❌"
        print(f"  {status_icon} 状态: {result.status_code} | "
              f"耗时: {result.response_ms}ms | "
              f"数据行: {result.data_rows}")

        if result.success:
            success_count += 1
            if result.key_fields:
                print(f"  关键字段: {result.key_fields}")
            if result.sample_data:
                print(f"  数据样本: {result.sample_data[:200]}")
        else:
            print(f"  错误: {result.error_msg}")

        time.sleep(_REQUEST_INTERVAL)

    print("\n" + "=" * 80)
    print(f"探测完成: {total} 个端点, 成功 {success_count}, 失败 {total - success_count}")
    print("=" * 80)

    # 按类别汇总
    print("\n📊 按类别汇总:")
    categories: dict[str, list[ProbeResult]] = {}
    for r in results:
        cat = r.name.split("-")[0]
        categories.setdefault(cat, []).append(r)

    for cat, cat_results in categories.items():
        ok = sum(1 for r in cat_results if r.success)
        total_rows = sum(r.data_rows for r in cat_results if r.success)
        print(f"  {cat}: {ok}/{len(cat_results)} 成功, 共 {total_rows} 行数据")

    # 分钟线专项分析
    print("\n📈 分钟线数据专项分析:")
    minute_results = [r for r in results if r.name.startswith("分钟线")]
    for r in minute_results:
        status = "✅" if r.success else "❌"
        rows = f"{r.data_rows}行" if r.success else r.error_msg
        print(f"  {status} {r.name}: {rows}")

    # 反爬策略分析
    print("\n🔒 反爬策略分析:")
    failed = [r for r in results if not r.success]
    if failed:
        for r in failed:
            print(f"  ❌ {r.name}: {r.error_msg[:100]}")
    else:
        print("  所有端点均成功访问")


if __name__ == "__main__":
    main()
