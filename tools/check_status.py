#!/usr/bin/env python3
"""导入状态查询脚本"""
import argparse
import logging
import sys
import os

# 将src目录添加到sys.path，使stock_spider包可导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from stock_spider.data.storage.connection import ConnectionPool
from stock_spider.data.importer.monthly_stats import MonthlyStats
from stock_spider.utils.trade_calendar import TradeCalendar

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
)


def main() -> None:
    parser = argparse.ArgumentParser(description='导入状态查询')
    parser.add_argument(
        '--stats', action='store_true', help='查询月度统计',
    )
    parser.add_argument(
        '--period', choices=['1m', '5m'], help='周期',
    )
    parser.add_argument('--month', type=str, help='月份，如202302')
    args = parser.parse_args()

    ConnectionPool.initialize()

    # 月度统计查询模式
    if args.stats:
        calendar = TradeCalendar()
        stats = MonthlyStats(calendar)
        period = args.period or '1m'
        month = args.month
        if month:
            result = stats.get_stats(period, month)
            for row in result:
                print(
                    f"{row['code']:6s} {row['market']:2s} "
                    f"实际:{row['row_count']:6d} "
                    f"预期:{row['expected_count']:6d} "
                    f"差异:{row['diff_pct']:.2f}%"
                )
        else:
            print("请指定 --month 参数")
        return

    # 默认查询import_progress表
    conn = ConnectionPool.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT period, zip_file, status, total_rows "
                "FROM import_progress ORDER BY period, zip_file"
            )
            for row in cur.fetchall():
                print(
                    f"{row[0]:4s} {row[1]:40s} "
                    f"{row[2]:8s} {row[3] or 0}"
                )
    finally:
        ConnectionPool.return_connection(conn)

    ConnectionPool.close_all()


if __name__ == '__main__':
    main()
