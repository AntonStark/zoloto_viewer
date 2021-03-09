import collections
import html
import itertools
import re

from . import _base

from zoloto_viewer.infoplan.models import MarkerVariable
from zoloto_viewer.viewer.models import Project


class VarsIndexFileBuilder(_base.AbstractCsvFileBuilder):
    def __init__(self, project: 'Project'):
        super().__init__(project)
        self.csv_header = ('Номер первого носителя', 'Кол-во употреблений', 'Первая строка', 'Вторая строка')

    def make_rows(self):
        pict_regex = re.compile(MarkerVariable.PICT_PATTERN)

        def process_var(variable: str):
            variable = html.unescape(variable)
            # filter empty and masterpage marks
            if not variable or variable.startswith('mp:'):
                return []

            variable = variable.replace('&tab', '')
            variable = re.sub(pict_regex, '', variable)
            by_lines = variable.split('\n')
            # нечётные строчки должны содержать русский текст, а чётные перевод
            rus, eng = by_lines[::2], by_lines[1::2]
            return itertools.zip_longest(rus, eng, fillvalue='')

        variables = MarkerVariable.objects.filter(marker__floor__project=self.project)

        var_first_use = {}
        var_count = collections.defaultdict(int)
        for v in variables:
            for lang_pair in process_var(v.value):
                var_first_use.setdefault(lang_pair, v.marker.number)
                var_count[lang_pair] += 1

        def by_rus(row):
            target: str = row[2]
            # hack to sort words first
            startswith_letter = target[0].isalnum() if target else True
            return not startswith_letter, target

        return sorted([
            (number, var_count[lang_pair], lang_pair[0], lang_pair[1])
            for lang_pair, number in var_first_use.items()
        ], key=by_rus)
