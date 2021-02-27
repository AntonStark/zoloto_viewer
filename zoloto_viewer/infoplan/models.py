import collections
import uuid
from django.contrib.postgres import fields
from django.db import models, transaction


class Marker(models.Model):
    """
    Отражает положение носителя выбранного типа layer в границах монтажной области floor
    """
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True)

    layer = models.ForeignKey('viewer.Layer', on_delete=models.SET_NULL, null=True)
    floor = models.ForeignKey('viewer.Page', on_delete=models.CASCADE)
    ordinal = models.IntegerField(null=True, default=None)

    pos_x = models.IntegerField()
    pos_y = models.IntegerField()
    rotation = models.IntegerField(default=0)

    correct = models.BooleanField(null=True, default=None)  # todo remove after pdf generation review (point too)
    points = fields.JSONField(default=list)     # [ [P], ..., [P] ] | [ [P1, P2, P3], ... ], P = [x: float, y: float]

    CIRCLE_RADIUS = 15
    COMMENT_MARK_RADIUS = 2
    COMMENT_MARK_PADDING = 0.7 * CIRCLE_RADIUS

    class Meta:
        unique_together = [('floor', 'layer', 'ordinal')]

    @property
    def all_comments_resolved(self):
        return all(self.markercomment_set.values_list('resolved', flat=True))

    @property
    def comments_json(self):
        return [c.to_json() for c in self.markercomment_set.all()]

    @property
    def has_comments(self):
        return bool(self.markercomment_set.count())

    @property
    def has_errors(self):
        return self.markervariable_set.filter(wrong=True).exists()

    @property
    def number(self):
        return '/'.join([self.layer.title, self.floor.floor_caption, str(self.ordinal)])

    @classmethod
    def position_attrs(cls):
        return ['pos_x', 'pos_y', 'rotation']

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

    def polygon_points(self):
        # 9todo review draw marker during pdf generation
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
            'comments_resolved': self.all_comments_resolved,
            'position': {
                'center_x': self.pos_x,
                'center_y': self.pos_y,
                'rotation': self.rotation,
            }
        }


class VariablesManager(models.Manager):
    def reset_values(self, marker, vars_by_side):
        with transaction.atomic():
            marker.markervariable_set.all().delete()
            variables = []
            for side, side_vars in vars_by_side.items():
                variables += [
                    MarkerVariable(marker=marker, side=side, key=k, value=v)
                    for k, v in enumerate(side_vars, start=1)
                ]
            self.bulk_create(variables)

    def vars_of_marker(self, marker):
        return marker.markervariable_set.all()

    def vars_by_side(self, marker: Marker, apply_transformations=None):
        # [
        #   {side: 1, variables: ['a', 'b']},
        #   {side: 2, variables: []}
        # ]
        vars = marker.markervariable_set.values_list('side', 'key', 'value')
        vars_by_side = collections.defaultdict(list)
        for s, k, v in vars:
            vars_by_side[s].append(v)

        if apply_transformations:
            transformed = {}
            for s in vars_by_side.keys():
                vars = vars_by_side[s]
                for tr in apply_transformations:
                    vars = tr.apply(vars, side=s)
                transformed[s] = vars
            vars_by_side = transformed

        res = [
            {'side': side_key, 'variables': vars_by_side.get(side_key, [])}
            for side_key in marker.layer.kind.side_keys()
        ]
        return res


class MarkerVariable(models.Model):
    """
    При обновлении набора переменных маркера, все становятся
    wrong = False даже если value не изменилось
    """
    marker = models.ForeignKey(Marker, on_delete=models.CASCADE)

    side = models.IntegerField(default=0)
    key = models.IntegerField(null=False, editable=False)
    value = models.TextField()
    wrong = models.BooleanField(null=False, default=False)

    objects = VariablesManager()

    class Meta:
        unique_together = ['marker', 'side', 'key']
        ordering = ['side', 'key']

    def to_json(self):
        return {'key': self.key, 'side': self.side, 'value': self.value, 'wrong': self.wrong}


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

    def to_json(self):
        return {'content': self.content, 'date_created': self.date_created, 'resolved': self.resolved}

    def resolve(self):
        self.resolved = True
        self.save()
