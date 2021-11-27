import logging
import math

from abc import abstractmethod, ABC
from dataclasses import dataclass, field
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as rc
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from zoloto_viewer.viewer.models import Layer

from . import layout

logger = logging.getLogger(__name__)


class PlanBox:
    DECLARED_PLAN_ASPECT = 365 / 227

    def __init__(self, image_pil, image_size, indd_bounds):
        self._img = ImageReader(image_pil)
        self._img_width, self._img_height = image_size
        self._indd_bounds = indd_bounds

        self._box_width, self._box_height = layout.work_area_size()
        self._box_x, self._box_y = layout.plan_area_position()

    @property
    def canvas_left(self):
        return self._box_x

    @property
    def canvas_right(self):
        return self._box_x + self._box_width

    @property
    def canvas_bottom(self):
        return self._box_y

    @property
    def canvas_top(self):
        return self._box_y + self._box_height

    @property
    def max_x(self):
        return self._img_width

    @property
    def max_y(self):
        return self._img_height

    def calc_pos(self, point):
        # нужно из points используя _indd_bounds получить координаты относительно подложки
        # и затем используя размер подложки получить координаты относительно canvas
        gb_top, gb_left, gb_bottom, gb_right = self._indd_bounds
        m_x, m_y = point
        rel_x = (m_x - gb_left) / gb_right
        can_x = self._box_x + rel_x * self._box_width
        rel_y = 1. - (m_y - gb_top) / gb_bottom      # invert y axis
        can_y = self._box_y + rel_y * self._box_height
        return can_x, can_y

    def _scale(self, point):
        gb_top, gb_left, gb_bottom, gb_right = self._indd_bounds
        factor = self._box_height / (gb_bottom - gb_top)
        return (factor * point[0], factor * point[1])

    def draw_plan_image(self, canvas: rc.Canvas, **options):
        # ведущее направеление считаем так: берём отношение ширина/высота
        # если оно больше или равно заданному тогда горизонталь ведущее направление, в противном случае вертикаль
        # если это горизонталь, обновляем self._box_height
        # если вертикаль, то нужно пересчитать ширину и сдвиг слева
        actual_aspect = self._img_width / self._img_height
        if actual_aspect >= PlanBox.DECLARED_PLAN_ASPECT:
            self._box_height = self._box_width / actual_aspect
            canvas.drawImage(self._img, x=self._box_x, y=self._box_y,
                             width=self._box_width,
                             preserveAspectRatio=True, anchor='sw')
        else:
            new_width = self._box_height * actual_aspect
            self._box_x += (self._box_width - new_width) / 2
            self._box_width = new_width
            canvas.drawImage(self._img, x=self._box_x, y=self._box_y,
                             height=self._box_height,
                             preserveAspectRatio=True, anchor='sw')


class PlanLegend:
    def __init__(self, position, y_bottom_bound, layers_count):
        self.x, self.y = position
        scale_factor = self.deduce_scale_factor(self.y, y_bottom_bound, layers_count)
        self.font_name = layout.Definitions.DEFAULT_FONT_NAME
        self.font_size = scale_factor
        self.legend_inter = 4 * scale_factor
        self.desc_padding_left = 3 * scale_factor

    def draw(self, canvas, box, layers):
        text_font_size = self.font_size
        x_mark = self.x
        x_text = x_mark + self.desc_padding_left
        marker_font_size = 3 * text_font_size

        y_top_line = self.y + self.legend_inter
        for l in layers:
            y_top_line = y_top_line - self.legend_inter
            y_next_line = y_top_line - 1.5 * text_font_size

            object_example = Object(x=x_mark, y=y_top_line, a=0, number='', layer=l)
            object_example.draw(canvas, box, convert_pos=False, font_size=marker_font_size)

            canvas.setFont(self.font_name, text_font_size)
            canvas.setFillColor(colors.black)
            canvas.drawString(x_text, y_top_line, l.title)
            canvas.drawString(x_text, y_next_line, l.desc)

    def deduce_scale_factor(self, y_top, y_bottom_bound, layers_count):
        # y_next_line = y_top - 4 * SCALE_FACTOR * (layers_count - 1) - 1.5 * SCALE_FACTOR
        # y_next_line_min = y_top - SCALE_FACTOR * (4 * layers_count - 1.5)
        try_values = [7, 6, 5, 4]

        def probe(scale_factor):
            y_min = y_top - scale_factor * (4 * layers_count - 1.5)
            is_above_bound = y_min > y_bottom_bound
            return is_above_bound

        for value in try_values:
            if probe(value):
                return value
        return try_values[-1]


