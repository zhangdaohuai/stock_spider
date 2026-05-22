#!/usr/bin/env python3
"""导入后数据校验脚本"""
import argparse
import json
import logging
import sys
import os

# 将src目录添加到sys.path，使stock_spider包可导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from stock_spider.data.storage.connection import ConnectionPool
from stock_spider.data.importer.data_validator import DataValidator
from stock_spider.utils.trade_calendar import TradeCalendar

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
)


def main() -> None:
    parser = argparse.ArgumentParser(description='导入后数据校验')
    parser.add_argument(
        '--period', choices=['1m', '5m'], required=True, help='周期',
    )
    parser.add_argument('--month', type=str, help='指定月份，如202302')
    parser.add_argument(
        '--all', action='store_true', help='校验全部月份',
    )
    args = parser.parse_args()

    ConnectionPool.initialize()
    calendar = TradeCalendar()
    validator = DataValidator(calendar)

    # 确定待校验的月份列表
    months: list[str] = []
    if args.all:
        conn = ConnectionPool.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT DISTINCT SUBSTRING(zip_file FROM '(\\d{6})') "
                    "FROM import_progress WHERE period=%s ORDER BY 1",
                    (args.period,),
                )
                months = [row[0] for row in cur.fetchall()]
        finally:
            ConnectionPool.return_connection(conn)
    elif args.month:
        months = [args.month]
    else:
        parser.print_help()
        return

    # 逐月执行校验
    for month in months:
        print(f"\n{'=' * 60}")
        print(f"校验 {args.period} {month}")
        print(f"{'=' * 60}")
        results = validator.validate_all(args.period, month)
        for check_name, result in results.items():
            status = result.get('status', 'unknown')
            print(f"  {check_name:20s}: {status}")
            if status != 'pass':
                print(
                    f"    详情: "
                    f"{json.dumps(result, ensure_ascii=False, default=str)}"
                )

    ConnectionPool.close_all()


if __name__ == '__main__':
    main()
