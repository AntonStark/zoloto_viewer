import collections
import itertools
import html

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
        def variables_to_row(variables_list, marker_number, side_label=None):
            master_page = ''
            mp = MarkerVariable.MASTER_PAGE_MARK
            # assuming that master page mark may be only in the first variable
            if variables_list and variables_list[0].startswith(mp):
                master_page, *variables_list = variables_list
                master_page = master_page[len(mp):]

            number = marker_number
            if side_label:
                number += f'_{side_label}'
            prefix = [number, master_page]
            return prefix + variables_list

        def marker_rows_split(marker: Marker, marker_number):
            side_buckets = collections.defaultdict(list)
            side_data = marker.markerfingerpost_set.first()
            for value, side in marker.markervariable_set.values_list('value', 'side'):
                if side_data.is_enabled(side):
                    side_buckets[side].append(html.unescape(value))
            variables = side_buckets.items()    # [ (side, [side_variables] ), ]

            for side, side_variables in variables:
                yield variables_to_row(side_variables, marker_number, side_label=side)

        def marker_rows_single(marker: Marker, marker_number):
            singular_side = ''
            variables = [
                (singular_side, [html.unescape(value)
                                 for value in marker.markervariable_set.values_list('value', flat=True)])
            ]
            _, all_variables = variables[0]
            return variables_to_row(all_variables, marker_number)

        need_split = self.layer.kind.is_fingerpost
        if need_split:
            return tuple(itertools.chain.from_iterable(
                marker_rows_split(m, m.number)
                for m in Marker.objects.filter(layer=self.layer)
            ))
        else:
            return [
                marker_rows_single(m, m.number)
                for m in Marker.objects.filter(layer=self.layer)
            ]
