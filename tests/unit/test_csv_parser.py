from datetime import datetime
from decimal import Decimal

import pytest

from stock_spider.data.importer.csv_parser import CsvParser
from stock_spider.data.importer.models import Kline1mRecord, Kline5mRecord


class TestParse1mRow:
    def test_parse_1m_row_normal(self) -> None:
        line = "000001,2023-02-01 09:30:00,15.03,15.03,15.03,15.03,3601.0,5412300.0,15.03"
        result = CsvParser.parse_1m_row(line)
        assert result is not None
        assert isinstance(result, Kline1mRecord)
        assert result.code == "000001"
        assert result.trade_time == datetime(2023, 2, 1, 9, 30, 0)
        assert result.market == "SZ"
        assert result.open == Decimal("15.03")
        assert result.close == Decimal("15.03")
        assert result.high == Decimal("15.03")
        assert result.low == Decimal("15.03")
        assert result.volume == 3601
        assert result.amount == Decimal("5412300.0")
        assert result.avg_price == Decimal("15.03")

    def test_parse_1m_row_header_skip(self) -> None:
        line = "股票代码,时间,开盘,收盘,最高,最低,成交量,成交额,均价"
        result = CsvParser.parse_1m_row(line)
        assert result is None

    def test_parse_1m_row_non_main_board(self) -> None:
        line = "300001,2023-02-01 09:30:00,15.03,15.03,15.03,15.03,3601.0,5412300.0,15.03"
        result = CsvParser.parse_1m_row(line)
        assert result is None

    def test_parse_1m_row_invalid_price(self) -> None:
        line = "000001,2023-02-01 09:30:00,0,15.03,15.03,15.03,3601.0,5412300.0,15.03"
        result = CsvParser.parse_1m_row(line)
        assert result is None

    def test_parse_1m_row_low_gt_high(self) -> None:
        line = "000001,2023-02-01 09:30:00,15.03,15.03,14.00,16.00,3601.0,5412300.0,15.03"
        result = CsvParser.parse_1m_row(line)
        assert result is None

    def test_parse_1m_row_core_code(self) -> None:
        line = "600519,2023-02-01 09:30:00,1800.00,1805.00,1810.00,1795.00,5000.0,9000000.0,1800.00"
        result = CsvParser.parse_1m_row(line)
        assert result is not None
        assert result.core_code == "SH600519202302010930"


class TestParse5mRow:
    def test_parse_5m_row_normal_11(self) -> None:
        line = "000001,平安银行,5.0,2023-02-01 09:35:00,15.03,15.01,15.08,14.95,43954.0,6.59863E7,0.02"
        result = CsvParser.parse_5m_row(line)
        assert result is not None
        assert isinstance(result, Kline5mRecord)
        assert result.code == "000001"
        assert result.trade_time == datetime(2023, 2, 1, 9, 35, 0)
        assert result.market == "SZ"
        assert result.open == Decimal("15.03")
        assert result.close == Decimal("15.01")
        assert result.high == Decimal("15.08")
        assert result.low == Decimal("14.95")
        assert result.volume == 43954
        assert result.turnover == Decimal("0.02")

    def test_parse_5m_row_normal_12(self) -> None:
        line = "000001,平安银行,5.0,0,2023-02-01 09:35:00,15.03,15.01,15.08,14.95,43954.0,6.59863E7,0.02"
        result = CsvParser.parse_5m_row(line)
        assert result is not None
        assert isinstance(result, Kline5mRecord)
        assert result.code == "000001"
        assert result.trade_time == datetime(2023, 2, 1, 9, 35, 0)
        assert result.open == Decimal("15.03")
        assert result.close == Decimal("15.01")

    def test_parse_5m_row_scientific(self) -> None:
        line = "000001,平安银行,5.0,2023-02-01 09:35:00,15.03,15.01,15.08,14.95,43954.0,6.59863E7,0.02"
        result = CsvParser.parse_5m_row(line)
        assert result is not None
        assert result.amount == Decimal("6.59863E7")

    def test_parse_5m_row_index_exclude(self) -> None:
        line = "000001,上证指数,10,2023-02-01 09:35:00,3200.00,3198.00,3205.00,3195.00,100000.0,5.0E9,0.01"
        result = CsvParser.parse_5m_row(line)
        assert result is None


class TestDetectEncoding:
    def test_detect_encoding_utf8(self) -> None:
        text = "股票代码,时间,开盘"
        raw = text.encode('utf-8')
        assert CsvParser.detect_encoding(raw) == 'utf-8'

    def test_detect_encoding_gbk(self) -> None:
        text = "股票代码,时间,开盘"
        raw = text.encode('gbk')
        assert CsvParser.detect_encoding(raw) == 'gbk'


class TestParseScientific:
    def test_parse_scientific(self) -> None:
        assert CsvParser.parse_scientific("6.59863E7") == Decimal("6.59863E7")
        assert CsvParser.parse_scientific("2.98901E7") == Decimal("2.98901E7")
        assert CsvParser.parse_scientific("abc") == Decimal('0')
        assert CsvParser.parse_scientific("12345.67") == Decimal("12345.67")
