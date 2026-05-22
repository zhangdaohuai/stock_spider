import json
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from stock_spider.data.importer.data_validator import DataValidator
from stock_spider.utils.trade_calendar import TradeCalendar


@pytest.fixture()
def mock_conn() -> MagicMock:
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    conn._cursor = cursor
    return conn


@pytest.fixture()
def calendar_file(tmp_path: str) -> str:
    data = {
        "2024": {
            "01": [
                "2024-01-02", "2024-01-03", "2024-01-04",
                "2024-01-05", "2024-01-08", "2024-01-09",
                "2024-01-10", "2024-01-11", "2024-01-12",
                "2024-01-15", "2024-01-16", "2024-01-17",
                "2024-01-18", "2024-01-19", "2024-01-22",
                "2024-01-23", "2024-01-24", "2024-01-25",
                "2024-01-26", "2024-01-29", "2024-01-30",
                "2024-01-31",
            ],
        }
    }
    cal_file = tmp_path / "trade_calendar.json"
    cal_file.write_text(json.dumps(data), encoding="utf-8")
    return str(cal_file)


@pytest.fixture()
def calendar(calendar_file: str) -> TradeCalendar:
    return TradeCalendar(config_path=calendar_file)


@pytest.fixture()
def validator(calendar: TradeCalendar) -> DataValidator:
    return DataValidator(calendar=calendar)


@patch("stock_spider.data.importer.data_validator.ConnectionPool")
def test_validate_row_count_pass(
    mock_pool: MagicMock, validator: DataValidator, mock_conn: MagicMock
) -> None:
    mock_pool.get_connection.return_value = mock_conn
    mock_conn._cursor.fetchone.side_effect = [(1000,), (1000,)]

    result = validator.validate_row_count("1m", "202401")

    assert result["status"] == "pass"
    assert result["db_count"] == 1000
    assert result["progress_count"] == 1000
    assert result["diff_pct"] == 0.0
    mock_pool.return_connection.assert_called_once_with(mock_conn)


@patch("stock_spider.data.importer.data_validator.ConnectionPool")
def test_validate_row_count_warn(
    mock_pool: MagicMock, validator: DataValidator, mock_conn: MagicMock
) -> None:
    mock_pool.get_connection.return_value = mock_conn
    mock_conn._cursor.fetchone.side_effect = [(1100,), (1000,)]

    result = validator.validate_row_count("1m", "202401", threshold=1.0)

    assert result["status"] == "warn"
    assert result["db_count"] == 1100
    assert result["progress_count"] == 1000
    assert result["diff_pct"] == 10.0


@patch("stock_spider.data.importer.data_validator.ConnectionPool")
def test_validate_ohlcv_pass(
    mock_pool: MagicMock, validator: DataValidator, mock_conn: MagicMock
) -> None:
    mock_pool.get_connection.return_value = mock_conn
    mock_conn._cursor.fetchone.return_value = (0,)

    result = validator.validate_ohlcv_consistency("1m", "202401")

    assert result["status"] == "pass"
    assert result["error_count"] == 0
    assert result["sample_errors"] == []


@patch("stock_spider.data.importer.data_validator.ConnectionPool")
def test_validate_ohlcv_error(
    mock_pool: MagicMock, validator: DataValidator, mock_conn: MagicMock
) -> None:
    mock_pool.get_connection.return_value = mock_conn
    mock_conn._cursor.fetchone.return_value = (3,)
    mock_conn._cursor.fetchall.return_value = [
        ("000001", "2024-01-02 09:31:00", 10.5, 11.0, 10.0, 9.5, 100),
        ("000002", "2024-01-02 09:32:00", 20.0, 21.0, 19.0, 22.0, 200),
        ("000003", "2024-01-02 09:33:00", 5.0, 5.5, 5.2, 4.8, -10),
    ]

    result = validator.validate_ohlcv_consistency("1m", "202401")

    assert result["status"] == "error"
    assert result["error_count"] == 3
    assert len(result["sample_errors"]) == 3