@dataclass
class Object:
    x: int
    y: int
    a: int
    number: str

    layer: Layer
    layer_id: int = field(init=False)
    layer_color: dict = field(init=False)
    layer_kind: int = field(init=False)

    marker: Any = field(default=None, init=False)
    bounding_box: 'BoundingBox' = field(init=False, default=None)

    # расстояние от центра объекта до ближнего края подписи
    class Offset:
        LEFT = -10
        RIGHT = 10
        TOP = 10
        BOTTOM = -10

    def __hash__(self):
        return hash((self.x, self.y, self.a, self.number))

    def __post_init__(self):
        while self.a < 0:
            self.a += 360
        while self.a >= 360:
            self.a -= 360

        l = self.layer
        self.layer_id = l.id
        self.layer_color = layout.color_adapter(l.color.rgb_code)
        self.layer_kind = l.kind.id

    def __repr__(self):
        return f'<{self.__class__.__name__} number={self.number}>'

    @property
    def center(self):
        return self.x, self.y

    @property
    def position(self):
        return self.x, self.y, self.a

    @property
    def _symbol(self):
        MARKS = {
            1: '\uE901',
            2: '\uE902',
            3: '\uE903',
            4: '\uE904',
            5: '\uE900',
        }
        symbol = MARKS[self.layer_kind]
        return symbol

    @classmethod
    def caption_offset(cls, object_rotation, object_kind):
        offset_left = offset_top = 0
        need_rotate = False
        if object_kind == 1:
            return cls._caption_offset_kind1(object_rotation)
        elif object_kind == 2:
            if 31 <= object_rotation <= 149:
                need_rotate = True
                offset_top = cls.Offset.TOP
            elif 150 <= object_rotation <= 210:
                offset_left = cls.Offset.LEFT
            elif 211 <= object_rotation <= 329:
                need_rotate = True
                offset_top = cls.Offset.BOTTOM
            else:   # object_rotation <= 30 or 330 <= object_rotation
                offset_left = cls.Offset.RIGHT
        else:
            if 31 <= object_rotation <= 149:
                offset_left = cls.Offset.RIGHT
            elif 150 <= object_rotation <= 210:
                need_rotate = True
                offset_top = cls.Offset.TOP
            elif 211 <= object_rotation <= 329:
                offset_left = cls.Offset.LEFT
            else:   # object_rotation <= 30 or 330 <= object_rotation
                need_rotate = True
                offset_top = cls.Offset.BOTTOM
        offset = (offset_left, offset_top)
        return offset, need_rotate

    @classmethod
    def _caption_offset_kind1(cls, object_rotation):
        offset_left = offset_top = 0
        need_rotate = False
        if 31 <= object_rotation <= 149:
            offset_left = cls.Offset.RIGHT
            if 105 < object_rotation:
                offset_top = cls.Offset.TOP
            elif object_rotation < 75:
                offset_top = cls.Offset.BOTTOM
            else:
                pass    # offset_top = 0
        elif 150 <= object_rotation <= 210:
            need_rotate = True
            offset_top = cls.Offset.TOP
            if object_rotation < 165:
                offset_left = cls.Offset.RIGHT
            elif 195 < object_rotation:
                offset_left = cls.Offset.LEFT
            else:
                pass    # offset_left = 0
        elif 211 <= object_rotation <= 329:
            offset_left = cls.Offset.LEFT
            if object_rotation < 255:
                offset_top = cls.Offset.TOP
            elif 285 < object_rotation:
                offset_top = cls.Offset.BOTTOM
            else:
                pass    # offset_top = 0
        else:   # object_rotation <= 30 or 330 <= object_rotation
            need_rotate = True
            offset_top = cls.Offset.BOTTOM
            if 15 < object_rotation:
                offset_left = cls.Offset.RIGHT
            elif 330 <= object_rotation < 345:
                offset_left = cls.Offset.LEFT
            else:
                pass    # offset_left = 0
        offset = (offset_left, offset_top)
        return offset, need_rotate

    def caption(self) -> 'MarkerCaption':
        if not self.marker:
            self.marker = MarkerCaption(self.number, rotation=0, obj=self)
        return self.marker

    def get_bounding_box(self, canvas, box, font_size=None):
        if self.bounding_box:
            return self.bounding_box

        # box.calc_pos() осуществляет перенос и растяжение (через процентные координаты),
        # а canvas отдаёт абсолютные размеры длины и высоты строки,
        # поэтому растяжение должно быть применено на этом шаге
        font, size = self._font_options(font_size)
        canvas.setFont(font, size)
        str_width_fix = 8
        width = canvas.stringWidth(self._symbol) - str_width_fix
        height = width

        # center coordinates
        x, y = box.calc_pos(self.center)
        left = x - width / 2
        bottom = y - height / 2

        bounding_box = BoundingBox(left, bottom, width, height, ref=self)
        self.bounding_box = bounding_box
        return bounding_box

    def get_bounding_circle(self, canvas, box, font_size=None) -> 'BoundingCircle':
        # center coordinates
        x, y = box.calc_pos(self.center)

        font, size = self._font_options(font_size)
        canvas.setFont(font, size)
        str_width_fix = 8
        width = canvas.stringWidth(self._symbol) - str_width_fix
        r = width // 2
        return BoundingCircle(x, y, r, ref=self)

    def _font_options(self, font_size=None):
        font = layout.Definitions.MARK_FONT_NAME
        size = font_size or layout.Definitions.MARK_FONT_SIZE
        return font, size

    def draw(self, canvas, box, convert_pos=True, font_size=None, **options):
        self.get_bounding_box(canvas, box)  # for attr cache

        font, size = self._font_options(font_size)
        _centralize_height = - size / 2
        opacity = options.get('objects_opacity', 100)
        alpha = opacity / 100

        if convert_pos:
            x, y = box.calc_pos(self.center)
        else:
            x, y = self.center
        rotation = self.a

        canvas.saveState()
        layout.set_colors(canvas, self.layer_color, alpha=alpha)
        canvas.setFont(font, size)
        canvas.translate(x, y)
        canvas.rotate(rotation)
        canvas.drawCentredString(0, _centralize_height, self._symbol)
        canvas.restoreState()

        # debug only
        debug_boxes = False
        main_object = alpha == 1
        if debug_boxes and main_object:
            canvas.saveState()
            bb = self.get_bounding_box(canvas, box)
            canvas.translate(bb.x, bb.y)
            canvas.setStrokeColor(colors.red)
            canvas.rect(0, 0, bb.w, bb.h, stroke=1, fill=0)
            canvas.restoreState()

        # debug only
        debug_circles = False
        if debug_circles and main_object:
            canvas.saveState()
            bc = self.get_bounding_circle(canvas, box)
            canvas.translate(bc.cx, bc.cy)
            canvas.setStrokeColor(colors.red)
            canvas.circle(0, 0, bc.r)
            canvas.restoreState()

    def get_caption_offset(self, increase_a=None, cross_delta=None):
        a_ = self.a
        if increase_a:
            a_ += increase_a
        offset, need_rotate = self.__class__.caption_offset(a_, self.layer_kind)
        if cross_delta:
            if need_rotate:     # apply delta to horizontal offset
                offset = (offset[0] + cross_delta, offset[1])
            else:
                offset = (offset[0], offset[1] + cross_delta)
        return offset, need_rotate


