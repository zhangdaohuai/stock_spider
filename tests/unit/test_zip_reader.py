import zipfile
from pathlib import Path

import pytest

from stock_spider.data.importer.zip_reader import ZipReader


@pytest.fixture
def sample_zip(tmp_path: Path) -> str:
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("SH600519.csv", "code,time,open,close\n600519,09:30,100,101\n")
        zf.writestr("SZ000858.csv", "code,time,open,close\n000858,09:30,50,51\n")
        zf.writestr("readme.txt", "not a csv")
    return str(zip_path)


@pytest.fixture
def empty_zip(tmp_path: Path) -> str:
    zip_path = tmp_path / "empty.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        pass
    return str(zip_path)


def test_list_csv_files(sample_zip: str) -> None:
    reader = ZipReader(sample_zip)
    csv_files = reader.list_csv_files()
    assert "SH600519.csv" in csv_files
    assert "SZ000858.csv" in csv_files
    assert "readme.txt" not in csv_files


def test_list_csv_files_sorted(sample_zip: str) -> None:
    reader = ZipReader(sample_zip)
    csv_files = reader.list_csv_files()
    assert csv_files == sorted(csv_files)


def test_get_file_count(sample_zip: str) -> None:
    reader = ZipReader(sample_zip)
    assert reader.get_file_count() == 2


def test_read_csv_stream(sample_zip: str) -> None:
    reader = ZipReader(sample_zip)
    stream = reader.read_csv_stream("SH600519.csv")
    content = stream.read()
    stream.close()
    assert b"code,time,open,close" in content
    assert b"600519,09:30,100,101" in content


def test_read_csv_lines(sample_zip: str) -> None:
    reader = ZipReader(sample_zip)
    lines = reader.read_csv_lines("SZ000858.csv")
    assert len(lines) == 2
    assert lines[0].strip() == b"code,time,open,close"
    assert lines[1].strip() == b"000858,09:30,50,51"


def test_file_not_found(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        ZipReader(tmp_path / "nonexistent.zip")


def test_empty_zip(empty_zip: str) -> None:
    reader = ZipReader(empty_zip)
    assert reader.list_csv_files() == []
    assert reader.get_file_count() == 0


def test_non_csv_excluded(sample_zip: str) -> None:
    reader = ZipReader(sample_zip)
    csv_files = reader.list_csv_files()
    assert all(f.lower().endswith(".csv") for f in csv_files)
