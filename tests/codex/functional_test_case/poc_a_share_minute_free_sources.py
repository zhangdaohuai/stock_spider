"""Probe free-ish A-share historical minute-bar sources.

This script is intentionally a small-sample validator, not a downloader.
It checks availability, historical depth, response shape, and rough latency
for candidate free sources found during source research.

Default providers:
  - baostock: official free Python package, 5/15/30/60 minute bars
  - akshare: free wrapper, mostly Eastmoney-backed minute bars
  - eastmoney: direct push2his HTTP endpoint used by many wrappers
  - pytdx: public Tongdaxin quote servers through pytdx

Optional providers:
  - ths: unofficial Tonghuashun webpage endpoints; only runs when explicitly
    requested because endpoint and policy stability are weaker.

Example:
  python tests/codex/functional_test_case/poc_a_share_minute_free_sources.py
  python tests/codex/functional_test_case/poc_a_share_minute_free_sources.py --providers baostock,pytdx
  python tests/codex/functional_test_case/poc_a_share_minute_free_sources.py --providers ths --include-unofficial
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import os
import re
import socket
import sys
import time
import traceback
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_PROVIDERS = ("baostock", "akshare", "eastmoney", "pytdx")
DEFAULT_DATES = ("2016-01-04", "2019-01-02", "2020-01-02", "2024-01-02")
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "output"


@dataclass
class ProbeCase:
    name: str
    ok: bool
    skipped: bool = False
    rows: int | None = None
    latency_ms: int | None = None
    first_time: str | None = None
    last_time: str | None = None
    columns: list[str] = field(default_factory=list)
    message: str = ""
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderResult:
    provider: str
    ok: bool
    free_assumption: str
    historical_minute_claim: str
    reliability_hint: str
    cases: list[ProbeCase] = field(default_factory=list)
    message: str = ""


def _clear_proxy_env() -> None:
    for key in (
        "http_proxy",
        "https_proxy",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ALL_PROXY",
        "all_proxy",
    ):
        os.environ.pop(key, None)
    os.environ["NO_PROXY"] = "*"
    os.environ["no_proxy"] = "*"


def _module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _elapsed_ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


def _safe_columns(df: Any) -> list[str]:
    cols = getattr(df, "columns", [])
    try:
        return [str(c) for c in list(cols)]
    except Exception:
        return []


def _safe_len(obj: Any) -> int:
    try:
        return len(obj)
    except Exception:
        return 0


def _first_last_from_df(df: Any, preferred_columns: tuple[str, ...]) -> tuple[str | None, str | None]:
    if _safe_len(df) == 0:
        return None, None
    for col in preferred_columns:
        try:
            if col in df.columns:
                return str(df.iloc[0][col]), str(df.iloc[-1][col])
        except Exception:
            continue
    try:
        return str(df.iloc[0].to_dict()), str(df.iloc[-1].to_dict())
    except Exception:
        return None, None


def _json_get(url: str, params: dict[str, Any], timeout: float = 12.0) -> tuple[dict[str, Any], int]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
        ),
        "Referer": "https://quote.eastmoney.com/",
        "Accept": "application/json,text/plain,*/*",
    }
    full_url = f"{url}?{urlencode(params)}"
    request = Request(full_url, headers=headers)
    start = time.perf_counter()
    with urlopen(request, timeout=timeout) as resp:
        payload = resp.read().decode("utf-8", errors="replace")
    return json.loads(payload), _elapsed_ms(start)


def _text_get(url: str, timeout: float = 12.0, referer: str | None = None) -> tuple[str, int, int]:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
        ),
        "Accept": "text/html,application/json,text/plain,*/*",
    }
    if referer:
        headers["Referer"] = referer
    request = Request(url, headers=headers)
    start = time.perf_counter()
    with urlopen(request, timeout=timeout) as resp:
        status = getattr(resp, "status", 0)
        payload = resp.read().decode("utf-8", errors="replace")
    return payload, status, _elapsed_ms(start)


def probe_baostock(args: argparse.Namespace) -> ProviderResult:
    result = ProviderResult(
        provider="baostock",
        ok=False,
        free_assumption="Free, no token; anonymous login through baostock package.",
        historical_minute_claim="5/15/30/60 minute bars; no official 1-minute support in documented frequency set.",
        reliability_hint="Good candidate for free 5-minute historical validation, but local PoC must verify earliest usable minute date.",
    )
    if not _module_available("baostock"):
        result.message = "baostock is not installed; run in conda agent env or install baostock."
        result.cases.append(ProbeCase(name="import", ok=False, skipped=True, message=result.message))
        return result

    import baostock as bs  # type: ignore

    login_start = time.perf_counter()
    login = bs.login()
    result.cases.append(
        ProbeCase(
            name="login",
            ok=getattr(login, "error_code", "") == "0",
            latency_ms=_elapsed_ms(login_start),
            message=f"{getattr(login, 'error_code', '')}: {getattr(login, 'error_msg', '')}",
        )
    )

    if getattr(login, "error_code", "") != "0":
        result.message = "baostock login failed."
        try:
            bs.logout()
        except Exception:
            pass
        return result

    fields = "date,time,code,open,high,low,close,volume,amount,adjustflag"
    try:
        for frequency in ("1", "5", "15", "30", "60"):
            for day in args.dates:
                start = time.perf_counter()
                try:
                    rs = bs.query_history_k_data_plus(
                        args.baostock_code,
                        fields,
                        start_date=day,
                        end_date=day,
                        frequency=frequency,
                        adjustflag="3",
                    )
                    df = rs.get_data()
                    first, last = _first_last_from_df(df, ("time", "date"))
                    rows = _safe_len(df)
                    err = f"{getattr(rs, 'error_code', '')}: {getattr(rs, 'error_msg', '')}"
                    result.cases.append(
                        ProbeCase(
                            name=f"freq={frequency} date={day}",
                            ok=(getattr(rs, "error_code", "") == "0" and rows > 0),
                            rows=rows,
                            latency_ms=_elapsed_ms(start),
                            first_time=first,
                            last_time=last,
                            columns=_safe_columns(df),
                            message=err,
                        )
                    )
                except Exception as exc:
                    result.cases.append(
                        ProbeCase(
                            name=f"freq={frequency} date={day}",
                            ok=False,
                            latency_ms=_elapsed_ms(start),
                            message=str(exc),
                        )
                    )
                time.sleep(args.sleep)
    finally:
        try:
            bs.logout()
        except Exception:
            pass

    result.ok = any(case.ok for case in result.cases if case.name.startswith("freq=5"))
    return result


def probe_akshare(args: argparse.Namespace) -> ProviderResult:
    result = ProviderResult(
        provider="akshare",
        ok=False,
        free_assumption="Free Python package; no API key; many A-share minute APIs are Eastmoney-backed.",
        historical_minute_claim="1/5/15/30/60 minute supported by function signature, but historical depth is source-limited and must be tested.",
        reliability_hint="Useful as a wrapper, but not reliable as sole source for long historical 1-minute A-share bars.",
    )
    if not _module_available("akshare"):
        result.message = "akshare is not installed; run in conda agent env or install akshare."
        result.cases.append(ProbeCase(name="import", ok=False, skipped=True, message=result.message))
        return result

    import akshare as ak  # type: ignore

    result.cases.append(
        ProbeCase(
            name="version",
            ok=True,
            message=str(getattr(ak, "__version__", "unknown")),
        )
    )

    windows = [
        ("old_2020_1m", "1", "2020-01-02 09:30:00", "2020-01-02 15:00:00"),
        ("recent_1m", "1", args.recent_start, args.recent_end),
        ("old_2020_5m", "5", "2020-01-02 09:30:00", "2020-01-02 15:00:00"),
        ("recent_5m", "5", args.recent_start, args.recent_end),
    ]

    for name, period, start_date, end_date in windows:
        start = time.perf_counter()
        try:
            df = ak.stock_zh_a_hist_min_em(
                symbol=args.stock,
                period=period,
                start_date=start_date,
                end_date=end_date,
                adjust="",
            )
            first, last = _first_last_from_df(df, ("时间", "datetime", "date"))
            result.cases.append(
                ProbeCase(
                    name=name,
                    ok=_safe_len(df) > 0,
                    rows=_safe_len(df),
                    latency_ms=_elapsed_ms(start),
                    first_time=first,
                    last_time=last,
                    columns=_safe_columns(df),
                )
            )
        except Exception as exc:
            result.cases.append(
                ProbeCase(name=name, ok=False, latency_ms=_elapsed_ms(start), message=str(exc))
            )
        time.sleep(args.sleep)

    result.ok = any(case.ok for case in result.cases if case.name.startswith("recent"))
    return result


def probe_eastmoney(args: argparse.Namespace) -> ProviderResult:
    result = ProviderResult(
        provider="eastmoney_direct",
        ok=False,
        free_assumption="No key for public push2his endpoint, but this is an unofficial web API surface.",
        historical_minute_claim="K-line endpoint supports klt=1/5/15/30/60/101 parameters; accessible depth and anti-crawl behavior must be tested.",
        reliability_hint="Fast when reachable, but anti-crawl/IP blocking risk is high; use only with conservative rate limits and fallback.",
    )
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    for klt in ("1", "5"):
        for day in ("20200102", args.recent_beg):
            start = time.perf_counter()
            params = {
                "fields1": "f1,f2,f3,f4,f5,f6",
                "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
                "klt": klt,
                "fqt": "0",
                "secid": args.secid,
                "beg": day,
                "end": day,
                "lmt": "500",
                "ut": "fa5fd1943c7b386f172d6893dbfba10b",
                "_": str(int(time.time() * 1000)),
            }
            try:
                data, latency = _json_get(url, params, timeout=args.timeout)
                klines = (((data or {}).get("data") or {}).get("klines") or [])
                first = klines[0].split(",")[0] if klines else None
                last = klines[-1].split(",")[0] if klines else None
                result.cases.append(
                    ProbeCase(
                        name=f"klt={klt} date={day}",
                        ok=len(klines) > 0,
                        rows=len(klines),
                        latency_ms=latency,
                        first_time=first,
                        last_time=last,
                        message=f"rc={data.get('rc')} msg={data.get('message') or data.get('msg')}",
                    )
                )
            except (HTTPError, URLError, socket.timeout, TimeoutError) as exc:
                result.cases.append(
                    ProbeCase(
                        name=f"klt={klt} date={day}",
                        ok=False,
                        latency_ms=_elapsed_ms(start),
                        message=f"{type(exc).__name__}: {exc}",
                    )
                )
            except Exception as exc:
                result.cases.append(
                    ProbeCase(
                        name=f"klt={klt} date={day}",
                        ok=False,
                        latency_ms=_elapsed_ms(start),
                        message=str(exc),
                    )
                )
            time.sleep(args.sleep)

    result.ok = any(case.ok for case in result.cases)
    return result


def probe_pytdx(args: argparse.Namespace) -> ProviderResult:
    result = ProviderResult(
        provider="pytdx",
        ok=False,
        free_assumption="Free package; connects to public Tongdaxin quote servers; no formal SLA.",
        historical_minute_claim="get_security_bars supports 1-minute and 5-minute categories, count max 800 per call; older data requires paging.",
        reliability_hint="Good exploratory fallback for recent bars, but public server stability and long-range history depth require repeated validation.",
    )
    if not _module_available("pytdx"):
        result.message = "pytdx is not installed; install pytdx to run this probe."
        result.cases.append(ProbeCase(name="import", ok=False, skipped=True, message=result.message))
        return result

    from pytdx.hq import TdxHq_API  # type: ignore

    hosts = [tuple(host.split(":")) for host in args.tdx_hosts.split(",") if host.strip()]
    category_map = {"1m": 8, "5m": 0}
    for host, port_str in hosts:
        port = int(port_str)
        api = TdxHq_API(auto_retry=True)
        start = time.perf_counter()
        try:
            connected = api.connect(host, port, time_out=args.timeout)
            result.cases.append(
                ProbeCase(
                    name=f"connect {host}:{port}",
                    ok=bool(connected),
                    latency_ms=_elapsed_ms(start),
                )
            )
            if not connected:
                continue

            for label, category in category_map.items():
                all_rows: list[dict[str, Any]] = []
                for page in range(args.tdx_pages - 1, -1, -1):
                    offset = page * 800
                    call_start = time.perf_counter()
                    rows = api.get_security_bars(
                        category,
                        args.tdx_market,
                        args.stock,
                        offset,
                        800,
                    )
                    converted = api.to_df(rows or [])
                    if _safe_len(converted):
                        all_rows.extend(converted.to_dict("records"))
                    result.cases.append(
                        ProbeCase(
                            name=f"{label} {host}:{port} offset={offset}",
                            ok=_safe_len(converted) > 0,
                            rows=_safe_len(converted),
                            latency_ms=_elapsed_ms(call_start),
                            columns=_safe_columns(converted),
                        )
                    )
                    time.sleep(args.sleep)

                if all_rows:
                    result.cases.append(
                        ProbeCase(
                            name=f"{label} {host}:{port} aggregate",
                            ok=True,
                            rows=len(all_rows),
                            first_time=str(all_rows[0].get("datetime") or all_rows[0].get("date")),
                            last_time=str(all_rows[-1].get("datetime") or all_rows[-1].get("date")),
                            detail={"pages": args.tdx_pages, "page_size": 800},
                        )
                    )
            api.disconnect()
        except Exception as exc:
            result.cases.append(
                ProbeCase(
                    name=f"pytdx {host}:{port}",
                    ok=False,
                    latency_ms=_elapsed_ms(start),
                    message=str(exc),
                )
            )
            try:
                api.disconnect()
            except Exception:
                pass

    result.ok = any(case.ok and "aggregate" in case.name for case in result.cases)
    return result


def probe_ths(args: argparse.Namespace) -> ProviderResult:
    result = ProviderResult(
        provider="tonghuashun_unofficial",
        ok=False,
        free_assumption="No key observed for tested webpage endpoints, but this is unofficial and must respect robots/terms.",
        historical_minute_claim="Community findings mention recent minute bars, but depth and permission must be verified per endpoint.",
        reliability_hint="Research-only candidate; do not design production around it unless policy and stability are confirmed.",
    )
    if not args.include_unofficial:
        result.message = "Skipped; pass --include-unofficial to probe Tonghuashun webpage endpoints."
        result.cases.append(ProbeCase(name="skipped", ok=False, skipped=True, message=result.message))
        return result

    robots_start = time.perf_counter()
    try:
        robots, status, latency = _text_get("https://www.10jqka.com.cn/robots.txt", timeout=args.timeout)
        result.cases.append(
            ProbeCase(
                name="robots.txt",
                ok=status == 200,
                latency_ms=latency,
                message=robots[:300].replace("\n", " | "),
            )
        )
    except Exception as exc:
        result.cases.append(
            ProbeCase(name="robots.txt", ok=False, latency_ms=_elapsed_ms(robots_start), message=str(exc))
        )

    # The v2 endpoint pattern is already present in the project root poc_10jqka.py.
    for year in args.ths_years:
        url = f"http://d.10jqka.com.cn/v2/line/hs_{args.stock}/01/{year}.js"
        start = time.perf_counter()
        try:
            text, status, latency = _text_get(url, timeout=args.timeout, referer="http://q.10jqka.com.cn/")
            rows, first_time, last_time, parse_msg = _parse_ths_jsonp_rows(text)
            result.cases.append(
                ProbeCase(
                    name=f"v2 line 1m {year}.js",
                    ok=status == 200 and rows > 0,
                    rows=rows,
                    latency_ms=latency,
                    first_time=first_time,
                    last_time=last_time,
                    message=f"status={status} length={len(text)} {parse_msg}",
                )
            )
        except Exception as exc:
            result.cases.append(
                ProbeCase(
                    name=f"v2 line 1m {year}.js",
                    ok=False,
                    latency_ms=_elapsed_ms(start),
                    message=str(exc),
                )
            )
        time.sleep(args.sleep)

    v6_candidates = {
        "v6 candidate 1m last": f"http://d.10jqka.com.cn/v6/line/hs_{args.stock}/11/last.js",
        "v6 candidate intraday last": f"http://d.10jqka.com.cn/v6/line/hs_{args.stock}/01/last.js",
        "v6 candidate 60m last": f"http://d.10jqka.com.cn/v6/line/hs_{args.stock}/60/last.js",
    }
    for name, url in v6_candidates.items():
        start = time.perf_counter()
        try:
            text, status, latency = _text_get(url, timeout=args.timeout, referer="http://q.10jqka.com.cn/")
            rows, first_time, last_time, parse_msg = _parse_ths_jsonp_rows(text)
            result.cases.append(
                ProbeCase(
                    name=name,
                    ok=status == 200 and rows > 0,
                    rows=rows,
                    latency_ms=latency,
                    first_time=first_time,
                    last_time=last_time,
                    message=f"status={status} length={len(text)} {parse_msg}",
                )
            )
        except Exception as exc:
            result.cases.append(
                ProbeCase(
                    name=name,
                    ok=False,
                    latency_ms=_elapsed_ms(start),
                    message=str(exc),
                )
            )
        time.sleep(args.sleep)

    result.ok = any(case.ok and (case.name.startswith("v2") or case.name.startswith("v6")) for case in result.cases)
    return result


def _parse_ths_jsonp_rows(text: str) -> tuple[int, str | None, str | None, str]:
    match = re.search(r"\((\{.*\})\)\s*$", text, re.DOTALL)
    if not match:
        return 0, None, None, "parse=no_jsonp"
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        return 0, None, None, f"parse=json_error:{exc}"
    data_text = str(payload.get("data") or "")
    if not data_text:
        return 0, None, None, "parse=no_data"
    rows = [row for row in data_text.split(";") if row.strip()]
    first = rows[0].split(",")[0] if rows else None
    last = rows[-1].split(",")[0] if rows else None
    return len(rows), first, last, "parse=ok"


def summarize(results: list[ProviderResult]) -> None:
    print("\nA-share historical minute free-source probe")
    print("=" * 72)
    for provider in results:
        status = "OK" if provider.ok else "NO"
        print(f"\n[{status}] {provider.provider}")
        if provider.message:
            print(f"  message: {provider.message}")
        print(f"  assumption: {provider.free_assumption}")
        print(f"  claim: {provider.historical_minute_claim}")
        for case in provider.cases:
            mark = "skip" if case.skipped else ("ok" if case.ok else "fail")
            rows = "" if case.rows is None else f" rows={case.rows}"
            latency = "" if case.latency_ms is None else f" {case.latency_ms}ms"
            span = ""
            if case.first_time or case.last_time:
                span = f" span={case.first_time} -> {case.last_time}"
            msg = f" msg={case.message}" if case.message else ""
            print(f"  - {mark}: {case.name}{rows}{latency}{span}{msg}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    today = dt.date.today()
    recent_end = f"{today:%Y-%m-%d} 15:00:00"
    recent_start = f"{today - dt.timedelta(days=14):%Y-%m-%d} 09:30:00"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--providers",
        default=",".join(DEFAULT_PROVIDERS),
        help="Comma-separated providers: baostock,akshare,eastmoney,pytdx,ths",
    )
    parser.add_argument("--stock", default="000001", help="Six-digit stock code, e.g. 000001.")
    parser.add_argument("--secid", default="0.000001", help="Eastmoney secid, e.g. 0.000001 or 1.600000.")
    parser.add_argument("--baostock-code", default="sz.000001", help="Baostock code, e.g. sz.000001.")
    parser.add_argument(
        "--dates",
        nargs="*",
        default=list(DEFAULT_DATES),
        help="Single-day windows for Baostock boundary checks, YYYY-MM-DD.",
    )
    parser.add_argument("--recent-start", default=recent_start, help="Recent start datetime for AkShare checks.")
    parser.add_argument("--recent-end", default=recent_end, help="Recent end datetime for AkShare checks.")
    parser.add_argument("--recent-beg", default=f"{today:%Y%m%d}", help="Recent YYYYMMDD for Eastmoney checks.")
    parser.add_argument("--timeout", type=float, default=12.0)
    parser.add_argument("--sleep", type=float, default=1.0, help="Sleep seconds between network calls.")
    parser.add_argument("--tdx-market", type=int, default=0, help="0=SZ, 1=SH for pytdx.")
    parser.add_argument(
        "--tdx-hosts",
        default="119.147.212.81:7709,47.103.48.45:7709,121.14.110.194:7709",
        help="Comma-separated host:port list for pytdx.",
    )
    parser.add_argument("--tdx-pages", type=int, default=3, help="Number of 800-row pages per pytdx period.")
    parser.add_argument("--include-unofficial", action="store_true", help="Allow probing unofficial THS endpoints.")
    parser.add_argument(
        "--ths-years",
        nargs="*",
        default=["2016", "2019", "2020", "2023", "2024"],
        help="Years to probe for Tonghuashun unofficial v2 line endpoint.",
    )
    parser.add_argument("--keep-proxy", action="store_true", help="Do not clear proxy environment variables.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if not args.keep_proxy:
        _clear_proxy_env()

    providers = [item.strip().lower() for item in args.providers.split(",") if item.strip()]
    probes = {
        "baostock": probe_baostock,
        "akshare": probe_akshare,
        "eastmoney": probe_eastmoney,
        "pytdx": probe_pytdx,
        "ths": probe_ths,
    }

    results: list[ProviderResult] = []
    for provider in providers:
        func = probes.get(provider)
        if func is None:
            results.append(
                ProviderResult(
                    provider=provider,
                    ok=False,
                    free_assumption="unknown",
                    historical_minute_claim="unknown",
                    reliability_hint="unknown",
                    message=f"Unknown provider: {provider}",
                )
            )
            continue
        try:
            results.append(func(args))
        except Exception as exc:
            results.append(
                ProviderResult(
                    provider=provider,
                    ok=False,
                    free_assumption="probe crashed",
                    historical_minute_claim="probe crashed",
                    reliability_hint="probe crashed",
                    message=f"{exc}\n{traceback.format_exc()}",
                )
            )

    summarize(results)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"a_share_minute_free_sources_{stamp}.json"
    payload = {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "args": vars(args),
        "results": [asdict(item) for item in results],
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nJSON report: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
