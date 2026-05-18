"""东方财富网页递归链接发现爬虫 (PoC)

以海天味业(603288)为入口，递归3层深度发现 eastmoney.com 域名下
与股票相关的所有链接，按域名分类输出并汇总统计。
"""

import os
import time
import logging
from collections import defaultdict
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# 清除代理设置，直连东方财富
for _proxy_key in [
    "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
    "ALL_PROXY", "all_proxy",
]:
    os.environ.pop(_proxy_key, None)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
)
logger = logging.getLogger(__name__)

# 入口URL
SEED_URL = "https://quote.eastmoney.com/sh603288.html"
# 最大递归深度
MAX_DEPTH = 3
# 请求间隔(秒)
REQUEST_DELAY = 1.0
# 请求超时(秒)
REQUEST_TIMEOUT = 15

# 广告/追踪/登录等非数据域名黑名单
BLOCKED_DOMAINS: set[str] = {
    "acttg.eastmoney.com",
    "js1.eastmoney.com",
    "g.eastmoney.com",
    "emdata.eastmoney.com",
}

# 广告/追踪/下载/登录等URL路径关键词黑名单
BLOCKED_PATH_KEYWORDS: set[str] = {
    "tg.aspx",
    "download",
    "login",
    "register",
    "signup",
    "passport",
    "oauth",
    "captcha",
    "appdownload",
    "android",
    "iphone",
    "weixin",
}

# 公共请求头
HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://quote.eastmoney.com/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# 复用HTTP会话
_session = requests.Session()
_session.headers.update(HEADERS)


def _is_eastmoney_domain(hostname: str) -> bool:
    """判断是否属于 eastmoney.com 域名"""
    return hostname.endswith(".eastmoney.com") or hostname == "eastmoney.com"


def _is_blocked(url: str) -> bool:
    """判断URL是否属于广告/追踪/登录等非数据链接"""
    parsed = urlparse(url)
    hostname = parsed.hostname or ""

    # 域名黑名单
    if hostname in BLOCKED_DOMAINS:
        return True

    # 路径关键词黑名单
    path_lower = (parsed.path + "?" + parsed.query).lower()
    for keyword in BLOCKED_PATH_KEYWORDS:
        if keyword in path_lower:
            return True

    # 过滤锚点链接和javascript伪协议
    if url.startswith(("javascript:", "#", "mailto:")):
        return True

    return False


def _normalize_url(url: str) -> str:
    """标准化URL：去除片段标识符和末尾斜杠"""
    parsed = urlparse(url)
    # 重建URL，去除fragment
    normalized = parsed._replace(fragment="").geturl()
    # 去除末尾斜杠(仅路径部分)
    if normalized.endswith("/") and not parsed.path == "/":
        normalized = normalized.rstrip("/")
    return normalized


def fetch_page(url: str) -> str | None:
    """请求页面并返回HTML内容，失败返回None"""
    try:
        resp = _session.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        # 仅处理HTML响应
        content_type = resp.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            return None
        return resp.text
    except requests.RequestException as exc:
        logger.warning("请求失败 %s: %s", url, exc)
        return None


def extract_links(html: str, base_url: str) -> list[tuple[str, str]]:
    """从HTML中提取所有符合条件的链接

    返回: [(url, link_text), ...]
    """
    soup = BeautifulSoup(html, "html.parser")
    results: list[tuple[str, str]] = []

    for tag in soup.find_all("a", href=True):
        raw_href = tag["href"].strip()
        link_text = tag.get_text(strip=True)[:50]  # 截断过长文本

        # 拼接为绝对URL
        absolute_url = urljoin(base_url, raw_href)
        normalized = _normalize_url(absolute_url)

        parsed = urlparse(normalized)
        # 仅保留eastmoney域名下的链接
        if not parsed.hostname or not _is_eastmoney_domain(parsed.hostname):
            continue
        # 过滤非数据链接
        if _is_blocked(normalized):
            continue
        # 过滤无协议链接
        if not parsed.scheme.startswith("http"):
            continue

        results.append((normalized, link_text))

    return results


def discover_links(
    seed_url: str, max_depth: int
) -> dict[str, list[tuple[str, str, int]]]:
    """递归发现链接，按域名分类

    返回: {domain: [(url, link_text, depth), ...]}
    """
    # 已访问URL集合，避免重复爬取
    visited: set[str] = set()
    # 按域名分类的结果
    domain_links: dict[str, list[tuple[str, str, int]]] = defaultdict(list)

    # BFS队列: (url, depth)
    queue: list[tuple[str, int]] = [(seed_url, 0)]

    while queue:
        current_url, depth = queue.pop(0)

        if depth > max_depth:
            continue

        normalized = _normalize_url(current_url)
        if normalized in visited:
            continue
        visited.add(normalized)

        logger.info("[深度%d] 正在爬取: %s", depth, normalized)

        html = fetch_page(normalized)
        if html is None:
            continue

        # 限流
        time.sleep(REQUEST_DELAY)

        # 提取当前页面链接
        links = extract_links(html, normalized)
        parsed_current = urlparse(normalized)
        current_domain = parsed_current.hostname or "unknown"

        # 将当前页面自身也记录
        if normalized != seed_url or depth == 0:
            domain_links[current_domain].append(
                (normalized, "【入口页面】", depth)
            )

        for link_url, link_text in links:
            parsed_link = urlparse(link_url)
            link_domain = parsed_link.hostname or "unknown"

            # 记录发现的链接
            domain_links[link_domain].append(
                (link_url, link_text, depth + 1)
            )

            # 未访问过的链接加入队列继续爬取
            if link_url not in visited and depth + 1 <= max_depth:
                queue.append((link_url, depth + 1))

    return domain_links


def print_results(
    domain_links: dict[str, list[tuple[str, str, int]]],
) -> None:
    """按域名分类输出链接发现结果"""
    print("\n=== 链接发现结果 ===")

    # 按域名排序输出
    for domain in sorted(domain_links.keys()):
        links = domain_links[domain]
        # 按深度和URL排序
        links.sort(key=lambda x: (x[2], x[0]))

        print(f"\n--- {domain} ---")
        for url, text, depth in links:
            display_text = f" [{text}]" if text else ""
            print(f"  [深度{depth}] {url}{display_text}")


def print_summary(
    domain_links: dict[str, list[tuple[str, str, int]]],
) -> None:
    """输出汇总统计"""
    print("\n=== 汇总统计 ===")
    total = 0
    # 按链接数量降序排列
    sorted_domains = sorted(
        domain_links.items(), key=lambda x: len(x[1]), reverse=True
    )
    for domain, links in sorted_domains:
        count = len(links)
        total += count
        print(f"{domain}: {count}个链接")

    print(f"\n总链接数: {total}")
    print(f"覆盖域名数: {len(domain_links)}")


def main() -> None:
    """主入口：从海天味业(603288)页面开始递归链接发现"""
    logger.info("开始链接发现，入口: %s，最大深度: %d", SEED_URL, MAX_DEPTH)
    domain_links = discover_links(SEED_URL, MAX_DEPTH)
    print_results(domain_links)
    print_summary(domain_links)


if __name__ == "__main__":
    main()
