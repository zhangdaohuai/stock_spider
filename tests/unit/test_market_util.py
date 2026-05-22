from stock_spider.utils.market_util import classify_stock


def test_sh_main_board() -> None:
    assert classify_stock("600519") == ("SH", True)


def test_sz_main_board() -> None:
    assert classify_stock("000858") == ("SZ", True)


def test_sz_sme_board() -> None:
    assert classify_stock("002001") == ("SZ", True)


def test_gem_exclude() -> None:
    assert classify_stock("300001") == (None, False)


def test_star_exclude() -> None:
    assert classify_stock("688001") == (None, False)


def test_bse_exclude() -> None:
    assert classify_stock("830001") == (None, False)


def test_index_exclude() -> None:
    assert classify_stock("000001", ktype="10") == (None, False)


def test_normal_with_ktype() -> None:
    assert classify_stock("600519", ktype="5") == ("SH", True)


def test_empty_code() -> None:
    assert classify_stock("") == (None, False)


def test_short_code() -> None:
    assert classify_stock("60") == (None, False)
