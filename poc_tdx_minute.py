"""
pytdx / mootdx 分钟线数据能力验证 PoC 脚本
本脚本仅用于技术研究验证，不会合入主代码库。
验证内容：
1. pytdx get_security_bars 获取1分钟/5分钟线的实际数据深度
2. pytdx get_history_minute_time_data 的历史范围
3. mootdx bars/minute 方法的数据深度
4. offset/start 翻页机制与数据重复检测
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
from pytdx.hq import TdxHq_API
from pytdx.exhq import TdxExHq_API
from pytdx.util.best_ip import select_best_ip

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
)
logger = logging.getLogger("poc_tdx_minute")


def find_best_server() -> dict:
    """自动选择最优通达信行情服务器"""
    try:
        info = select_best_ip()
        logger.info("最优服务器: %s:%s", info["ip"], info["port"])
        return info
    except Exception as e:
        logger.warning("自动选IP失败: %s, 使用默认", e)
        return {"ip": "119.147.212.81", "port": 7709}


# ============================================================
# 测试1: pytdx get_security_bars 分钟线数据深度
# ============================================================
def test_pytdx_bars_depth(
    api: TdxHq_API,
    category: int,
    market: int,
    code: str,
    label: str,
) -> None:
    """
    测试 get_security_bars 在指定 category 下能获取多少条数据。
    通过逐步增大 start 参数翻页，检测数据重复或截断。
    """
    logger.info("=" * 60)
    logger.info("测试: pytdx get_security_bars category=%d (%s)", category, label)
    logger.info("=" * 60)

    all_data: list = []
    seen_datetimes: set = set()
    duplicate_count: int = 0
    batch_size: int = 800  # 单次最大请求数
    start: int = 0

    for page in range(10):  # 最多翻10页
        data = api.get_security_bars(category, market, code, start, batch_size)
        if not data:
            logger.info("第%d页返回空数据, 停止翻页", page + 1)
            break

        # 检测重复
        page_duplicates = 0
        for item in data:
            dt = item.get("datetime", "")
            if dt in seen_datetimes:
                page_duplicates += 1
            else:
                seen_datetimes.add(dt)

        if page_duplicates > 0:
            duplicate_count += page_duplicates
            logger.warning(
                "第%d页有%d条重复数据 (总重复: %d)",
                page + 1, page_duplicates, duplicate_count,
            )

        all_data.extend(data)
        logger.info(
            "第%d页: 获取%d条, start=%d, "
            "时间范围: %s ~ %s, 重复: %d",
            page + 1, len(data), start,
            data[0].get("datetime", "N/A"),
            data[-1].get("datetime", "N/A"),
            page_duplicates,
        )

        # 如果返回数据不足 batch_size，说明已到末尾
        if len(data) < batch_size:
            logger.info("返回数据不足%d条, 已到数据末尾", batch_size)
            break

        start += batch_size

    # 汇总统计
    if all_data:
        df = pd.DataFrame(all_data)
        df = df.drop_duplicates(subset=["datetime"])
        logger.info(
            "汇总: 总获取%d条, 去重后%d条, "
            "最早: %s, 最晚: %s",
            len(all_data), len(df),
            df["datetime"].iloc[-1] if len(df) > 0 else "N/A",
            df["datetime"].iloc[0] if len(df) > 0 else "N/A",
        )
        # 计算天数跨度
        try:
            earliest = pd.to_datetime(df["datetime"].iloc[-1])
            latest = pd.to_datetime(df["datetime"].iloc[0])
            span_days = (latest - earliest).days
            logger.info("时间跨度: %d 天", span_days)
        except Exception:
            pass


# ============================================================
# 测试2: pytdx get_history_minute_time_data 历史范围
# ============================================================
def test_pytdx_history_minute(
    api: TdxHq_API,
    market: int,
    code: str,
) -> None:
    """
    测试 get_history_minute_time_data 能获取多早的数据。
    从当前日期往前逐步尝试，找到最早可获取的日期。
    """
    logger.info("=" * 60)
    logger.info("测试: pytdx get_history_minute_time_data 历史范围")
    logger.info("=" * 60)

    today = datetime.now()
    # 尝试从今天往前搜索
    found_dates: list = []
    not_found_dates: list = []

    # 先测试最近30天
    for i in range(30):
        check_date = today - timedelta(days=i)
        # 跳过周末
        if check_date.weekday() >= 5:
            continue
        date_int = int(check_date.strftime("%Y%m%d"))
        data = api.get_history_minute_time_data(market, code, date_int)
        if data:
            found_dates.append(date_int)
        else:
            not_found_dates.append(date_int)

    if found_dates:
        logger.info(
            "最近30天内可获取历史分时数据的日期: %d个, "
            "最早: %d, 最晚: %d",
            len(found_dates), min(found_dates), max(found_dates),
        )
    else:
        logger.warning("最近30天内未获取到任何历史分时数据")

    # 尝试更早的日期 (60天前, 90天前, 120天前, 180天前, 365天前)
    test_offsets = [60, 90, 120, 180, 365]
    for offset in test_offsets:
        check_date = today - timedelta(days=offset)
        date_int = int(check_date.strftime("%Y%m%d"))
        data = api.get_history_minute_time_data(market, code, date_int)
        status = "有数据" if data else "无数据"
        logger.info("日期 %d (距今%d天): %s", date_int, offset, status)


# ============================================================
# 测试3: mootdx 分钟线数据深度
# ============================================================
def test_mootdx_bars_depth() -> None:
    """测试 mootdx Quotes.bars 方法获取分钟线的深度"""
    logger.info("=" * 60)
    logger.info("测试: mootdx Quotes.bars 分钟线数据深度")
    logger.info("=" * 60)

    try:
        from mootdx.quotes import Quotes

        client = Quotes.factory(market="std", bestip=True, timeout=15)

        # 测试不同 frequency 的1分钟线
        # frequency 映射: 7/8=1min, 0=5min
        for freq, label in [(8, "1分钟线(freq=8)"), (7, "1分钟线(freq=7)"), (0, "5分钟线(freq=0)")]:
            logger.info("--- frequency=%d (%s) ---", freq, label)
            try:
                # 测试大 offset
                for offset_val in [100, 500, 800, 1000, 2000, 5000]:
                    data = client.bars(
                        symbol="000001",
                        frequency=freq,
                        offset=offset_val,
                    )
                    if data is not None and len(data) > 0:
                        logger.info(
                            "offset=%d: 获取%d条, "
                            "最早: %s, 最晚: %s",
                            offset_val, len(data),
                            str(data.index[-1]) if len(data) > 0 else "N/A",
                            str(data.index[0]) if len(data) > 0 else "N/A",
                        )
                    else:
                        logger.info("offset=%d: 无数据", offset_val)
                    time.sleep(0.3)  # 限流
            except Exception as e:
                logger.error("frequency=%d 测试失败: %s", freq, e)

        client.close()
    except ImportError:
        logger.warning("mootdx 未安装, 跳过测试")
    except Exception as e:
        logger.error("mootdx 测试失败: %s", e)


# ============================================================
# 测试4: pytdx 扩展行情(exhq)分钟线
# ============================================================
def test_pytdx_exhq_minute() -> None:
    """测试扩展行情接口的分钟线能力"""
    logger.info("=" * 60)
    logger.info("测试: pytdx 扩展行情(exhq)分钟线")
    logger.info("=" * 60)

    api = TdxExHq_API()
    # 扩展行情服务器列表
    ex_servers = [
        ("61.152.107.141", 7727),
        ("218.75.126.9", 7727),
        ("115.238.56.198", 7727),
    ]

    connected = False
    for ip, port in ex_servers:
        try:
            if api.connect(ip, port):
                logger.info("连接扩展行情服务器成功: %s:%d", ip, port)
                connected = True
                break
        except Exception:
            continue

    if not connected:
        logger.warning("无法连接扩展行情服务器, 跳过")
        return

    try:
        # 查看可用市场
        markets = api.get_markets()
        if markets:
            df_markets = api.to_df(markets)
            logger.info("可用市场列表:\n%s", df_markets.to_string())

        # 尝试获取股指期货的分钟线 (市场47)
        for category in [0, 1, 7, 8]:
            try:
                data = api.get_instrument_bars(category, 47, "IFL0", 0, 100)
                if data:
                    df = api.to_df(data)
                    logger.info(
                        "扩展行情 category=%d: 获取%d条, "
                        "时间范围: %s ~ %s",
                        category, len(df),
                        df["datetime"].iloc[-1] if len(df) > 0 else "N/A",
                        df["datetime"].iloc[0] if len(df) > 0 else "N/A",
                    )
                else:
                    logger.info("扩展行情 category=%d: 无数据", category)
            except Exception as e:
                logger.info("扩展行情 category=%d: 失败 - %s", category, e)
    finally:
        api.disconnect()


# ============================================================
# 主函数
# ============================================================
def main() -> None:
    logger.info("开始 pytdx/mootdx 分钟线数据能力验证")
    logger.info("当前时间: %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # 查找最优服务器
    server = find_best_server()

    # 初始化 pytdx 标准行情 API
    api = TdxHq_API()

    try:
        with api.connect(server["ip"], server["port"]):
            logger.info("pytdx 连接成功: %s:%d", server["ip"], server["port"])

            # 测试1: 1分钟线数据深度 (category=7)
            test_pytdx_bars_depth(api, 7, 0, "000001", "1分钟线(cat=7)")
            time.sleep(1)

            # 测试1b: 1分钟线数据深度 (category=8)
            test_pytdx_bars_depth(api, 8, 0, "000001", "1分钟线(cat=8)")
            time.sleep(1)

            # 测试1c: 5分钟线数据深度 (category=0)
            test_pytdx_bars_depth(api, 0, 0, "000001", "5分钟线(cat=0)")
            time.sleep(1)

            # 测试2: 历史分时数据范围
            test_pytdx_history_minute(api, 0, "000001")

    except Exception as e:
        logger.error("pytdx 标准行情测试失败: %s", e)

    # 测试3: mootdx
    test_mootdx_bars_depth()

    # 测试4: 扩展行情
    test_pytdx_exhq_minute()

    logger.info("所有测试完成")


if __name__ == "__main__":
    main()