@dataclass
class MarkerCaption:
    CAPTION_FONT_NAME = 'Helvetica'
    CAPTION_FONT_SIZE = 6
    USUAL_WIDTH = 6 * CAPTION_FONT_SIZE

    number: str
    rotation: int

    obj: Object
    bounding_box: 'BoundingBox' = field(init=False, default=None)

    def __repr__(self):
        return f'<{self.__class__.__name__} number={self.number}>'

    def draw(self, canvas, box, **_):
        if not self.bounding_box:
            offset, need_rotate = self.obj.get_caption_offset()
            self.get_bounding_box(canvas, offset, need_rotate)   # to set cached attr

        x, y = self.bounding_box.x, self.bounding_box.y
        width = self.bounding_box.w
        height = self.bounding_box.h
        need_rotate = self.rotation == 90

        canvas.saveState()
        layout.set_colors(canvas, self.obj.layer_color)
        canvas.setFont(self.CAPTION_FONT_NAME, self.CAPTION_FONT_SIZE)
        canvas.translate(x, y)
        if need_rotate:
            canvas.rotate(self.rotation)
            canvas.rect(0, -1, height, width, stroke=0, fill=1)
        else:
            canvas.rect(0, -1, width, height, stroke=0, fill=1)
        canvas.setFillColor(colors.white)
        canvas.drawString(0, 0, self.number)
        canvas.restoreState()

    def get_bounding_box(self, canvas, offset, need_rotate=False, force_update=False) -> 'BoundingBox':
        # сначала без rotate
        # offset нужно применять к центру объекта
        # и если он отрицательный, то дополнительно уменьшать на длину маркера
        if self.bounding_box and not force_update:
            return self.bounding_box

        if need_rotate:
            return self._get_bounding_box_rotate(canvas, offset)

        canvas.setFont(self.CAPTION_FONT_NAME, self.CAPTION_FONT_SIZE)
        width = canvas.stringWidth(self.number)
        height = self.CAPTION_FONT_SIZE

        offset_x, offset_y = offset
        obj_xc = self.obj.bounding_box.x + self.obj.bounding_box.w // 2
        obj_yc = self.obj.bounding_box.y + self.obj.bounding_box.h // 2

        # text length
        if offset_x < 0:
            offset_x -= width
        # center to down left corner
        offset_y -= height // 2

        left = obj_xc + offset_x
        bottom = obj_yc + offset_y

        bounding_box = BoundingBox(left, bottom, width, height, ref=self)
        self.bounding_box = bounding_box
        self.rotation = 0
        return self.bounding_box

    def _get_bounding_box_rotate(self, canvas, offset):
        offset_x, offset_y = offset
        obj_xc = self.obj.bounding_box.x + self.obj.bounding_box.w // 2
        obj_yc = self.obj.bounding_box.y + self.obj.bounding_box.h // 2

        canvas.setFont(self.CAPTION_FONT_NAME, self.CAPTION_FONT_SIZE)
        height = canvas.stringWidth(self.number)
        width = self.CAPTION_FONT_SIZE

        # text length
        if offset_y < 0:
            offset_y -= height
        offset_x += width // 2  # move to the right so text vertical centered

        left = obj_xc + offset_x
        bottom = obj_yc + offset_y
        bounding_box = BoundingBox(left, bottom, width, height, ref=self)
        self.bounding_box = bounding_box
        self.rotation = 90
        return self.bounding_box


