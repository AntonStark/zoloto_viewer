from django.db.models import Count
from django.db.models.functions import Length

from zoloto_viewer.infoplan.models import MarkerVariable


def calc_variable_metrics(markers):
    longest_variable = MarkerVariable.objects.filter(marker__in=markers) \
        .annotate(val_len=Length('value')).order_by('-val_len').first()
    max_var_marker = markers.annotate(var_count=Count('markervariable')).order_by('-var_count').first()
    return longest_variable.value, max_var_marker.var_count
