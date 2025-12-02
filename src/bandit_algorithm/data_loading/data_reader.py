import pyarrow.parquet as pq
import pandas as pd


class DataReader:
    def __init__(self, file_path, batch_size: int):
        self.file_path = file_path
        self.batch_size = batch_size
        self.df = pd.DataFrame()

    def read(self):
        parquet_file = pq.ParquetFile(self.file_path)
        for batch in parquet_file.iter_batches(batch_size=self.batch_size):
            self.df = pd.concat([self.df, batch.to_pandas()], axis=0)

        return self.df.reset_index()
