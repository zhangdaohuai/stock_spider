#!/usr/bin/env python3
"""数据库初始化脚本"""
import logging
import sys
import os

# 将src目录添加到sys.path，使stock_spider包可导入
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from stock_spider.data.storage.db_manager import DatabaseManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(message)s",
)


def main() -> None:
    print("正在初始化数据库...")
    db_mgr = DatabaseManager()
    db_mgr.ensure_schema()
    print("数据库初始化完成")


if __name__ == '__main__':
    main()