class Bounds(ABC):
    ref: Union[Object, MarkerCaption]

    @abstractmethod
    def intersect(self, other: 'Bounds'):
        pass


@dataclass(frozen=True)
class BoundingCircle(Bounds):
    cx: int
    cy: int
    r: int

    ref: Union[Object, MarkerCaption]

    def __repr__(self):
        return f'BC({self.cx:.0f},{self.cy:.0f}){self.r:.0f}/{self.ref.number}'

    def intersect(self, other: 'Bounds'):
        return False    # no matter for now


@dataclass
class BoundingBox(Bounds):
    x: int
    y: int
    w: int
    h: int

    ref: Union[Object, MarkerCaption]

    def __repr__(self):
        return f'BB[{self.x:.0f}:{self.x + self.w:.0f}],[{self.y:.0f}:{self.y + self.h:.0f}]/{self.ref.number}'

    def intersect(self, other: 'Bounds'):
        if isinstance(other, BoundingBox):
            return self._intersect_box(other)
        elif isinstance(other, BoundingCircle):
            return self._intersect_circle(other)
        else:
            return False    # ignore unknown shapes

    def ignore_intersectins(self, other: 'BoundingBox'):
        # todo log intersections
        return False

    def _intersect_box(self, other: 'BoundingBox'):
        # add 5px margins to other
        margins = 5

        s_x_min, s_x_max = self.x, self.x + self.w
        o_x_min, o_x_max = other.x - margins, other.x + other.w + margins
        leftmost_right = min(s_x_max, o_x_max)
        rightmost_left = max(s_x_min, o_x_min)
        x_overlap = leftmost_right > rightmost_left

        s_y_min, s_y_max = self.y, self.y + self.h
        o_y_min, o_y_max = other.y - margins, other.y + other.h + margins
        bottommost_top = min(s_y_max, o_y_max)
        topmost_bottom = max(s_y_min, o_y_min)
        y_overlap = bottommost_top > topmost_bottom
        is_intersect = x_overlap and y_overlap
        return is_intersect

    def _intersect_circle(self, other: 'BoundingCircle'):
        # add 5px margins to other
        margins = 5
        rad_margins = other.r + margins

        s_x_min, s_x_max = self.x, self.x + self.w
        o_x_min, o_x_max = other.cx - rad_margins, other.cx + rad_margins
        leftmost_right = min(s_x_max, o_x_max)
        rightmost_left = max(s_x_min, o_x_min)
        x_overlap = leftmost_right > rightmost_left

        s_y_min, s_y_max = self.y, self.y + self.h
        o_y_min, o_y_max = other.cy - rad_margins, other.cy + rad_margins
        bottommost_top = min(s_y_max, o_y_max)
        topmost_bottom = max(s_y_min, o_y_min)
        y_overlap = bottommost_top > topmost_bottom
        is_intersect = x_overlap and y_overlap
        return is_intersect


