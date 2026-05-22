import json
import logging
import os
from datetime import date, datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class TradeCalendar:

    def __init__(self, config_path: str | None = None) -> None:
        resolved = (
            config_path
            or os.environ.get("CONFIG_PATH")
            or str(
                Path(__file__).resolve().parents[3] / "config" / "trade_calendar.json"
            )
        )
        with open(resolved, encoding="utf-8") as fh:
            self._data: dict[str, dict[str, list[str]]] = json.load(fh)

    def get_trading_days_count(self, year: int, month: int) -> int:
        year_key = str(year)
        month_key = f"{month:02d}"
        year_data = self._data.get(year_key)
        if year_data is None:
            fallback = self._fallback_count(year, month)
            logger.warning(
                "年份 %d 不在交易日历中，使用回退估算: %d 天", year, fallback
            )
            return fallback
        month_days = year_data.get(month_key)
        if month_days is None:
            fallback = self._fallback_count(year, month)
            logger.warning(
                "%d-%02d 不在交易日历中，使用回退估算: %d 天",
                year,
                month,
                fallback,
            )
            return fallback
        return len(month_days)

    def get_trading_days(self, year: int, month: int) -> list[date]:
        year_key = str(year)
        month_key = f"{month:02d}"
        year_data = self._data.get(year_key)
        if year_data is None:
            fallback = self._fallback_days(year, month)
            logger.warning(
                "年份 %d 不在交易日历中，使用回退估算，共 %d 天",
                year,
                len(fallback),
            )
            return fallback
        month_days = year_data.get(month_key)
        if month_days is None:
            fallback = self._fallback_days(year, month)
            logger.warning(
                "%d-%02d 不在交易日历中，使用回退估算，共 %d 天",
                year,
                month,
                len(fallback),
            )
            return fallback
        return [datetime.strptime(d, "%Y-%m-%d").date() for d in month_days]

    def is_trading_day(self, target_date: date) -> bool:
        days = self.get_trading_days(target_date.year, target_date.month)
        return target_date in days

    def calc_expected_count(self, period: str, year: int, month: int) -> int:
        trading_days = self.get_trading_days_count(year, month)
        if period == "1m":
            return 240 * trading_days
        elif period == "5m":
            return 48 * trading_days
        else:
            raise ValueError(f"不支持的周期: {period}")

    def _fallback_count(self, year: int, month: int) -> int:
        weekdays = self._count_weekdays(year, month)
        estimated = max(weekdays - 2, 0)
        logger.warning(
            "回退估算 %d-%02d 交易日: 工作日 %d - 法定假日约2天 = %d",
            year,
            month,
            weekdays,
            estimated,
        )
        return estimated

    def _fallback_days(self, year: int, month: int) -> list[date]:
        result: list[date] = []
        first = date(year, month, 1)
        # 当月最后一天
        if month == 12:
            last = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last = date(year, month + 1, 1) - timedelta(days=1)
        current = first
        while current <= last:
            if current.weekday() < 5:
                result.append(current)
            current += timedelta(days=1)
        logger.warning(
            "回退估算 %d-%02d 交易日列表，共 %d 天（仅工作日近似）",
            year,
            month,
            len(result),
        )
        return result

    @staticmethod
    def _count_weekdays(year: int, month: int) -> int:
        first = date(year, month, 1)
        if month == 12:
            last = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last = date(year, month + 1, 1) - timedelta(days=1)
        count = 0
        current = first
        while current <= last:
            if current.weekday() < 5:
                count += 1
            current += timedelta(days=1)
        return count
