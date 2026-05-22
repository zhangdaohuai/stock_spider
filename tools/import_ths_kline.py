#!/usr/bin/env python3
"""同花顺K线数据导入脚本"""
import argparse
import logging
import sys
import os

# 将src目录添加到sys.path，使stock_spider包可导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from stock_spider.data.importer.ths_importer import ThsImporter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
)


def main() -> None:
    parser = argparse.ArgumentParser(description='同花顺K线数据导入')
    parser.add_argument(
        '--period', choices=['1m', '5m'], help='导入周期: 1m或5m',
    )
    parser.add_argument('--month', type=str, help='指定月份，如202302')
    parser.add_argument(
        '--status', action='store_true', help='查看导入状态',
    )
    args = parser.parse_args()

    importer = ThsImporter()

    # 查看导入状态模式
    if args.status:
        status = importer.get_import_status(args.period)
        for row in status:
            print(
                f"{row['period']:4s} "
                f"{row['zip_file']:40s} "
                f"{row['status']:8s} "
                f"{row.get('total_rows', 0)}"
            )
        return

    if not args.period:
        parser.print_help()
        return

    # 指定月份导入，否则导入整个周期
    if args.month:
        importer.import_month(args.period, args.month)
    else:
        importer.import_period(args.period)


if __name__ == '__main__':
    main()
