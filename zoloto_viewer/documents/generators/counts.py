import csv

from zoloto_viewer.infoplan.models import Marker
from zoloto_viewer.viewer.models import Project

from . import _base


class CountFileBuilder(_base.AbstractFileBuilder):
    def __init__(self):
        super().__int__(bytes_buffer=False, extension='csv')

    def build(self, project: 'Project'):
        csv_header = ('Тип элемента', 'Название носителя', 'Количество')
        csv_rows = [
            (L.title, L.desc, markers.count())
            for L, markers in Marker.objects.by_layer(project).items()
        ]

        writer = csv.writer(self.buffer, dialect='excel', delimiter=',')
        writer.writerow(csv_header)
        writer.writerows(csv_rows)
