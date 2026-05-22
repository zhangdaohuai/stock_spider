"""检查K线ZIP文件中open=0的行比例"""
import zipfile

# 检查1分钟线
print("=== 1分钟线 ===")
months_1m = ['202111', '202112', '202201', '202202', '202203', '202204', '202205', '202206', '202207', '202208', '202209', '202210', '202211', '202212', '202301', '202302']
for month in months_1m:
    zip_path = f'stock_data/tdx_data/一分钟K线数据/{month}.zip'
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            csv_files = [
                f for f in zf.namelist()
                if f.endswith('.csv') and '000001_' in f and '_1_' in f
            ]
            if csv_files:
                with zf.open(csv_files[0]) as csv_f:
                    lines = csv_f.readlines()
                    zero_open = 0
                    total_data = 0
                    for line in lines[1:]:
                        try:
                            text = line.decode('gbk').strip()
                        except Exception:
                            try:
                                text = line.decode('utf-8').strip()
                            except Exception:
                                continue
                        fields = text.split(',')
                        if len(fields) >= 3:
                            total_data += 1
                            try:
                                if float(fields[2]) == 0.0:
                                    zero_open += 1
                            except Exception:
                                pass
                    pct = zero_open / total_data * 100 if total_data > 0 else 0
                    print(
                        f'{month}: total={total_data}, '
                        f'open=0: {zero_open} ({pct:.1f}%)'
                    )
            else:
                print(f'{month}: 未找到000001文件')
    except FileNotFoundError:
        print(f'{month}: 文件不存在')

# 检查5分钟线
print("\n=== 5分钟线 ===")
months_5m = ['202111', '202112', '202201', '202202', '202203']
for month in months_5m:
    zip_path = f'stock_data/tdx_data/五分钟K线数据/{month}.zip'
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            csv_files = [
                f for f in zf.namelist()
                if f.endswith('.csv') and '000001_' in f and '_5_' in f
            ]
            if not csv_files:
                csv_files = [
                    f for f in zf.namelist()
                    if f.endswith('.csv') and '000001_' in f
                ][:1]
            if csv_files:
                with zf.open(csv_files[0]) as csv_f:
                    lines = csv_f.readlines()
                    zero_open = 0
                    total_data = 0
                    for line in lines[1:]:
                        try:
                            text = line.decode('gbk').strip()
                        except Exception:
                            try:
                                text = line.decode('utf-8').strip()
                            except Exception:
                                continue
                        fields = text.split(',')
                        # 5分钟线open在字段4或5位置
                        open_idx = 4 if len(fields) >= 12 else 3
                        if len(fields) > open_idx:
                            total_data += 1
                            try:
                                if float(fields[open_idx]) == 0.0:
                                    zero_open += 1
                            except Exception:
                                pass
                    pct = zero_open / total_data * 100 if total_data > 0 else 0
                    print(
                        f'{month}: total={total_data}, '
                        f'open=0: {zero_open} ({pct:.1f}%)'
                    )
            else:
                print(f'{month}: 未找到000001文件')
    except FileNotFoundError:
        print(f'{month}: 文件不存在')
