"""深度翻页测试 - 测试1分钟线和5分钟线的最大数据深度"""
from pytdx.hq import TdxHq_API

api = TdxHq_API()
with api.connect('shtdx.gtjas.com', 7709):
    # 1分钟线深度测试
    print("=== 1分钟线(category=7) 深度翻页测试 ===")
    for start in range(0, 50001, 800):
        data = api.get_security_bars(7, 0, '000001', start, 800)
        if not data:
            print(f'start={start}: 空数据, 停止')
            break
        first_dt = data[0].get('datetime', '')
        last_dt = data[-1].get('datetime', '')
        print(f'start={start}: {len(data)}条, {last_dt} ~ {first_dt}')
        if len(data) < 800:
            break

    # 5分钟线深度测试
    print("\n=== 5分钟线(category=0) 深度翻页测试 ===")
    for start in range(0, 50001, 800):
        data = api.get_security_bars(0, 0, '000001', start, 800)
        if not data:
            print(f'start={start}: 空数据, 停止')
            break
        first_dt = data[0].get('datetime', '')
        last_dt = data[-1].get('datetime', '')
        print(f'start={start}: {len(data)}条, {last_dt} ~ {first_dt}')
        if len(data) < 800:
            break

    # get_history_minute_time_data 更精确的范围测试
    print("\n=== get_history_minute_time_data 范围测试 ===")
    from datetime import datetime, timedelta
    today = datetime.now()
    for days_ago in [30, 45, 60, 75, 90, 100, 120, 150, 180, 200, 365]:
        check_date = today - timedelta(days=days_ago)
        date_int = int(check_date.strftime('%Y%m%d'))
        data = api.get_history_minute_time_data(0, '000001', date_int)
        status = f"有数据({len(data)}条)" if data else "无数据"
        print(f'距今{days_ago}天 ({date_int}): {status}')
