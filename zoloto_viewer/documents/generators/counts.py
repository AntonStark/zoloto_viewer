from zoloto_viewer.infoplan.models import Marker
from zoloto_viewer.viewer.models import Project

from . import _base


class CountFileBuilder(_base.AbstractCsvFileBuilder):
    def __init__(self, project: 'Project'):
        super().__int__(project)
        self.csv_header = ('Тип элемента', 'Название носителя', 'Количество')

    def make_rows(self):
        return [
            (L.title, L.desc, markers.count())
            for L, markers in Marker.objects.by_layer(self.project).items()
        ]
