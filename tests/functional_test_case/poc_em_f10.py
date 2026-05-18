"""东方财富F10档案全量数据接口验证 (PoC)"""

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
_STOCK_CODE: str = "SH603288"

# F10 PageAjax 基础路径
_F10_BASE: str = (
    "https://emweb.securities.eastmoney.com/PC_HSF10"
)


def _create_session() -> requests.Session:
    """创建带默认头部的请求会话"""
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36"
        ),
        "Referer": "https://emweb.securities.eastmoney.com/",
    })
    return session


def _fetch_f10(
    session: requests.Session,
    path: str,
    params: dict[str, object],
    label: str,
) -> dict[str, object]:
    """请求 F10 PageAjax 接口并打印摘要"""
    url = f"{_F10_BASE}/{path}"
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

        try:
            data = resp.json()
        except Exception:
            print(f"  返回非JSON内容: {resp.text[:200]}")
            return {}

        for key, val in data.items():
            if isinstance(val, list):
                print(f"  {key}: {len(val)}行")
            elif isinstance(val, dict):
                inner = val.get("data", []) or []
                if inner:
                    print(f"  {key}: {len(inner)}行")
                else:
                    print(f"  {key}: dict({len(val)}键)")
            else:
                print(f"  {key}: {type(val).__name__}")

        return data  # type: ignore[return-value]

    except requests.RequestException as exc:
        elapsed = time.time() - start
        print(f"请求失败({elapsed:.3f}s): {exc}")
        return {}


def test_company_survey(session: requests.Session) -> None:
    """1. 公司概况"""
    _fetch_f10(
        session,
        "CompanySurvey/PageAjax",
        {"code": _STOCK_CODE},
        "公司概况",
    )
    time.sleep(_REQUEST_INTERVAL)


def test_business_analysis(session: requests.Session) -> None:
    """2. 经营分析"""
    _fetch_f10(
        session,
        "BusinessAnalysis/PageAjax",
        {"code": _STOCK_CODE},
        "经营分析",
    )
    time.sleep(_REQUEST_INTERVAL)


def test_core_subject(session: requests.Session) -> None:
    """3. 核心题材"""
    _fetch_f10(
        session,
        "Operations/SubjectDetailAjax",
        {"code": _STOCK_CODE},
        "核心题材",
    )
    time.sleep(_REQUEST_INTERVAL)


def test_share_structure(session: requests.Session) -> None:
    """4. 股本结构"""
    _fetch_f10(
        session,
        "ShareStructure/PageAjax",
        {"code": _STOCK_CODE},
        "股本结构",
    )
    time.sleep(_REQUEST_INTERVAL)


def test_company_event(session: requests.Session) -> None:
    """5. 公司大事"""
    _fetch_f10(
        session,
        "CompanyEvent/PageAjax",
        {"code": _STOCK_CODE},
        "公司大事",
    )
    time.sleep(_REQUEST_INTERVAL)


def test_finance_analysis(session: requests.Session) -> None:
    """6. 财务分析(主要指标)"""
    _fetch_f10(
        session,
        "NewFinanceAnalysis/ZYZBAjaxNew",
        {"type": 0, "code": _STOCK_CODE},
        "财务分析",
    )
    time.sleep(_REQUEST_INTERVAL)


def test_capital_operation(session: requests.Session) -> None:
    """7. 资本运作"""
    _fetch_f10(
        session,
        "CapitalOperation/PageAjax",
        {"code": _STOCK_CODE},
        "资本运作",
    )
    time.sleep(_REQUEST_INTERVAL)


def test_relative_stock(session: requests.Session) -> None:
    """8. 关联个股"""
    _fetch_f10(
        session,
        "RelativeStock/PageAjax",
        {"code": _STOCK_CODE},
        "关联个股",
    )


def main() -> None:
    """主入口: 依次验证8个F10档案API"""
    session = _create_session()

    test_company_survey(session)
    test_business_analysis(session)
    test_core_subject(session)
    test_share_structure(session)
    test_company_event(session)
    test_finance_analysis(session)
    test_capital_operation(session)
    test_relative_stock(session)

    session.close()
    print("\n全部验证完成")


if __name__ == "__main__":
    main()
