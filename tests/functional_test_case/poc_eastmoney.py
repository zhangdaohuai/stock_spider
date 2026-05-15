"""东方财富网实时行情API接口验证脚本 (PoC)"""

import os
import requests
import json
import time

# 清除代理设置，直连东方财富
for proxy_key in [
    "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY",
    "ALL_PROXY", "all_proxy",
]:
    os.environ.pop(proxy_key, None)


def test_index_realtime():
    """测试1: 上证指数和深证成指实时行情"""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36"
        ),
        "Referer": "https://quote.eastmoney.com/",
    }

    base_url = "https://push2.eastmoney.com/api/qt/stock/get"

    # 上证指数 secid = 1.000001
    print("=" * 60)
    print("测试1: 上证指数实时行情")
    print("=" * 60)
    params_sh = {
        "ut": "fa5fd1943c7b386f172d6893dbfba10b",
        "invt": "2",
        "fltt": "2",
        "fields": (
            "f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,"
            "f55,f57,f58,f60,f107,f116,f117,f152,f168,"
            "f169,f170,f171"
        ),
        "secid": "1.000001",
        "_": str(int(time.time() * 1000)),
    }
    try:
        resp = requests.get(
            base_url, params=params_sh, headers=headers, timeout=10
        )
        print(f"状态码: {resp.status_code}")
        data = resp.json()
        print(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"请求失败: {e}")

    print()

    # 深证成指 secid = 0.399001
    print("=" * 60)
    print("测试2: 深证成指实时行情")
    print("=" * 60)
    params_sz = {
        "ut": "fa5fd1943c7b386f172d6893dbfba10b",
        "invt": "2",
        "fltt": "2",
        "fields": (
            "f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,"
            "f55,f57,f58,f60,f107,f116,f117,f152,f168,"
            "f169,f170,f171"
        ),
        "secid": "0.399001",
        "_": str(int(time.time() * 1000)),
    }
    try:
        resp = requests.get(
            base_url, params=params_sz, headers=headers, timeout=10
        )
        print(f"状态码: {resp.status_code}")
        data = resp.json()
        print(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"请求失败: {e}")


def test_index_list():
    """测试3: 指数列表接口"""
    print()
    print("=" * 60)
    print("测试3: 指数列表 (沪深重要指数)")
    print("=" * 60)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36"
        ),
        "Referer": "https://quote.eastmoney.com/",
    }
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": "1",
        "pz": "20",
        "po": "1",
        "np": "1",
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": "2",
        "invt": "2",
        "fid": "f3",
        "fs": "b:MK0021",
        "fields": (
            "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,"
            "f12,f13,f14,f15,f16,f17,f18"
        ),
    }
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"状态码: {resp.status_code}")
        data = resp.json()
        if data.get("data") and data["data"].get("diff"):
            for item in data["data"]["diff"][:10]:
                code = item.get("f12", "")
                name = item.get("f14", "")
                price = item.get("f2", "")
                pct = item.get("f3", "")
                print(
                    f"代码: {code}, 名称: {name}, "
                    f"最新: {price}, 涨跌幅: {pct}%"
                )
        else:
            print(
                "返回数据:",
                json.dumps(data, ensure_ascii=False, indent=2)[:500],
            )
    except Exception as e:
        print(f"请求失败: {e}")


def test_kline():
    """测试4: K线历史数据接口"""
    print()
    print("=" * 60)
    print("测试4: 上证指数K线历史数据")
    print("=" * 60)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36"
        ),
        "Referer": "https://quote.eastmoney.com/",
    }
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": (
            "f51,f52,f53,f54,f55,f56,f57,f58,f59,"
            "f60,f61"
        ),
        "klt": "101",  # 日线
        "fqt": "1",     # 前复权
        "secid": "1.000001",
        "beg": "0",
        "end": "20500000",
        "lmt": "10",    # 最近10条
        "ut": "fa5fd1943c7b386f172d6893dbfba10b",
        "_": str(int(time.time() * 1000)),
    }
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"状态码: {resp.status_code}")
        data = resp.json()
        klines = data.get("data", {}).get("klines", [])
        print(f"获取到 {len(klines)} 条K线数据")
        for k in klines[-5:]:
            print(f"  {k}")
    except Exception as e:
        print(f"请求失败: {e}")