@patch("stock_spider.data.importer.data_validator.ConnectionPool")
def test_validate_daily_count_pass(
    mock_pool: MagicMock, validator: DataValidator, mock_conn: MagicMock
) -> None:
    mock_pool.get_connection.return_value = mock_conn
    mock_conn._cursor.fetchall.return_value = []

    result = validator.validate_daily_count("1m", "202401")

    assert result["status"] == "pass"
    assert result["abnormal_days"] == []
    assert result["total_days_checked"] == 22


@patch("stock_spider.data.importer.data_validator.ConnectionPool")
def test_validate_no_zero_volume_pass(
    mock_pool: MagicMock, validator: DataValidator, mock_conn: MagicMock
) -> None:
    mock_pool.get_connection.return_value = mock_conn
    mock_conn._cursor.fetchone.return_value = (0,)

    result = validator.validate_no_zero_volume("1m", "202401")

    assert result["status"] == "pass"
    assert result["count"] == 0
    assert result["sample"] == []


@patch("stock_spider.data.importer.data_validator.ConnectionPool")
def test_validate_no_zero_volume_warn(
    mock_pool: MagicMock, validator: DataValidator, mock_conn: MagicMock
) -> None:
    mock_pool.get_connection.return_value = mock_conn
    mock_conn._cursor.fetchone.return_value = (2,)
    mock_conn._cursor.fetchall.return_value = [
        ("000001", "2024-01-02 09:31:00", 0, 5000.0),
        ("000002", "2024-01-02 09:32:00", 0, 3000.0),
    ]

    result = validator.validate_no_zero_volume("1m", "202401")

    assert result["status"] == "warn"
    assert result["count"] == 2
    assert len(result["sample"]) == 2


@patch("stock_spider.data.importer.data_validator.ConnectionPool")
def test_validate_partition_integrity_pass(
    mock_pool: MagicMock, validator: DataValidator, mock_conn: MagicMock
) -> None:
    mock_pool.get_connection.return_value = mock_conn
    mock_conn._cursor.fetchone.return_value = (0,)

    result = validator.validate_partition_integrity("1m")

    assert result["status"] == "pass"
    assert result["default_partition_count"] == 0


@patch("stock_spider.data.importer.data_validator.ConnectionPool")
def test_validate_partition_integrity_warn(
    mock_pool: MagicMock, validator: DataValidator, mock_conn: MagicMock
) -> None:
    mock_pool.get_connection.return_value = mock_conn
    mock_conn._cursor.fetchone.return_value = (50,)

    result = validator.validate_partition_integrity("1m")

    assert result["status"] == "warn"
    assert result["default_partition_count"] == 50


@patch("stock_spider.data.importer.data_validator.ConnectionPool")
def test_validate_monthly_stats_pass(
    mock_pool: MagicMock, validator: DataValidator, mock_conn: MagicMock
) -> None:
    mock_pool.get_connection.return_value = mock_conn
    mock_conn._cursor.fetchall.return_value = []
    mock_conn._cursor.fetchone.return_value = (100,)

    result = validator.validate_monthly_stats("1m", "202401")

    assert result["status"] == "pass"
    assert result["abnormal_stocks"] == []
    assert result["total_stocks"] == 100


@patch("stock_spider.data.importer.data_validator.ConnectionPool")
def test_validate_all(
    mock_pool: MagicMock, validator: DataValidator, mock_conn: MagicMock
) -> None:
    mock_pool.get_connection.return_value = mock_conn
    mock_conn._cursor.fetchone.side_effect = [
        (1000,), (1000,), (0,), (0,), (0,), (100,),
    ]
    mock_conn._cursor.fetchall.return_value = []

    result = validator.validate_all("1m", "202401")

    assert "row_count" in result
    assert "ohlcv" in result
    assert "daily_count" in result
    assert "zero_volume" in result
    assert "partition" in result
    assert "monthly_stats" in result
    assert result["row_count"]["status"] == "pass"
    assert result["ohlcv"]["status"] == "pass"
    assert result["zero_volume"]["status"] == "pass"
    assert result["partition"]["status"] == "pass"
    assert result["monthly_stats"]["status"] == "pass"
