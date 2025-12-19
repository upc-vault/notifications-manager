import pyarrow.parquet as pq

parquet_file = pq.ParquetFile('part-00000-b6d6fc31-19ab-4361-8676-58414d2f5cad-c000.snappy.parquet')
column_names = parquet_file.schema.names

for col_name in column_names:
    print(f"- {col_name}")

print(parquet_file.read())
