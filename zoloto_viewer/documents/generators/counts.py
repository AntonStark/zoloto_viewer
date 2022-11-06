from collections import defaultdict
from typing import Dict

from zoloto_viewer.infoplan.models import (
    Marker,
    MarkerVariable,
    MarkerFingerpost,
)
from zoloto_viewer.viewer.models import (
    Project,
    Layer,
)

from . import _base


class CountFileBuilder(_base.AbstractCsvFileBuilder):
    def __init__(self, project: 'Project'):
        super().__init__()
        self.csv_header = ('Тип элемента', 'Название носителя', 'Количество')
        self.project = project

    def make_rows(self):
        return (
            (L.title, L.desc, _report_count(L, markers))
            for L, markers in Marker.objects.by_layer(self.project).items()
        )


def _report_count(layer: Layer, markers) -> str:
    if layer.kind.is_fingerpost:
        markers_count = markers.count()

        marker_panes_count = defaultdict(int)
        marker_panes_data: Dict[str, MarkerFingerpost] = {
            mf.marker_id: mf
            for mf in MarkerFingerpost.objects.filter(marker__in=markers)
        }
        for marker_uid, side, value in (
            MarkerVariable.objects
                .filter(marker__in=markers)
                .values_list('marker_id', 'side', 'value')
        ):
            if value and marker_panes_data[marker_uid].is_enabled(side):
                marker_panes_count[marker_uid] += 1
        panes_count = sum(marker_panes_count.values())

        return f'{markers_count}Ш + {panes_count}Л'

    return str(markers.count())
