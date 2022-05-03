import logging

from reportlab.lib import colors
from typing import Iterator, List

from zoloto_viewer.viewer.models import Layer, LayerGroup, Page
from zoloto_viewer.infoplan.models import CaptionPlacement

from . import layout
from .plan import BoundingBox, BoundsIndex, MarkerCaption, Object
from .plan_page_writer import PlanPageWriterMinimal

logger = logging.getLogger(__name__)


class PlanPageWriterLayerGroupsSimple(PlanPageWriterMinimal):
    def __init__(self, canvas,
                 floor: Page, layers: List[Layer], layers_group: LayerGroup,
                 marker_positions_getter):
        logger.debug('start PlanPageWriterMinimal')
        super().__init__(canvas, floor, layers, marker_positions_getter)
        logger.debug('start PlanPageWriterLayerGroupsSimple')
        self.layers_group = layers_group
        self.caption_placements = {
            cp.marker.uid: cp.data
            for cp in layers_group.captionplacement_set.all()   # type: CaptionPlacement
        }
        active_layers = Layer.objects.filter(id__in=layers_group.layers)
        self._active_layers = [l for l in layers if l in active_layers]
        logger.debug('start _marker_positions_active')
        self._marker_positions_active = [mo for mo in self._marker_positions
                                         if mo.layer in self._active_layers]
        self._marker_positions_active__no_placement = [mo for mo in self._marker_positions_active
                                                       if mo.uid not in self.caption_placements]
        if not self._marker_positions_active:
            # skip layer group where no markers
            raise layout.NoMarkersInActiveGroupException
        self._marker_positions_inactive = [mo for mo in self._marker_positions
                                           if mo.layer not in self._active_layers]
        self._active_db_placed__marker_captions = None
        self._active_not_placed__marker_captions = None

        self.max_collisions_allowed = 0
        logger.debug('end PlanPageWriterLayerGroupsSimple')

    def draw_content(self):
        logger.debug('start draw_content')
        self._content_box.draw_plan_image(self.canvas, **self.draw_options)

        self.draw_options['objects_opacity'] = 40
        self._draw_markers(self._marker_positions_inactive)

        self.draw_options['objects_opacity'] = 100
        self._draw_markers(self._marker_positions_active)

        # logger.debug('start place_captions')
        self._active_db_placed__marker_captions = self.restore_captions_db_data()
        self._draw_marker_captions(self._active_db_placed__marker_captions)

        # logger.debug('start _draw_marker_captions')
        self._active_not_placed__marker_captions = self.place_captions(self._marker_positions_active__no_placement)
        self.store_captions_db_data(self._active_not_placed__marker_captions)
        self._draw_marker_captions(self._active_not_placed__marker_captions)

        # self._draw_box_test_marks()
        # logger.debug('start _draw_legend')
        self._draw_legend(self._active_layers)

    def restore_captions_db_data(self) -> List[MarkerCaption]:
        object_index = {mo.uid: mo for mo in self._marker_positions}
        return [
            MarkerCaption.from_db_data(data, object_index[uid], self._content_box)
            for uid, data in self.caption_placements.items()
            if uid in object_index
        ]

    def store_captions_db_data(self, captions_to_save: List[MarkerCaption]):
        list_marker_uid_to_save = [mc.obj.uid for mc in captions_to_save]
        CaptionPlacement.objects.filter(marker_id__in=list_marker_uid_to_save).delete()
        CaptionPlacement.objects.bulk_create([
            CaptionPlacement(
                marker_id=mc.obj.uid,
                layer_group=self.layers_group,
                data=mc.to_db_data(self._content_box),
            )
            for mc in captions_to_save
        ])

    def place_captions(self, marker_objects: List[Object]) -> List[MarkerCaption]:
        bb_index = BoundsIndex(self.canvas, self._content_box, marker_objects)

        markers_queue = [obj.caption() for obj in marker_objects]
        for current_marker in markers_queue:
            self.place_next(bb_index, current_marker)

        captions_right_places = [bb.ref for bb in bb_index.markers_bounds]
        return captions_right_places

    def place_next(self, bb_index: BoundsIndex, current_marker):
        # logger.debug(f'place_next at: {current_marker.number}, remains: {len(marker_place_queue)}')
        place_gen = self.make_marker_placements(bb_index, current_marker)
        place = next(place_gen)     # take from gen
        bb_index.write(place)

    def _draw_marker_captions(self, captions):
        options = self.draw_options
        for mc in captions:   # type: MarkerCaption
            mc.draw(self.canvas, self._content_box, **options)

    def make_marker_placements(self, bb_index: BoundsIndex, current_marker: MarkerCaption) -> Iterator[BoundingBox]:
        """
        Генератор положений подписи (повороты смещения) которые
        не конфликтуют с другими объектов и маркеров на основании bb_index
        :raises: MarkerNoPlaceException
        """
        place_gen = self._make_marker_placements(current_marker)
        for place in place_gen:
            yield place

    def _make_marker_placements(self, current_marker: MarkerCaption) -> Iterator[BoundingBox]:
        """
        Генератор положений подписи (повороты смещения) которые
        не конфликтуют с другими объектов и маркеров на основании bb_index
        """
        object_ = current_marker.obj
        h = MarkerCaption.CAPTION_FONT_SIZE
        h2 = 2 * h
        placement_tuning_options = [
            # (increase_a, cross_delta, comment)
            (None, None, 'default place'),

            (180, None, 'a + 180 place'),
            (90,  None, 'a + 90 place'),
            (270, None, 'a + 270 place'),

            (None, -h,  'default:-h'),
            (None, -h2, 'default:-2h'),
            (None, h,   'default:+h'),
            (None, h2,  'default:+2h'),
            (180,  -h,  'a + 180:-h'),
            (180,  -h2, 'a + 180:-2h'),
            (180,  h,   'a + 180:+h'),
            (180,  h2,  'a + 180:+2h'),
            (90,   -h,  'a + 90:-h'),
            (90,   -h2, 'a + 90:-2h'),
            (90,   h,   'a + 90:+h'),
            (90,   h2,  'a + 90:+2h'),
            (270,  -h,  'a + 270:-h'),
            (270,  -h2, 'a + 270:-2h'),
            (270,  h,   'a + 270:+h'),
            (270,  h2,  'a + 270:+2h'),
        ]

        for increase_a, cross_delta, comment in placement_tuning_options:
            offset, need_rotate = object_.get_caption_offset(increase_a=increase_a, cross_delta=cross_delta)
            current_marker.set_box_params(offset=offset, need_rotate=need_rotate)
            place = current_marker.get_bounding_box(self.canvas, force_update=True)
            # logger.info(f'_make_marker_placements: number={current_marker.number}, {comment} -> {place}')
            yield place

    def _draw_box_test_marks(self):
        canvas = self.canvas
        box = self._content_box

        canvas.saveState()
        canvas.setFillColor(colors.red)
        canvas.setStrokeColor(colors.red)

        lb = (0, 0)
        rb = (box.max_x, 0)
        lt = (0, box.max_y)
        rt = (box.max_x, box.max_y)

        x, y = box.calc_pos(lb)
        canvas.rect(x, y, 2, 2, stroke=1, fill=1)

        x, y = box.calc_pos(rb)
        canvas.rect(x, y, 2, 2, stroke=1, fill=1)

        x, y = box.calc_pos(lt)
        canvas.rect(x, y, 2, 2, stroke=1, fill=1)

        x, y = box.calc_pos(rt)
        canvas.rect(x, y, 2, 2, stroke=1, fill=1)

        canvas.restoreState()