class BoundsIndex:
    def __init__(self, canvas, plan_box, objects):
        self._objects = [
            m.get_bounding_circle(canvas, plan_box)
            for m in objects
        ]
        self._markers = []

    def __iter__(self) -> Bounds:
        for obj__bb in self._objects:
            yield obj__bb
        for mc_bb in self._markers:
            yield mc_bb

    @property
    def last_placed_obj(self) -> Optional[Object]:
        if self._markers:
            last_marker = self._markers[-1].ref
            return last_marker.obj

    @property
    def objects_bounds(self) -> List[BoundingCircle]:
        return self._objects.copy()

    @property
    def markers_bounds(self) -> List[Bounds]:
        return self._markers.copy()

    def cancel_last_marker(self):
        self._markers.pop()

    def collisions(self, box: BoundingBox):
        def own_obj(bb):
            box_is_caption = type(box.ref) == MarkerCaption
            bb_is_object = type(bb.ref) == Object
            return box_is_caption and bb_is_object and box.ref.obj == bb.ref

        buf = []
        for bb in self:     # type: Bounds
            if box.intersect(bb):
                # marker of object may be close
                if not own_obj(bb):
                    buf.append(bb)
        return buf

    def determine_obj_groups(self) -> List['NearObjectsGroup']:
        """
        Определяем группы маркеров расположенных близко друг другу по bb_index
        Нужно сначала перебрать все пары и если что найдём объединить по транзитивности
        """
        # todo
        return [NearObjectsGroup(objects=[])]

    def is_collide(self, box: BoundingBox, allow=0):
        def own_obj(bb):
            box_is_caption = type(box.ref) == MarkerCaption
            bb_is_object = type(bb.ref) == Object
            return box_is_caption and bb_is_object and box.ref.obj == bb.ref

        count = 0
        for bb in self:     # type: Bounds
            if box.intersect(bb):
                # marker of object may be close
                if not own_obj(bb):
                    count += 1
                    if count > allow:
                        return True
        return False

    def is_object_placed(self, obj: Object):
        for m in self._markers:
            if m.ref == obj:
                return True
        return False

    def obj_groups_append_neighbours(self, obj_group_list):
        for group in obj_group_list:    # type: NearObjectsGroup
            group.find_neighbours(self)

    def write(self, place: Bounds):
        self._markers.append(place)


