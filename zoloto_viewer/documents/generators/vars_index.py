import collections

from . import _base

from zoloto_viewer.infoplan.models import Marker, MarkerVariable
from zoloto_viewer.infoplan.utils import variable_transformations
from zoloto_viewer.viewer.models import Project


class VarsIndexFileBuilder(_base.AbstractCsvFileBuilder):
    def __init__(self, project: 'Project'):
        super().__init__()
        self.csv_header = ('Номер первого носителя', 'Кол-во употреблений', 'Первая строка', 'Вторая строка')
        self.project = project

    def make_rows(self, target='csv'):
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
        var_ids = collections.defaultdict(list)

        # vars_by_side это словарь marker_uid -> infoplan, где infoplan это словарь side -> side_vars_list
        # и apply_transformations действуют на side_vars_list ожидая
        # список типа variable_transformations.Variable (namedtuple)
        for m in vars_by_side.keys():
            marker_infoplan = vars_by_side[m]
            marker_number = marker_numbers[m]
            for s in marker_infoplan.keys():
                marker_vars = marker_infoplan[s]
                for v in marker_vars:   # type: variable_transformations.Variable
                    for lang_pair in MarkerVariable.to_lang_pairs(v.value):
                        var_first_use.setdefault(lang_pair, marker_number)
                        var_count[lang_pair] += 1
                        var_ids[lang_pair].append(v.variable_id)

        def by_rus(row):
            target: str = row[2]
            # hack to sort words first
            startswith_letter = target[0].isalnum() if target else True
            return not startswith_letter, target

        def render_number_count_ru_en(number, lang_pair):
            return number, var_count[lang_pair], lang_pair[0], lang_pair[1]

        def render_ru_en_var_ids(number, lang_pair):
            return var_ids[lang_pair], lang_pair[1], lang_pair[0]

        if target == 'web':
            render_method = render_ru_en_var_ids
        else:
            render_method = render_number_count_ru_en

        return sorted([
            render_method(number, lang_pair)
            for lang_pair, number in var_first_use.items()
        ], key=by_rus)
