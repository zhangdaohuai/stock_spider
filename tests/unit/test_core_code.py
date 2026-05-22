from datetime import datetime

from stock_spider.utils.core_code import generate_core_code


def test_1m_core_code() -> None:
    result = generate_core_code("SH", "600519", datetime(2023, 2, 1, 9, 30))
    assert result == "SH600519202302010930"


def test_5m_core_code() -> None:
    result = generate_core_code("SZ", "000858", datetime(2023, 2, 1, 9, 35))
    assert result == "SZ000858202302010935"


def test_deterministic() -> None:
    dt = datetime(2023, 2, 1, 9, 30)
    result1 = generate_core_code("SH", "600519", dt)
    result2 = generate_core_code("SH", "600519", dt)
    assert result1 == result2


def test_uniqueness_different_stock() -> None:
    dt = datetime(2023, 2, 1, 9, 30)
    result1 = generate_core_code("SH", "600519", dt)
    result2 = generate_core_code("SH", "601318", dt)
    assert result1 != result2


def test_uniqueness_different_time() -> None:
    dt1 = datetime(2023, 2, 1, 9, 30)
    dt2 = datetime(2023, 2, 1, 9, 31)
    result1 = generate_core_code("SH", "600519", dt1)
    result2 = generate_core_code("SH", "600519", dt2)
    assert result1 != result2


def test_length() -> None:
    result = generate_core_code("SH", "600519", datetime(2023, 2, 1, 9, 30))
    assert len(result) == 20


def test_midnight_time() -> None:
    result = generate_core_code("SH", "600519", datetime(2023, 2, 1, 0, 0))
    assert result == "SH600519202302010000"


def test_end_of_day() -> None:
    result = generate_core_code("SH", "600519", datetime(2023, 2, 1, 15, 0))
    assert result == "SH600519202302011500"
