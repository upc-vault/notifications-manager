from data_loading.data_reader import DataReader


def eval(self):
    self.train_df = DataReader('data_loading/part-00000-b6d6fc31-19ab-4361-8676-58414d2f5cad-c000.snappy.parquet', 5000, 100000).read()
