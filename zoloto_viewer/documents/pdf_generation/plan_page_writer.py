import logging

from reportlab.lib import colors
from typing import Dict, ItemsView, Iterator, List, Set, Tuple

from zoloto_viewer.viewer.models import Layer, Page

from . import layout
from .plan import get_objects_distance
from .plan import PlanBox, PlanLegend, Object, ObjectBoundsBucket, ObjectsConfiguration, MarkerCaption, NearObjectsGroup, \
    BoundingBox, BoundingCircle, BoundsIndex, MarkerNoPlaceException, MakerPlacementAllDone

logger = logging.getLogger(__name__)


class PlanPageWriterMinimal(layout.BasePageWriterDeducingTitle):
    _content_box = None

    def __init__(self, canvas, floor: Page, layers: List[Layer], marker_positions_getter):
        self.floor = floor
        self.layers = layers
        self._marker_positions = marker_positions_getter(floor, layers)
        self.draw_options = {
        }
        self._content_box = PlanBox(self.floor.plan_pil_obj,
                                    (self.floor.plan.width, self.floor.plan.height),
                                    self.floor.geometric_bounds)
        super().__init__(canvas)

    @classmethod
    def place_legend(cls):
        x, y = layout.plan_area_position_left_top()
        x += layout.Definitions.PLAN_LEGEND_PADDING_LEFT
        y -= layout.Definitions.PLAN_LEGEND_PADDING_TOP
        return x, y

    def draw_content(self):
        self._content_box.draw_plan_image(self.canvas, **self.draw_options)
        self._draw_markers(self._marker_positions)
        self._draw_legend(self.layers)

    def make_page_title(self):
        title = [
            f'Монтажная область {self.floor.file_title}. {self.floor.level_subtitle}',
            ''
        ]
        return title

    def make_page_super_title(self):
        super_title = [self.floor.project.title, self.floor.project.stage]
        return super_title

    def _draw_markers(self, objects):
        options = self.draw_options
        for mo in objects:   # type: Object
            mo.draw(self.canvas, self._content_box, **options)

    def _draw_legend(self, layers):
        legend = PlanLegend(self.place_legend(), layout.Definitions.BOTTOM_LINE, len(layers))
        legend.draw(self.canvas, self._content_box, layers)


