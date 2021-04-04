import abc
import csv
import io


class AbstractCsvFileBuilder(abc.ABC):
    def __init__(self):
        self.csv_header = ()
        self.buffer = io.StringIO()
        super().__init__()

    @abc.abstractmethod
    def make_rows(self):
        pass

    @property
    def buffer_bytes(self):
        return io.BytesIO(self.buffer.getvalue().encode('utf-8'))

    def build(self):
        writer = csv.writer(self.buffer, dialect='excel', delimiter=',')
        writer.writerow(self.csv_header)
        writer.writerows(self.make_rows())
