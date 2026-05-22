from datetime import datetime


def generate_core_code(market: str, code: str, trade_time: datetime) -> str:
    """生成核心编码: market(2)+code(6)+YYYYMMDDHHmm(12)=20位

    示例: generate_core_code("SH", "600519", datetime(2023,2,1,9,30))
          → "SH600519202302010930"
    """
    time_str = trade_time.strftime("%Y%m%d%H%M")
    return f"{market}{code}{time_str}"