class PlanPageWriterLayerGroups(PlanPageWriterMinimal):
    def __init__(self, canvas,
                 floor: Page, layers: List[Layer], active_layers: List[Layer],
                 marker_positions_getter):
        super().__init__(canvas, floor, layers, marker_positions_getter)
        self._active_layers = [l for l in layers if l in active_layers]
        self._marker_positions_active = [mo for mo in self._marker_positions
                                         if mo.layer in self._active_layers]
        if not self._marker_positions_active:
            # skip layer group where no markers
            raise layout.NoMarkersInActiveGroupException
        self._marker_positions_inactive = [mo for mo in self._marker_positions
                                           if mo.layer not in self._active_layers]
        self._active_marker_captions = None

        self.max_collisions_allowed = 0

    def draw_content(self):
        logger.debug('start draw_content')
        self._content_box.draw_plan_image(self.canvas, **self.draw_options)

        self.draw_options['objects_opacity'] = 40
        self._draw_markers(self._marker_positions_inactive)

        self.draw_options['objects_opacity'] = 100
        self._draw_markers(self._marker_positions_active)

        self._active_marker_captions = self.place_captions(self._marker_positions_active)

        logger.debug('start _draw_marker_captions')
        self._draw_marker_captions(self._active_marker_captions)

        # self._draw_box_test_marks()

        self._draw_legend(self._active_layers)

    def place_captions(self, marker_objects: List[Object]) -> List[MarkerCaption]:
        bb_index = BoundsIndex(self.canvas, self._content_box, marker_objects)
        object_clusters = self._detect_clusters(bb_index)
        for cluster in object_clusters:
            partial_bb_index = self._place_captions_cluster(list(cluster))
            # update bb_index
            for marker in partial_bb_index.markers_bounds:
                bb_index.write(marker)

        captions_right_places = [bb.ref for bb in bb_index.markers_bounds]
        return captions_right_places

    def _detect_clusters(self, bb_index: BoundsIndex) -> List[Set[Object]]:
        buckets: List[ObjectBoundsBucket] = []
        for obj_bounds in bb_index.objects_bounds:
            near_buckets = [bucket for bucket in buckets if bucket.is_near(obj_bounds)]
            if len(near_buckets) > 1:
                replace_bucket = ObjectBoundsBucket.merge(near_buckets).add(obj_bounds)
                for nb in near_buckets:
                    buckets.remove(nb)
                buckets.append(replace_bucket)
            elif len(near_buckets) == 1:
                near_buckets[0].add(obj_bounds)
            else:
                new_bucket = ObjectBoundsBucket({obj_bounds})
                buckets.append(new_bucket)
        return [
            set(obj_bounds.ref for obj_bounds in bucket.bucket_bounds)
            for bucket in buckets
        ]

    def _place_captions_cluster(self, marker_objects: List[Object]) -> BoundsIndex:
        bb_index = BoundsIndex(self.canvas, self._content_box, marker_objects)
        # obj_groups = bb_index.determine_obj_groups()
        # bb_index.obj_groups_append_neighbours(obj_groups)
        obj_configuration = ObjectsConfiguration(bb_index.objects_bounds)
        # objects_placement_queue = self._build_placement_queue(obj_groups, marker_objects)
        objects_placement_queue = self._infer_placement_queue_from_configuration(obj_configuration)
        # if len(objects_placement_queue) > 10:
        #     print(objects_placement_queue)

        markers_queue = [obj.caption() for obj in objects_placement_queue]
        # todo rethink during
        #  refresh queue from conflicts
        #  and define error report behaviour (last page like infoplan, but black and one-side infoplan per page
        try:
            self.place_next(bb_index, markers_queue)
        except MakerPlacementAllDone:
            pass                # done, go forward
        except MarkerNoPlaceException:
            self.max_collisions_allowed = 1
            try:
                self.place_next(bb_index, markers_queue)
            except MakerPlacementAllDone:
                pass            # done, go forward
            except MarkerNoPlaceException:
                # draw with collisions then
                BoundingBox.intersect = BoundingBox.ignore_intersectins
                try:
                    self.place_next(bb_index, markers_queue)
                except MakerPlacementAllDone:
                    pass        # done, go forward

        return bb_index

    def _infer_placement_queue_from_configuration(
            self, configuration: ObjectsConfiguration
    ) -> List[Object]:
        ""
        """
        принимаем конфигурацию объектов ObjectsConfiguration
        берём из конфигурации очередной центр плотности (с фильтрацией по индексу что ещё не размещён)
        смотрим в очереди, которую строим, последний размещённый
        если последнего нет, используем центр плотности 
        если есть, то итерируемся по списку соседей (с фильтрацией по индексу что ещё не размещён)
        если "сосед" дальше двух длин подписи, всё равно используем центр плотности
        """
        _placement_queue = []
        density_centers_gen = iter(configuration.density_rank)

        def _select_next():
            while True:
                last_placed = _placement_queue[-1] if _placement_queue else None
                if last_placed:
                    neighbours_gen = configuration.neighbours_gen(last_placed)
                    try:
                        neighbour, distance = next(neighbours_gen)
                        while neighbour in _placement_queue:
                            neighbour, distance = next(neighbours_gen)
                    except StopIteration:
                        return
                    not_too_far = distance < 2 * MarkerCaption.USUAL_WIDTH
                    if not_too_far:
                        yield neighbour
                        continue

                try:
                    density_center = next(density_centers_gen)
                    while density_center in _placement_queue:
                        density_center = next(density_centers_gen)
                except StopIteration:
                    return
                yield density_center

        for obj in _select_next():
            _placement_queue.append(obj)

        return _placement_queue

    def _build_placement_queue(self, obj_group_list, marker_objects: List[Object]) -> List[Object]:
        """
        Сначала группы, затем их соседи. Затем проверить, что нет повторов.
        В конце добавить все оставшиеся
        """
        # todo обновблять порядок на основе информации о конфликта
        #  сдвигать конфликтующие в начало очереди
        queue = []
        for group in obj_group_list:    # type: NearObjectsGroup
            queue.extend(group.objects)
        for group in obj_group_list:    # type: NearObjectsGroup
            queue.extend(group.neighbours)

        queue = list(set(queue))

        objects_left = [obj for obj in marker_objects if obj not in queue]
        queue.extend(objects_left)

        return queue

    def _draw_marker_captions(self, captions):
        options = self.draw_options
        for mc in captions:   # type: MarkerCaption
            mc.draw(self.canvas, self._content_box, **options)

    def make_marker_placements(self, bb_index: BoundsIndex, current_marker: MarkerCaption)\
            -> Iterator[BoundingBox]:
        """
        Генератор положений подписи (повороты смещения) которые
        не конфликтуют с другими объектов и маркеров на основании bb_index
        :raises: MarkerNoPlaceException
        """
        place_gen = self._make_marker_placements(current_marker)
        for place in place_gen:
            if not bb_index.is_collide(place, self.max_collisions_allowed):
                yield place
            logger.info(f'make_marker_placements: place={place}, collisions: {bb_index.collisions(place)}')
        raise MarkerNoPlaceException

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
            place = current_marker.get_bounding_box(self.canvas, offset, need_rotate=need_rotate, force_update=True)
            logger.info(f'_make_marker_placements: number={current_marker.number}, {comment} -> {place}')
            yield place

    def place_next(self, bb_index: BoundsIndex, marker_place_queue: List[MarkerCaption]):
        if not marker_place_queue:
            raise MakerPlacementAllDone

        current_marker = marker_place_queue.pop(0)
        place_gen = self.make_marker_placements(bb_index, current_marker)

        def place_current():
            """
            :raises: MarkerNoPlaceException
            """
            try:
                place = next(place_gen)     # take from gen
            except MarkerNoPlaceException:
                marker_place_queue.insert(0, current_marker)
                raise
            else:
                bb_index.write(place)

        place_current()     # already may raise and we go up

        # loop need to retry in case of successful exception handling
        while True:
            try:
                self.place_next(bb_index, marker_place_queue)
            except MarkerNoPlaceException:
                # handler may in turn raise MarkerNoPlaceException too
                # and we go upper and upper
                bb_index.cancel_last_marker()
                place_current()

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


"""
разместили текущий
запускаем рекурсию
из рекурсии можем словить исключение 
  тогда переразместить текущий (может не удаться, тогда выйдем на уровень выше)
  и запустить рекусрию снова
"""
