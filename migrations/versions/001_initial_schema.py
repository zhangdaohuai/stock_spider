"""初始Schema: 创建6张核心表

Revision ID: 001
Revises:
Create Date: 2026-05-19

禁止实现downgrade()，所有migration只允许升级，绝对禁止降级。
"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()

    connection.execute(text(
        """
        CREATE TABLE IF NOT EXISTS db_version (
            version      VARCHAR(20)   PRIMARY KEY,
            description  VARCHAR(200)  NOT NULL,
            applied_at   TIMESTAMP     NOT NULL DEFAULT NOW()
        )
        """
    ))

    connection.execute(text(
        """
        CREATE TABLE IF NOT EXISTS stock_info (
            code        VARCHAR(6)   NOT NULL,
            name        VARCHAR(20)  NOT NULL,
            market      VARCHAR(2)   NOT NULL,
            stock_type  SMALLINT     NOT NULL DEFAULT 1,
            list_date   DATE,
            delist_date DATE,
            updated_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
            CONSTRAINT pk_stock_info PRIMARY KEY (code, market)
        )
        """
    ))

    connection.execute(text("CREATE INDEX idx_stock_info_type ON stock_info (stock_type)"))
    connection.execute(text("CREATE INDEX idx_stock_info_name ON stock_info (name)"))

    # 1分钟K线分区表（主表）
    connection.execute(text(
        """
        CREATE TABLE IF NOT EXISTS kline_1m (
            core_code   VARCHAR(20)  NOT NULL,
            trade_time  TIMESTAMP    NOT NULL,
            code        VARCHAR(6)   NOT NULL,
            market      VARCHAR(2)   NOT NULL,
            open        NUMERIC(10,3),
            close       NUMERIC(10,3),
            high        NUMERIC(10,3),
            low         NUMERIC(10,3),
            volume      BIGINT,
            amount      NUMERIC(18,2),
            avg_price   NUMERIC(10,3),
            created_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
            CONSTRAINT pk_kline_1m PRIMARY KEY (core_code, trade_time)
        ) PARTITION BY RANGE (trade_time)
        """
    ))

    _1m_partitions = [
        ("202110", "2021-10-01", "2021-11-01"),
        ("202111", "2021-11-01", "2021-12-01"),
        ("202112", "2021-12-01", "2022-01-01"),
        ("202201", "2022-01-01", "2022-02-01"),
        ("202202", "2022-02-01", "2022-03-01"),
        ("202203", "2022-03-01", "2022-04-01"),
        ("202204", "2022-04-01", "2022-05-01"),
        ("202205", "2022-05-01", "2022-06-01"),
        ("202206", "2022-06-01", "2022-07-01"),
        ("202207", "2022-07-01", "2022-08-01"),
        ("202208", "2022-08-01", "2022-09-01"),
        ("202209", "2022-09-01", "2022-10-01"),
        ("202210", "2022-10-01", "2022-11-01"),
        ("202211", "2022-11-01", "2022-12-01"),
        ("202212", "2022-12-01", "2023-01-01"),
        ("202301", "2023-01-01", "2023-02-01"),
        ("202302", "2023-02-01", "2023-03-01"),
    ]

    for suffix, start, end in _1m_partitions:
        connection.execute(text(
            f"""
            CREATE TABLE kline_1m_{suffix} PARTITION OF kline_1m
                FOR VALUES FROM ('{start}') TO ('{end}')
            """
        ))

    connection.execute(text(
        "CREATE TABLE kline_1m_default PARTITION OF kline_1m DEFAULT"
    ))

    connection.execute(text("CREATE INDEX idx_kline_1m_code_time ON kline_1m (code, trade_time)"))

    # 5分钟K线分区表（主表）
    connection.execute(text(
        """
        CREATE TABLE IF NOT EXISTS kline_5m (
            core_code   VARCHAR(20)  NOT NULL,
            trade_time  TIMESTAMP    NOT NULL,
            code        VARCHAR(6)   NOT NULL,
            market      VARCHAR(2)   NOT NULL,
            open        NUMERIC(10,3),
            close       NUMERIC(10,3),
            high        NUMERIC(10,3),
            low         NUMERIC(10,3),
            volume      BIGINT,
            amount      NUMERIC(18,2),
            turnover    NUMERIC(8,4),
            created_at  TIMESTAMP    NOT NULL DEFAULT NOW(),
            CONSTRAINT pk_kline_5m PRIMARY KEY (core_code, trade_time)
        ) PARTITION BY RANGE (trade_time)
        """
    ))

    _5m_partitions = [
        ("202108", "2021-08-01", "2021-09-01"),
        ("202109", "2021-09-01", "2021-10-01"),
        ("202110", "2021-10-01", "2021-11-01"),
        ("202111", "2021-11-01", "2021-12-01"),
        ("202112", "2021-12-01", "2022-01-01"),
        ("202201", "2022-01-01", "2022-02-01"),
        ("202202", "2022-02-01", "2022-03-01"),
        ("202203", "2022-03-01", "2022-04-01"),
        ("202204", "2022-04-01", "2022-05-01"),
        ("202205", "2022-05-01", "2022-06-01"),
        ("202206", "2022-06-01", "2022-07-01"),
        ("202207", "2022-07-01", "2022-08-01"),
        ("202208", "2022-08-01", "2022-09-01"),
        ("202209", "2022-09-01", "2022-10-01"),
        ("202210", "2022-10-01", "2022-11-01"),
        ("202211", "2022-11-01", "2022-12-01"),
        ("202212", "2022-12-01", "2023-01-01"),
        ("202301", "2023-01-01", "2023-02-01"),
        ("202302", "2023-02-01", "2023-03-01"),
    ]

    for suffix, start, end in _5m_partitions:
        connection.execute(text(
            f"""
            CREATE TABLE kline_5m_{suffix} PARTITION OF kline_5m
                FOR VALUES FROM ('{start}') TO ('{end}')
            """
        ))

    connection.execute(text(
        "CREATE TABLE kline_5m_default PARTITION OF kline_5m DEFAULT"
    ))

    connection.execute(text("CREATE INDEX idx_kline_5m_code_time ON kline_5m (code, trade_time)"))

    connection.execute(text(
        """
        CREATE TABLE IF NOT EXISTS import_progress (
            id              SERIAL       PRIMARY KEY,
            period          VARCHAR(4)   NOT NULL,
            zip_file        VARCHAR(50)  NOT NULL,
            status          VARCHAR(20)  NOT NULL DEFAULT 'pending',
            total_files     INTEGER      DEFAULT 0,
            imported_files  INTEGER      DEFAULT 0,
            total_rows      BIGINT       DEFAULT 0,
            error_msg       TEXT,
            started_at      TIMESTAMP,
            finished_at     TIMESTAMP,
            created_at      TIMESTAMP    NOT NULL DEFAULT NOW(),
            CONSTRAINT uk_import_progress UNIQUE (period, zip_file)
        )
        """
    ))

    connection.execute(text(
        """
        CREATE TABLE IF NOT EXISTS kline_monthly_stats (
            id              SERIAL       PRIMARY KEY,
            period          VARCHAR(4)   NOT NULL,
            month           VARCHAR(6)   NOT NULL,
            code            VARCHAR(6)   NOT NULL,
            market          VARCHAR(2)   NOT NULL,
            row_count       INTEGER      NOT NULL DEFAULT 0,
            expected_count  INTEGER      NOT NULL DEFAULT 0,
            diff_pct        NUMERIC(8,4) NOT NULL DEFAULT 0,
            checked_at      TIMESTAMP    NOT NULL DEFAULT NOW(),
            CONSTRAINT uk_kline_monthly_stats UNIQUE (period, month, code, market)
        )
        """
    ))

    connection.execute(text(
        "CREATE INDEX idx_kline_monthly_stats_month ON kline_monthly_stats (period, month)"
    ))
    connection.execute(text(
        "CREATE INDEX idx_kline_monthly_stats_diff "
        "ON kline_monthly_stats (period, diff_pct) WHERE ABS(diff_pct) > 5"
    ))

    connection.execute(text(
        "INSERT INTO db_version (version, description) VALUES ('001', '初始Schema')"
    ))


def downgrade() -> None:
    raise NotImplementedError("禁止降级")
