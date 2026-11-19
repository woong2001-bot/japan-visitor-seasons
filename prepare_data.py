"""실행: python prepare_data.py jnto.xlsx (openpyxl 필요)."""
import csv
import sys
from pathlib import Path
from openpyxl import load_workbook

# JNTO 「国籍/月別 訪日外客数」 2026-11-18 공개본
# https://www.jnto.go.jp/statistics/data/_files/20261118_1615-5.xlsx
names = {"韓国": "한국", "台湾": "대만", "米国": "미국"}
book = load_workbook(sys.argv[1], read_only=True, data_only=True)
records = []
for year in (2023, 2024, 2025):
    rows = list(book[str(year)].values)
    headers = rows[3]
    for row in rows:
        if row[0] not in names:
            continue
        counts = [row[headers.index(f"{month}月")] for month in range(1, 13)]
        assert all(isinstance(n, int) and n >= 0 for n in counts)
        assert sum(counts) == row[headers.index("累計")]
        print(year, names[row[0]], sum(counts), counts.index(max(counts))+1, max(counts))
        for month, count in enumerate(counts, 1):
            records.append((year, month, names[row[0]], count))
assert len(records) == len({r[:3] for r in records}) == 108
with (Path(__file__).parent / "data" / "arrivals.csv").open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["연도", "월", "시장", "방문객"])
    writer.writerows(records)
