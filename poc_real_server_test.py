"""验证pytdx真实服务器连通性 - 找到稳定可用的下载地址"""
from pytdx.hq import TdxHq_API
import time


def test_servers() -> None:
    # 通达信官方公共行情服务器列表
    servers = [
        ("119.147.212.81", 7709),
        ("112.74.214.43", 7727),
        ("221.231.141.60", 7709),
        ("101.227.73.20", 7709),
        ("101.227.77.254", 7709),
        ("14.215.128.18", 7709),
        ("59.173.18.140", 7709),
        ("180.153.18.170", 7709),
        ("180.153.18.171", 7709),
        ("202.108.253.130", 7709),
        ("202.108.253.131", 7709),
        ("60.12.136.250", 7709),
        ("60.191.117.167", 7709),
        ("115.238.56.198", 7709),
        ("218.75.126.9", 7709),
        ("115.238.90.165", 7709),
        ("124.160.88.183", 7709),
    ]

    print("=" * 70)
    print("pytdx 真实服务器连通性测试")
    print("=" * 70)

    alive_servers = []
    for ip, port in servers:
        api = TdxHq_API()
        try:
            start = time.time()
            result = api.connect(ip, port)
            latency = (time.time() - start) * 1000
            if result:
                # 获取1分钟K线验证数据可用性
                data = api.get_security_bars(8, 0, "000001", 0, 10)
                data_ok = data is not None and len(data) > 0
                count = len(data) if data else 0
                print(
                    f"[OK] {ip}:{port} - 延迟:{latency:.0f}ms "
                    f"- 数据获取:{'成功' if data_ok else '失败'} "
                    f"- 记录数:{count}"
                )
                alive_servers.append((ip, port, latency, data_ok))
                api.disconnect()
            else:
                print(f"[FAIL] {ip}:{port} - 连接被拒绝")
        except Exception as e:
            print(f"[ERROR] {ip}:{port} - {str(e)[:60]}")

    print()
    print("=" * 70)
    print(f"存活服务器: {len(alive_servers)}/{len(servers)}")
    print("=" * 70)

    # 按延迟排序
    alive_servers.sort(key=lambda x: x[2])
    print()
    print("推荐服务器（按延迟排序）:")
    for i, (ip, port, latency, data_ok) in enumerate(alive_servers[:5], 1):
        print(
            f"  {i}. {ip}:{port} ({latency:.0f}ms) "
            f"数据:{'OK' if data_ok else 'FAIL'}"
        )


if __name__ == "__main__":
    test_servers()
