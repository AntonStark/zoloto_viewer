import collections
import itertools
import html
from typing import (
    List,
    Generator,
)

from zoloto_viewer.infoplan.models import Marker, MarkerVariable
# from zoloto_viewer.infoplan.utils import variable_transformations
from zoloto_viewer.viewer.models import Layer

from . import _base


class InfoplanFileBuilder(_base.AbstractCsvFileBuilder):
    def __init__(self, layer: 'Layer'):
        super().__init__()
        self.csv_header = ('Номер элемента', 'Мастер-страница', 'Переменные')
        self.layer = layer

    def make_rows(self):

        need_split = self.layer.kind.is_fingerpost
        if need_split:
            return tuple(itertools.chain.from_iterable(
                marker_rows_split(m, m.number)      # returns list of rows
                for m in Marker.objects.filter(layer=self.layer)
            ))

        return [
            marker_rows_single(m, m.number)
            for m in Marker.objects.filter(layer=self.layer)
        ]


def variables_to_row(variables_list, marker_number: str, number_suffix: str = None) -> List[str]:
    master_page = ''
    mp = MarkerVariable.MASTER_PAGE_MARK
    # assuming that master page mark may be only in the first variable
    if variables_list and variables_list[0].startswith(mp):
        master_page, *variables_list = variables_list
        master_page = master_page[len(mp):]

    number = marker_number
    if number_suffix:
        number += f'_{number_suffix}'
    prefix = [number, master_page]
    return prefix + variables_list


def marker_rows_split(marker: Marker, marker_number: str) -> Generator[List[str], None, None]:
    side_buckets = collections.defaultdict(list)
    side_data = marker.markerfingerpost_set.first()
    for value, side in marker.markervariable_set.values_list('value', 'side'):
        if side_data.is_enabled(side):
            side_buckets[side].append(html.unescape(value))

    # each side becomes new line ihn file
    for side, side_variables in side_buckets.items():   # [ (side, [side_variables] ), ]
        # yield variables_to_row(side_variables, marker_number, side_label=side)
        for variable, var_letter in zip(side_variables, 'ABCDEFGH'):
            yield variables_to_row([variable], marker_number, number_suffix=f'{side}{var_letter}')


def marker_rows_single(marker: Marker, marker_number: str) -> List[str]:
    singular_side = ''
    variables = [
        (
            singular_side,
            [
                html.unescape(value)
                for value in marker.markervariable_set.values_list('value', flat=True)
            ]
        )
    ]
    _, all_variables = variables[0]
    return variables_to_row(all_variables, marker_number)