def test_min_kline():
    """测试5: 分钟级K线数据"""
    print()
    print("=" * 60)
    print("测试5: 上证指数分钟级K线数据 (5分钟)")
    print("=" * 60)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36"
        ),
        "Referer": "https://quote.eastmoney.com/",
    }
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": (
            "f51,f52,f53,f54,f55,f56,f57,f58,f59,"
            "f60,f61"
        ),
        "klt": "5",     # 5分钟线
        "fqt": "1",
        "secid": "1.000001",
        "beg": "0",
        "end": "20500000",
        "lmt": "10",
        "ut": "fa5fd1943c7b386f172d6893dbfba10b",
        "_": str(int(time.time() * 1000)),
    }
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"状态码: {resp.status_code}")
        data = resp.json()
        klines = data.get("data", {}).get("klines", [])
        print(f"获取到 {len(klines)} 条5分钟K线数据")
        for k in klines[-5:]:
            print(f"  {k}")
    except Exception as e:
        print(f"请求失败: {e}")


def test_trends():
    """测试6: 分时线数据"""
    print()
    print("=" * 60)
    print("测试6: 上证指数分时线数据")
    print("=" * 60)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36"
        ),
        "Referer": "https://quote.eastmoney.com/",
    }
    url = "https://push2his.eastmoney.com/api/qt/stock/trends2/get"
    params = {
        "fields1": "f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f11,f12,f13",
        "fields2": (
            "f51,f52,f53,f54,f55,f56,f57,f58"
        ),
        "iscr": "0",
        "secid": "1.000001",
        "ndays": "1",
        "ut": "fa5fd1943c7b386f172d6893dbfba10b",
        "_": str(int(time.time() * 1000)),
    }
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"状态码: {resp.status_code}")
        data = resp.json()
        trends = data.get("data", {}).get("trends", [])
        print(f"获取到 {len(trends)} 条分时数据")
        if trends:
            print(f"  最早: {trends[0]}")
            print(f"  最新: {trends[-1]}")
    except Exception as e:
        print(f"请求失败: {e}")


def test_response_time():
    """测试7: 响应时间评估"""
    print()
    print("=" * 60)
    print("测试7: 响应时间评估 (连续5次请求)")
    print("=" * 60)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36"
        ),
        "Referer": "https://quote.eastmoney.com/",
    }
    url = "https://push2.eastmoney.com/api/qt/stock/get"
    params = {
        "ut": "fa5fd1943c7b386f172d6893dbfba10b",
        "invt": "2",
        "fltt": "2",
        "fields": "f43,f57,f58",
        "secid": "1.000001",
        "_": str(int(time.time() * 1000)),
    }

    times = []
    for i in range(5):
        params["_"] = str(int(time.time() * 1000))
        start = time.time()
        try:
            resp = requests.get(
                url, params=params, headers=headers, timeout=10
            )
            elapsed = time.time() - start
            times.append(elapsed)
            print(f"  第{i+1}次: {elapsed:.3f}s, 状态码: {resp.status_code}")
        except Exception as e:
            print(f"  第{i+1}次: 失败 - {e}")
        time.sleep(0.5)

    if times:
        print(
            f"\n平均响应时间: {sum(times)/len(times):.3f}s, "
            f"最快: {min(times):.3f}s, 最慢: {max(times):.3f}s"
        )


if __name__ == "__main__":
    test_index_realtime()
    test_index_list()
    test_kline()
    test_min_kline()
    test_trends()
    test_response_time()
