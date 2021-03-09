import abc
import csv
import io

from zoloto_viewer.viewer.models import Project


class AbstractCsvFileBuilder(abc.ABC):
    def __init__(self, project: 'Project'):
        self.project = project
        self.csv_header = ()
        self.buffer = io.StringIO()
        super().__init__()

    @abc.abstractmethod
    def make_rows(self):
        pass

    def build(self):
        writer = csv.writer(self.buffer, dialect='excel', delimiter=',')
        writer.writerow(self.csv_header)
        writer.writerows(self.make_rows())
