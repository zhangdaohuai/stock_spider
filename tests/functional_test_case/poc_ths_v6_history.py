"""同花顺v6 API 1分钟线历史范围验证"""

import os

for _proxy_key in [
    "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
    "ALL_PROXY", "all_proxy",
]:
    os.environ.pop(_proxy_key, None)

import json
import re
import time
from typing import Any

import requests


_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://stockpage.10jqka.com.cn/",
}


def _parse_jsonp(text: str) -> dict[str, Any]:
    m = re.search(r'\((\{.*\})\)', text, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return {}


def main() -> None:
    s = requests.Session()

    # 1. v6 period=60 按年获取1分钟线
    print("=" * 60)
    print("v6 API period=60 按年获取1分钟线")
    print("=" * 60)
    for year in range(2020, 2027):
        url = f"http://d.10jqka.com.cn/v6/line/hs_600519/60/{year}.js"
        try:
            resp = s.get(url, headers=_HEADERS, timeout=15)
            if resp.status_code == 200:
                data = _parse_jsonp(resp.text)
                raw = data.get("data", "")
                total = data.get("total", "")
                name = data.get("name", "")
                if isinstance(raw, str) and raw:
                    lines = [l for l in raw.split(";") if l.strip()]
                    print(f"  ✅ {year}: {len(lines)}条, total={total}, name={name}")
                    if lines:
                        print(f"    首条: {lines[0][:120]}")
                        print(f"    末条: {lines[-1][:120]}")
                else:
                    print(f"  ⚠️ {year}: total={total}, 无data")
            else:
                print(f"  ❌ {year}: HTTP {resp.status_code}")
        except Exception as e:
            print(f"  ❌ {year}: {e}")
        time.sleep(0.5)

    # 2. v2 period=30 按年获取5分钟线
    print()
    print("=" * 60)
    print("v2 API period=30 按年获取5分钟线")
    print("=" * 60)
    for year in range(2020, 2027):
        url = f"http://d.10jqka.com.cn/v2/line/hs_600519/30/{year}.js"
        try:
            resp = s.get(url, headers=_HEADERS, timeout=15)
            if resp.status_code == 200:
                data = _parse_jsonp(resp.text)
                raw = data.get("data", "")
                if isinstance(raw, str) and raw:
                    lines = [l for l in raw.split(";") if l.strip()]
                    print(f"  ✅ {year}: {len(lines)}条")
                    if lines:
                        print(f"    首条: {lines[0][:120]}")
                        print(f"    末条: {lines[-1][:120]}")
                else:
                    print(f"  ⚠️ {year}: 无data")
            else:
                print(f"  ❌ {year}: HTTP {resp.status_code}")
        except Exception as e:
            print(f"  ❌ {year}: {e}")
        time.sleep(0.5)

    # 3. v2 period=40/50 按年获取30/60分钟线
    print()
    print("=" * 60)
    print("v2 API period=40/50 按年获取30/60分钟线")
    print("=" * 60)
    for period, name in [(40, "30分钟"), (50, "60分钟")]:
        for year in [2024, 2025, 2026]:
            url = f"http://d.10jqka.com.cn/v2/line/hs_600519/{period}/{year}.js"
            try:
                resp = s.get(url, headers=_HEADERS, timeout=15)
                if resp.status_code == 200:
                    data = _parse_jsonp(resp.text)
                    raw = data.get("data", "")
                    if isinstance(raw, str) and raw:
                        lines = [l for l in raw.split(";") if l.strip()]
                        print(f"  ✅ {name}-{year}: {len(lines)}条")
                        if lines:
                            print(f"    首条: {lines[0][:120]}")
                    else:
                        print(f"  ⚠️ {name}-{year}: 无data")
                else:
                    print(f"  ❌ {name}-{year}: HTTP {resp.status_code}")
            except Exception as e:
                print(f"  ❌ {name}-{year}: {e}")
            time.sleep(0.5)

    # 4. v6 period=60 last.js 详细分析
    print()
    print("=" * 60)
    print("v6 API period=60 last.js 详细分析")
    print("=" * 60)
    url = "http://d.10jqka.com.cn/v6/line/hs_600519/60/last.js"
    try:
        resp = s.get(url, headers=_HEADERS, timeout=15)
        data = _parse_jsonp(resp.text)
        print(f"  顶层键: {list(data.keys())}")
        print(f"  total: {data.get('total')}")
        print(f"  name: {data.get('name')}")
        print(f"  start: {data.get('start')}")
        print(f"  rt: {data.get('rt')}")
        raw = data.get("data", "")
        if isinstance(raw, str) and raw:
            lines = [l for l in raw.split(";") if l.strip()]
            print(f"  data: {len(lines)}条")
            if lines:
                print(f"    首条: {lines[0][:120]}")
                print(f"    末条: {lines[-1][:120]}")
                first_ts = lines[0].split(",")[0]
                last_ts = lines[-1].split(",")[0]
                print(f"    时间范围: {first_ts} -> {last_ts}")
    except Exception as e:
        print(f"  ❌ {e}")


if __name__ == "__main__":
    main()
