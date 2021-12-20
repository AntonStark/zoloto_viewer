import pickle
import redis

from django.conf import settings
from datetime import datetime, timezone
from typing import Any, List, Optional, Tuple

redis_cache = redis.Redis.from_url(settings.REDIS_URL)


def drop_group_caches(layer_group: 'LayerGroup'):
    keys = [
        make_cache_key(page, layer_group)
        for page in layer_group.project.page_set.all()
    ]
    redis_cache.delete(*keys)


def make_cache_key(floor: 'Page', layer_group: 'LayerGroup'):
    return f'marker_placements__floor_{floor.uid}_layer_group_{layer_group.id}'


def check_for_cache(floor, layer_group) -> Optional[Tuple[Any, datetime]]:
    key_ = make_cache_key(floor, layer_group)
    if key_ not in redis_cache:
        return

    val_ = redis_cache[key_]
    placement, timestamp = pickle.loads(val_)
    return placement, timestamp


def store_in_cache(floor, layer_group, placement):
    obj = (placement, datetime.now(tz=timezone.utc))
    val_ = pickle.dumps(obj)
    key_ = make_cache_key(floor, layer_group)

    redis_cache[key_] = val_


def is_cache_fresh(floor: 'Page', layers: List['Layers'], timestamp: datetime) -> bool:
    max_layers_updated = max(l.date_updated for l in layers)
    max_date_updated = max(floor.date_updated, max_layers_updated)
    try:
        return max_date_updated < timestamp
    except TypeError:
        return False
