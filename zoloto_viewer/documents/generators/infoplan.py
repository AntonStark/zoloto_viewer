import html

from zoloto_viewer.infoplan.models import Marker, MarkerVariable
from zoloto_viewer.viewer.models import Layer

from . import _base


class InfoplanFileBuilder(_base.AbstractCsvFileBuilder):
    def __init__(self, layer: 'Layer'):
        super().__init__()
        self.csv_header = ('Номер элемента', 'Мастер-страница', 'Переменные')
        self.layer = layer

    def make_rows(self):
        def one_row(marker: Marker):
            variables = [html.unescape(v)
                         for v in marker.markervariable_set.values_list('value', flat=True)]

            master_page = ''
            mp = MarkerVariable.MASTER_PAGE_MARK
            # assuming that master page mark may be only in the first variable
            if variables and variables[0].startswith(mp):
                master_page, *variables = variables
                master_page = master_page[len(mp):]

            prefix = [marker.number, master_page]
            return prefix + variables

        return (
            one_row(m)
            for m in Marker.objects.filter(layer=self.layer)
        )
