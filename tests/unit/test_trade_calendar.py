import json
from datetime import date

import pytest

from stock_spider.utils.trade_calendar import TradeCalendar


@pytest.fixture()
def sample_calendar_data() -> dict[str, dict[str, list[str]]]:
    return {
        "2022": {
            "01": [
                "2022-01-04",
                "2022-01-05",
                "2022-01-06",
                "2022-01-07",
                "2022-01-10",
                "2022-01-11",
                "2022-01-12",
                "2022-01-13",
                "2022-01-14",
                "2022-01-17",
                "2022-01-18",
                "2022-01-19",
                "2022-01-20",
                "2022-01-21",
                "2022-01-24",
                "2022-01-25",
                "2022-01-26",
                "2022-01-27",
                "2022-01-28",
            ],
            "02": [
                "2022-02-07",
                "2022-02-08",
                "2022-02-09",
                "2022-02-10",
                "2022-02-11",
                "2022-02-14",
                "2022-02-15",
                "2022-02-16",
                "2022-02-17",
                "2022-02-18",
                "2022-02-21",
                "2022-02-22",
                "2022-02-23",
                "2022-02-24",
                "2022-02-25",
                "2022-02-28",
            ],
        }
    }


@pytest.fixture()
def calendar_file(tmp_path, sample_calendar_data):
    cal_file = tmp_path / "trade_calendar.json"
    cal_file.write_text(json.dumps(sample_calendar_data), encoding="utf-8")
    return str(cal_file)


@pytest.fixture()
def cal(calendar_file) -> TradeCalendar:
    return TradeCalendar(config_path=calendar_file)


def test_get_trading_days_count(cal: TradeCalendar) -> None:
    assert cal.get_trading_days_count(2022, 1) == 19
    assert cal.get_trading_days_count(2022, 2) == 16


def test_get_trading_days(cal: TradeCalendar) -> None:
    days = cal.get_trading_days(2022, 1)
    assert isinstance(days, list)
    assert all(isinstance(d, date) for d in days)
    assert len(days) == 19
    assert days[0] == date(2022, 1, 4)
    assert days[-1] == date(2022, 1, 28)


def test_is_trading_day_true(cal: TradeCalendar) -> None:
    assert cal.is_trading_day(date(2022, 1, 4)) is True
    assert cal.is_trading_day(date(2022, 1, 28)) is True


def test_is_trading_day_false(cal: TradeCalendar) -> None:
    assert cal.is_trading_day(date(2022, 1, 1)) is False
    assert cal.is_trading_day(date(2022, 1, 2)) is False


def test_calc_expected_count_1m(cal: TradeCalendar) -> None:
    count = cal.calc_expected_count("1m", 2022, 1)
    assert count == 240 * 19


def test_calc_expected_count_5m(cal: TradeCalendar) -> None:
    count = cal.calc_expected_count("5m", 2022, 1)
    assert count == 48 * 19


def test_fallback_missing_month(cal: TradeCalendar) -> None:
    count = cal.get_trading_days_count(2022, 3)
    assert count > 0
    days = cal.get_trading_days(2022, 3)
    assert len(days) > 0
    assert all(isinstance(d, date) for d in days)
    # 2022年3月1日是周二，应为工作日
    assert date(2022, 3, 1) in days
    # 2022年3月5日是周六，不应在回退列表中
    assert date(2022, 3, 5) not in days


def test_invalid_period(cal: TradeCalendar) -> None:
    with pytest.raises(ValueError, match="不支持的周期"):
        cal.calc_expected_count("15m", 2022, 1)
