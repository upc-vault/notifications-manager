import pyarrow.parquet as pq
import pandas as pd


class DataReader:
    def __init__(self, file_path, batch_size: int, max_elms: int):
        self.file_path = file_path
        self.batch_size = batch_size
        self.max_elms = max_elms
        self.df = pd.DataFrame()

    def read(self):
        counter = 0
        parquet_file = pq.ParquetFile(self.file_path)

        for batch in parquet_file.iter_batches(batch_size=self.batch_size):
            batch = batch.to_pandas()
            self.df = pd.concat([self.df, batch], axis=0)
            counter += self.batch_size

            if counter >= self.max_elms:
                break

        return self.df.reset_index()
