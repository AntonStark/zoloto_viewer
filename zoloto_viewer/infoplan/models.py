import collections
import typing as t
import uuid
import re

from django.db import models, transaction


class MarkersManager(models.Manager):
    def by_layer(self, project, page=None) -> t.Dict['viewer.Layer', models.QuerySet]:  # noqa
        def _query(layer, page_) -> models.QuerySet:
            q = self.filter(layer=layer)
            if page_:
                q = q.filter(floor=page_)
            return q

        return {
            L: _query(L, page)
            for L in project.layer_set.all()
        }

    def max_last_modified(self, layer=None, page=None, project=None):
        if not any([layer, page, project]):
            raise ValueError('At least one of filtering arguments needed')
        if layer and page:
            q = self.filter(layer=layer, floor=page)
        elif layer:
            q = self.filter(layer=layer)
        elif page:
            q = self.filter(floor=page)
        else:
            q = self.filter(floor__project=project)

        lm = q.aggregate(value=models.Max('last_modified'))['value']
        return lm

    def get_numbers(self, floor, layer):
        return {m.uid: m.number
                for m in self.filter(floor=floor, layer=layer).all()}

    def get_numbers_list(self, uid_list):
        return {m.uid: m.number
                for m in self.filter(uid__in=uid_list).all()}

    def get_positions(self, floor, layer):
        return {m.uid: m.position
                for m in self.filter(floor=floor, layer=layer).all()}


class Marker(models.Model):
    """
    Отражает положение носителя выбранного типа layer в границах монтажной области floor
    """
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True)
    last_modified = models.DateTimeField(auto_now=True)

    layer = models.ForeignKey('viewer.Layer', on_delete=models.SET_NULL, null=True)
    floor = models.ForeignKey('viewer.Page', on_delete=models.CASCADE)
    ordinal = models.IntegerField(null=True, default=None)

    pos_x = models.IntegerField()
    pos_y = models.IntegerField()
    rotation = models.IntegerField(default=0)

    reviewed = models.BooleanField(default=False)

    CIRCLE_RADIUS = 15
    COMMENT_MARK_RADIUS = 2
    COMMENT_MARK_PADDING = 0.7 * CIRCLE_RADIUS

    objects = MarkersManager()

    class Meta:
        unique_together = [('floor', 'layer', 'ordinal')]
        ordering = ['ordinal']

    @property
    def all_comments_resolved(self):
        return all(c.resolved for c in self.markercomment_set.all())

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
        return f'{self.layer.title}/{self.floor.floor_caption}/{self.ordinal}'

    @property
    def neg_rotation(self):
        return -self.rotation

    @property
    def position(self):
        return self.pos_x, self.pos_y, self.rotation

    @classmethod
    def position_attrs(cls):
        return ['pos_x', 'pos_y', 'rotation']

    def save(self, *args, **kwargs):
        need_create_fingerpost_entry = not self.ordinal and self.layer.kind.is_fingerpost
        if self.ordinal is None and self.layer and self.floor:
            markers_same_series = Marker.objects.filter(layer=self.layer, floor=self.floor)
            max_ordinal = markers_same_series.aggregate(value=models.Max('ordinal'))['value']
            self.ordinal = max_ordinal + 1 if max_ordinal else 1
        self._handle_rotation()
        super().save(*args, **kwargs)
        if need_create_fingerpost_entry:
            self._create_fingerpost_entry()

    def copy(self, copy_variables=True, floor=None, pos_x=None, pos_y=None, rotation=None) -> 'Marker':
        mc = self.__class__(
            layer=self.layer,
            floor=self.floor,
            pos_x=self.pos_x,
            pos_y=self.pos_y,
            rotation=self.rotation,
        )

        if floor and floor != self.floor:
            mc.floor = floor
        else:   # move a little to prevent overlay
            mc.pos_x += 30
            mc.pos_y += 30

        if pos_x:
            mc.pos_x = pos_x
        if pos_y:
            mc.pos_y = pos_y
        if rotation:
            mc.rotation = rotation

        variables = []
        if copy_variables:
            variables = [mv.copy(marker_override=mc) for mv in self.markervariable_set.all()]

        with transaction.atomic():
            mc.save()
            MarkerVariable.objects.bulk_create(variables)
        return mc

    def serialize(self, transformations=None):
        if not transformations:
            transformations = []
        rep = self.to_json()

        rep.update({
            'comments': self.comments_json,
            'infoplan': MarkerVariable.objects.vars_of_marker_by_side(self, apply_transformations=transformations),
        })
        if self.layer.kind.is_fingerpost:
            rep.update({
                'fingerpost_data': self.markerfingerpost_set.first().to_json()
            })

        rep.update({
            'layer': {
                'title': self.layer.title,
                'color': self.layer.color.hex_code,
                'kind': {'name': self.layer.kind.name, 'sides': self.layer.kind.sides}
            }
        })
        return rep

    def to_json(self, layer=False, layer_kind=False, page=False):
        j = {
            'marker': self.uid,
            'number': self.number,
            'reviewed': self.reviewed,
            'has_comment': self.has_comments,
            'comments_resolved': self.all_comments_resolved,
            'position': {
                'center_x': self.pos_x,
                'center_y': self.pos_y,
                'rotation': self.rotation,
            }
        }
        if layer:
            j['layer'] = self.layer.title
            if layer_kind:
                j['layer_kind_name'] = self.layer.kind.name
        if page:
            j['page'] = self.floor.code
        return j

    def _handle_rotation(self):
        value = self.rotation
        while value >= 360:
            value -= 360
        while value < 0:
            value += 360
        self.rotation = value

    def _create_fingerpost_entry(self):
        MarkerFingerpost(marker=self).save()


