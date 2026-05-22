import zipfile, os

data_dir = 'stock_data/tdx_data/五分钟K线数据'
zf = zipfile.ZipFile(os.path.join(data_dir, '202203.zip'))

def decode_filename(filename):
    try:
        return filename.encode("cp437").decode("gbk")
    except (UnicodeDecodeError, UnicodeEncodeError):
        return filename

# 模拟ZipReader.list_csv_files()
result = []
for info in zf.infolist():
    filename = decode_filename(info.filename)
    if filename.lower().endswith(".csv"):
        result.append(filename)

print(f'CSV文件数: {len(result)}')

# 模拟read_csv_lines中的查找逻辑
# 关键：zf.open()用的是原始文件名，不是解码后的
# 但list_csv_files返回的是解码后的文件名
# ths_importer调用reader.read_csv_lines(csv_file)时
# csv_file是解码后的文件名

# 检查：read_csv_lines中是否正确匹配
mismatch = 0
for info in zf.infolist():
    decoded = decode_filename(info.filename)
    if decoded.lower().endswith('.csv'):
        # 在read_csv_lines中，会用decoded去匹配
        # 但zf.open()需要原始filename
        if decoded != info.filename:
            mismatch += 1

print(f'文件名解码不匹配数: {mismatch}')

# 测试实际匹配
test_decoded = result[0]
found = False
for info in zf.infolist():
    decoded = decode_filename(info.filename)
    if decoded == test_decoded:
        found = True
        break
print(f'测试匹配: {found} (文件: {test_decoded[:50]})')

# 关键问题：read_csv_lines中用的是原始filename还是decoded?
# 看zip_reader.py: zf.open(info.filename) 用的是原始filename
# 但匹配条件是 decoded == filename (传入的解码后文件名)
# 所以匹配应该没问题

# 让我检查是否有文件名包含空格导致问题
space_names = [n for n in result if ' ' in n]
print(f'文件名含空格的文件数: {len(space_names)}')
if space_names[:3]:
    for n in space_names[:3]:
        print(f'  {n[:80]}')

zf.close()
