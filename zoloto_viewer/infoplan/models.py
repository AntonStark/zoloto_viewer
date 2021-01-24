import uuid
from django.contrib.postgres import fields
from django.db import models
from django.utils.safestring import mark_safe


class MarkersManager(models.Manager):
    def remove_excess(self, layer, actual_numbers):
        self.filter(layer=layer).exclude(number__in=actual_numbers).delete()

    def create_missing(self, layer, page_by_caption, markers_info):
        existing = set(self.filter(layer=layer).values_list('number', flat=True))
        for number, params in markers_info.items():
            if number in existing:
                continue

            m_path, m_vars, indd_floor, n = params
            if indd_floor not in page_by_caption:
                continue    # skip marker creation if page does not loaded yet
            else:
                floor = page_by_caption[indd_floor]

            self.create(layer=layer, floor=floor, number=number, points=m_path)

    def update_variables(self, layer, marker_info):
        """
        :param marker_info: { number -> (path, vars, indd_floor, n) }
        """
        for number, params in marker_info.items():
            try:
                marker = self.get(layer=layer, number=number)
            except self.model.DoesNotExist:
                continue    # some of numbers may not have markers due to skip missing pages
            else:
                MarkerVariable.objects.reset_values(marker, params[1])


class Marker(models.Model):
    """
    После загрузки нового csv данные об ошибках стираются
    """
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True)

    layer = models.ForeignKey('viewer.Layer', on_delete=models.SET_NULL, null=True)
    floor = models.ForeignKey('viewer.Page', on_delete=models.CASCADE)
    ordinal = models.IntegerField(null=True, default=None)

    points = fields.JSONField(default=list)     # [ [P], ..., [P] ] | [ [P1, P2, P3], ... ], P = [x: float, y: float]
    pos_x = models.IntegerField()
    pos_y = models.IntegerField()
    rotation = models.IntegerField(default=0)

    correct = models.BooleanField(null=True, default=None)

    objects = MarkersManager()
    CIRCLE_RADIUS = 5
    COMMENT_MARK_PADDING = 0.7 * CIRCLE_RADIUS

    class Meta:
        unique_together = [('floor', 'layer', 'ordinal')]

    @property
    def comments_resolved(self):
        return all(self.markercomment_set.values_list('resolved', flat=True))

    @property
    def has_comments(self):
        return bool(self.markercomment_set.count())

    @property
    def number(self):
        return '/'.join([self.layer.title, self.floor.floor_caption, str(self.ordinal)])

    @staticmethod
    def multipoint_mid(mp):
        if len(mp) == 3:        # multipoint = [P1, P2, P3]
            return mp[1]        # ignore splines for now
        elif len(mp) == 1:      # multipoint = [P]
            return mp[0]
        else:
            return None

    def save(self, *args, **kwargs):
        if self.ordinal is None and self.layer and self.floor:
            markers_same_series = Marker.objects.filter(layer=self.layer, floor=self.floor)
            max_ordinal = markers_same_series.aggregate(value=models.Max('ordinal'))['value']
            self.ordinal = max_ordinal + 1 if max_ordinal else 1
        super().save(*args, **kwargs)

    def svg_item(self):
        def _point(p):
            return f'{p[0]} {p[1]}'

        points_attr = ', '.join(_point(p) for p in map(Marker.multipoint_mid, self.points) if p is not None)
        return mark_safe(f'<polygon points="{points_attr}" class="plan_marker" data-marker-uid="{self.uid}"/>')

    def path(self):
        middle_points = filter(None, map(Marker.multipoint_mid, self.points))
        return ', '.join(map(lambda p: f'{p[0]} {p[1]}', middle_points))

    # todo review draw marker during pdf generation
    def polygon_points(self):
        return list(map(Marker.multipoint_mid, self.points))

    def center_position(self):
        points = [p for p in map(Marker.multipoint_mid, self.points) if p is not None]
        return sum([p[0] for p in points]) / len(points), sum([p[1] for p in points]) / len(points)

    def ord_number(self):
        return int(self.number.split('/')[-1])

    def to_json(self):
        return {
            'marker': self.uid,
            'number': self.number,
            'correct': self.correct,
            'has_comment': self.has_comments,
            'comments_resolved': self.comments_resolved,
            'position': {
                'center_x': self.pos_x,
                'center_y': self.pos_y,
                'rotation': self.rotation,
            }
        }

    def has_errors(self):
        return self.markervariable_set.filter(wrong=True).exists()

    def deduce_correctness(self, force_true_false=False, save=False):
        """
        В случае явного (explicit) выхода отсутствие ошибок -- достаточное условие для correct = True,
        а при неявном -- в отсутствии ошибок необходимо наличие коммента
        """
        return  # disable marker correctness for now

        if self.has_errors():
            self.correct = False
        else:
            if force_true_false or self.has_comments or self.correct is not None:
                self.correct = True
        if save:
            self.save()


class VariablesManager(models.Manager):
    def reset_values(self, marker, new_variables):
        def _reset_from_dict(m, vars_dict):
            self.filter(marker=m).delete()
            self.bulk_create(
                self.model(marker=m, key=k, value=v)
                for k, v in vars_dict.items()
                if v != ''
            )

        if isinstance(new_variables, dict):
            _reset_from_dict(marker, new_variables)
        elif isinstance(new_variables, (list, tuple)):
            _reset_from_dict(marker, dict(enumerate(new_variables, 1)))
        else:
            raise TypeError('new_variables must be dict, list or tuple')

    def reset_wrong_statuses(self, marker, dict_of_wrongness: dict):
        vars_by_key = dict(map(lambda v: (v.key, v), self.filter(marker=marker).all()))
        for key, is_wrong in dict_of_wrongness.items():
            if key in vars_by_key:
                vars_by_key[key].wrong = bool(is_wrong)
        self.bulk_update(vars_by_key.values(), ['wrong'])

    def vars_of_marker(self, marker):
        return sorted(MarkerVariable.objects.filter(marker=marker).all(), key=lambda v: int(v.key))


class MarkerVariable(models.Model):
    """
    При обновлении набора переменных маркера, все становятся
    wrong = False даже если value не изменилось
    """
    marker = models.ForeignKey(Marker, on_delete=models.CASCADE)

    key = models.CharField(max_length=32, blank=False, editable=False)
    value = models.TextField()
    wrong = models.BooleanField(null=False, default=False)

    objects = VariablesManager()

    class Meta:
        unique_together = ['marker', 'key']

    def to_json(self):
        return {'key': self.key, 'value': self.value, 'wrong': self.wrong}


class MarkerComment(models.Model):
    """
    Позволяет вести список комментариев маркера
    """
    marker = models.ForeignKey(Marker, on_delete=models.CASCADE)
    content = models.TextField()
    date_created = models.DateTimeField(auto_now=True)
    resolved = models.BooleanField(null=False, default=False)

    class Meta:
        ordering = ['date_created']
