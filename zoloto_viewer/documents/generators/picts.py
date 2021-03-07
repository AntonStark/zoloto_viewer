import re

from zoloto_viewer.infoplan.models import MarkerVariable
from zoloto_viewer.viewer.models import Project

from . import _base


class PictListFileBuilder(_base.AbstractCsvFileBuilder):
    def __init__(self, project: 'Project'):
        super().__int__(project)
        self.csv_header = ('Код пиктограммы',)
        self.filename = f'project_{self.project.title}_picts.{self.extension}'

    def make_rows(self):
        variables = MarkerVariable.objects\
            .filter(marker__floor__project=self.project)\
            .values_list('value', flat=True)
        pict_codes = set(re.findall('@[A-z]+@', '\n'.join(variables)))
        return [(c,) for c in pict_codes]
