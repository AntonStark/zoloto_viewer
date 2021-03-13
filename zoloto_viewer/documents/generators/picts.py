import re

from zoloto_viewer.infoplan.models import MarkerVariable
from zoloto_viewer.viewer.models import Project

from . import _base


class PictListFileBuilder(_base.AbstractCsvFileBuilder):
    def __init__(self, project: 'Project'):
        super().__init__()
        self.csv_header = ('Код пиктограммы',)
        self.project = project

    def make_rows(self):
        variables = MarkerVariable.objects\
            .filter(marker__floor__project=self.project)\
            .values_list('value', flat=True)
        pict_codes = set(re.findall(MarkerVariable.PICT_PATTERN, '\n'.join(variables)))
        return ((c,) for c in pict_codes)
