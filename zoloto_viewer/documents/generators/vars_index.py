import collections
import html
import itertools
import re

from . import _base

from zoloto_viewer.infoplan.models import Marker, MarkerVariable
from zoloto_viewer.infoplan.utils import variable_transformations
from zoloto_viewer.viewer.models import Project


class VarsIndexFileBuilder(_base.AbstractCsvFileBuilder):
    def __init__(self, project: 'Project'):
        super().__init__()
        self.csv_header = ('Номер первого носителя', 'Кол-во употреблений', 'Первая строка', 'Вторая строка')
        self.project = project

    def make_rows(self):

        def process_var(variable: str):
            # filter empty
            if not variable:
                return []

            lines = variable.split('\n')

            def is_relevant(var):
                irrelevant_chars = [' ', ',', '-', '—']
                relevant = [c for c in set(var) if c not in irrelevant_chars]
                return bool(relevant)

            without_empty = [line for line in lines if is_relevant(line)]
            lines = without_empty
            # print(lines)

            def detect_languages(text):
                languages = []

                contains_cyrillic = re.search(r'[А-ЯА-яё]', text)
                if contains_cyrillic:
                    languages += ['ru']

                contains_english = re.search(r'[A-Za-z]', text)
                if contains_english:
                    languages += ['en']
                return languages

            rus = eng = []
            lang = detect_languages(variable)
            if 'ru' in lang and 'en' in lang:
                # чётные строчки должны содержать русский текст, а нечётные перевод
                rus, eng = lines[::2], lines[1::2]
            elif 'ru' in lang:
                rus = lines
            elif 'en' in lang:
                eng = lines
            return itertools.zip_longest(rus, eng, fillvalue='')

        transformations = [
            variable_transformations.UnescapeHtml(),
            variable_transformations.HideMasterPageLine(),
            variable_transformations.EliminateTabs(),
            variable_transformations.EliminatePictCodes(),
            variable_transformations.EliminateNumbers(),
            variable_transformations.EliminateArrows(),
        ]

        proj_variables = MarkerVariable.objects.filter(marker__floor__project=self.project)
        vars_by_side, markers = MarkerVariable.objects.vars_by_side(
            proj_variables,
            apply_transformations=transformations
        )

        marker_numbers = Marker.objects.get_numbers_list(markers)
        var_first_use = {}
        var_count = collections.defaultdict(int)

        for m in vars_by_side.keys():
            marker_infoplan = vars_by_side[m]
            for s in marker_infoplan.keys():
                marker_vars = marker_infoplan[s]
                for v in marker_vars:
                    # debug = list(process_var(v))
                    # print(debug)
                    # ————————————
                    # d = ''
                    for lang_pair in process_var(v):
                        var_first_use.setdefault(lang_pair, marker_numbers[m])
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