def is_objects_one_cluster(obj1: BoundingCircle, obj2: BoundingCircle) -> bool:
    caption_width = MarkerCaption.USUAL_WIDTH
    caption_height = MarkerCaption.CAPTION_FONT_SIZE

    dx = abs(obj1.cx - obj2.cx)
    dy = abs(obj1.cy - obj2.cy)

    near_horizontal = (dx < 2 * caption_width) and (dy < 3 * caption_height)
    near_vertical = (dx < 3 * caption_height) and (dy < 2 * caption_width)
    return near_horizontal or near_vertical


def get_objects_distance(obj1: BoundingCircle, obj2: BoundingCircle) -> float:
    dx = abs(obj1.cx - obj2.cx)
    dy = abs(obj1.cy - obj2.cy)
    return math.sqrt(math.pow(dx, 2)  + math.pow(dy, 2))


@dataclass
class ObjectBoundsBucket:
    bucket_bounds: Set[BoundingCircle] = field(default_factory=set)

    def is_near(self, other):
        for bound in self.bucket_bounds:
            if self.near_predicate(other, bound):
                return True
        return False

    def add(self, elem):
        self.bucket_bounds.add(elem)
        return self

    @classmethod
    def near_predicate(cls, obj1, obj2):
        return is_objects_one_cluster(obj1, obj2)

    @classmethod
    def merge(cls, buckets: List['ObjectBoundsBucket']):
        merged = set.union(*[bucket.bucket_bounds for bucket in buckets])
        return cls(bucket_bounds=merged)


class ObjectsConfiguration:
    def __init__(self, object_circles: List[BoundingCircle]):
        self._obj_circles: List[BoundingCircle] = object_circles
        self._obj_index: List[Object] = [obj.ref for obj in self._obj_circles]
        self._distance_list: List[Tuple[int, int, float]] = self._calc_distances_list()

        self.neighbours_index: Dict[Object, List[Tuple[Object, float]]] = self._make_neighbours_index()
        self.density_rank: List[Object] = self._make_density_rank()

    def neighbours_gen(self, obj: Object) -> Tuple[Object, float]:
        for neighbour, distance in self.neighbours_index[obj]:
            yield neighbour, distance

    def _calc_distances_list(self) -> List[Tuple[int, int, float]]:
        return [
            (i, j, get_objects_distance(obj1, obj2) )
            for i, obj1 in enumerate(self._obj_circles)
            for j, obj2 in enumerate(self._obj_circles)
            if obj2 != obj1
        ]

    def _make_density_rank(self) -> List[Object]:
        def density(selected: int) -> float:
            if self._distance_list:
                return 1. / sum(d for i, j, d in self._distance_list if i == selected)
            else:
                return 1.

        def tuple_to_density(index_obj_tuple):
            return density(index_obj_tuple[0])

        return [
            obj
            for i, obj in sorted(
                enumerate(self._obj_index), key=tuple_to_density, reverse=True
            )
        ]

    def _make_neighbours_index(self) -> Dict[Object, List[Tuple[Object, float]]]:
        def neighbours(selected: int) -> List[Tuple[Object, float]]:
            # итерируемся по списку обращая внимание только на кортежи где на первом месте selected
            def by_distance(ind_distance_tuple): return ind_distance_tuple[0]

            slice = [(j, d) for i, j, d in self._distance_list if i == selected]
            return [
                (self._obj_index[j], d)
                for j, d in sorted(slice, key=by_distance)
            ]

        return {
            obj1: neighbours(i)
            for i, obj1 in enumerate(self._obj_index)
        }

@dataclass
class NearObjectsGroup:
    objects: List[Object]
    neighbours: List[Object] = field(init=False, default_factory=list)

    def find_neighbours(self, bb_index: BoundsIndex):
        """
        Добавить к группе близкие к ней объекты по
        горизонтали или вертикали (соседей ищем по удалённости на длину/высоту подписи)
        """
        pass    # todo


class MarkerNoPlaceException(Exception):
    pass


class MakerPlacementAllDone(Exception):
    pass
