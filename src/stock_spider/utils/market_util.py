def classify_stock(code: str, ktype: str | None = None) -> tuple[str | None, bool]:
    """判断股票所属市场及是否为主板

    Args:
        code: 股票代码(6位)
        ktype: K线类型(None=日线/1m/5m, 10=指数)

    Returns:
        (market, is_main_board):
        - ("SH", True) - 上海主板(60xxxx)
        - ("SZ", True) - 深圳主板(00xxxx/002xxx)
        - (None, False) - 非主板(指数/创业板/科创板/北交所)
    """
    if ktype is not None and str(ktype) == "10":
        return (None, False)

    if not code or len(code) < 6:
        return (None, False)

    prefix = code[:2]

    if prefix == "60":
        return ("SH", True)

    if prefix == "00":
        return ("SZ", True)

    # 创业板排除
    if prefix == "30":
        return (None, False)

    # 科创板排除
    if prefix == "68":
        return (None, False)

    # 北交所排除
    if prefix in ("83", "87", "43"):
        return (None, False)

    return (None, False)