class MarkerFingerpost(models.Model):
    """
    Содержит информацию об использовании лопастей маркера типа фингерпост
    """
    marker = models.ForeignKey(Marker, on_delete=models.CASCADE)
    side1_enabled = models.BooleanField(default=True)
    side2_enabled = models.BooleanField(default=False)
    side3_enabled = models.BooleanField(default=False)
    side4_enabled = models.BooleanField(default=False)
    side5_enabled = models.BooleanField(default=False)
    side6_enabled = models.BooleanField(default=False)
    side7_enabled = models.BooleanField(default=False)
    side8_enabled = models.BooleanField(default=False)

    def is_enabled(self, side_num: int) -> bool:
        return getattr(self, f'side{side_num}_enabled')

    def make_css_labels_string(self):
        css_classes_mapping = {
            f'pane-{i}': getattr(self, f'side{i}_enabled')
            for i in range(1, 9)
        }
        return ' '.join(klass for klass, enabled in css_classes_mapping.items() if enabled)

    def to_json(self):
        return {
            f'pane-{i}': getattr(self, f'side{i}_enabled')
            for i in range(1, 9)
        }

    def update_from_obj(self, fingerpost_obj):
        # fingerpost_obj: {
        #   panes: [{pane_number, enabled}]
        # }
        panes_data = fingerpost_obj.get('panes', None)
        if panes_data:
            for pane_obj in panes_data:
                number = pane_obj['pane_number']
                enabled = bool(pane_obj['enabled'])
                setattr(self, f'side{number}_enabled', enabled)
        self.save()


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
            marker.save()   # to update marker.last_modified

    def vars_by_side(self, queryset: models.QuerySet, apply_transformations=None):
        markers = set()
        vars_by_side = collections.defaultdict(lambda: collections.defaultdict(list))
        marker_vars = queryset.values_list('marker', 'side', 'key', 'value')
        for mu, s, _, v in marker_vars:
            vars_by_side[mu][s].append(v)
            markers.add(mu)

        if apply_transformations:
            transformed = {}
            for m in vars_by_side.keys():
                marker_infoplan = vars_by_side[m]
                infoplan_transformed = {}
                for s in marker_infoplan.keys():
                    marker_vars = marker_infoplan[s]
                    for tr in apply_transformations:
                        marker_vars = tr.apply(marker_vars, side=m)
                    infoplan_transformed[s] = marker_vars
                transformed[m] = infoplan_transformed
            vars_by_side = transformed

        return vars_by_side, markers

    def vars_of_marker_by_side(self, marker: Marker, apply_transformations=None):
        # [
        #   {marker: UUID(), side: 1, variables: ['a', 'b']},
        #   {marker: UUID(), side: 2, variables: []}
        # ]
        variables = self.filter(marker=marker)
        vars_by_side, markers = self.vars_by_side(variables, apply_transformations)
        res = [
            {
                'side': side_key,
                'variables': vars_by_side[marker_uid].get(side_key, []),
            }
            for marker_uid in markers
            for side_key in marker.layer.kind.side_keys()
        ]
        return res

    def vars_page_layer_by_side(self, page, layer, apply_transformations=None):
        variables = self.filter(marker__floor=page, marker__layer=layer)
        vars_by_side, markers = self.vars_by_side(variables, apply_transformations)
        return vars_by_side, markers

    def filter_var_containing(self, project, lang_ru: str, lang_en: str):
        # lang_ru_regex = lang_ru.replace(' ', '[\t ]+')
        # lang_en_regex = lang_en.replace(' ', '[\t ]+')
        containing = self.filter(marker__floor__project=project)\
            .filter(value__regex=lang_ru).filter(value__regex=lang_en)
        return containing.values_list('id', flat=True)

    def var_replace_helper(self, project, name_old, name_new, filter_ids_in=None):
        if not name_old and not name_new:
            return []
        if not name_old and not filter_ids_in:
            raise ValueError('unbound call no allowed')
        if name_old == name_new:
            return filter_ids_in or []

        name_regex = name_old.replace(' ', '[\t ]+')
        to_replace = self.filter(marker__floor__project=project) \
            .filter(value__regex=name_regex)
        if filter_ids_in:
            to_replace = to_replace.filter(id__in=filter_ids_in)
        changed_vars_ids = to_replace.values_list('id', flat=True)
        for v in to_replace:
            v.value = re.sub(name_regex, name_new, v.value)
            v.save()
        return changed_vars_ids


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

    PICT_PATTERN = r'@[A-z\d]+@'
    MASTER_PAGE_MARK = 'mp:'

    class Meta:
        unique_together = ['marker', 'side', 'key']
        ordering = ['side', 'key']

    def to_json(self):
        return {'key': self.key, 'side': self.side, 'value': self.value, 'wrong': self.wrong}

    def copy(self, *, marker_override, save=False):
        mv = self.__class__(marker=marker_override,
                            side=self.side,
                            key=self.key,
                            value=self.value)
        if save:
            mv.save()
        return mv


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

    @classmethod
    def layer_with_comments_by_page(cls, project):
        """
        :return: {layers, count} dict with up to 3 layers which
         has markers with comments and total count of such layers
        """
        from django.contrib.postgres.aggregates import ArrayAgg
        markers_with_comments_unresolved = Marker.objects \
            .filter(floor__project=project, markercomment__resolved=False) \
            .order_by()     # turn off sorting
        data = markers_with_comments_unresolved \
            .values_list('floor__code') \
            .annotate(colors=ArrayAgg('layer__title', distinct=True))
        truncated = {code: dict(limit_3=layers[:3], count=len(layers))
                     for code, layers in data}
        return truncated

    def to_json(self):
        return {'content': self.content, 'date_created': self.date_created, 'resolved': self.resolved}

    def resolve(self):
        self.resolved = True
        self.save()
