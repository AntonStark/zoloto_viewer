import base64

from zoloto_viewer.viewer.models import Project


def parse_ignore_files(req_post):
    return {v for k, v in req_post.items() if k.startswith('ignore_file_')}


def parse_pages(req_post, req_files):
    CAPTION_LABEL = 'floor_caption_'

    ignore_files = parse_ignore_files(req_post)
    floor_captions = {}
    for k, v in req_post.items():
        if k.startswith(CAPTION_LABEL):
            encoded = k[len(CAPTION_LABEL):]
            filename = base64.decodebytes(encoded.encode('utf-8')).decode('utf-8')
            floor_captions[filename] = v

    new_pages_dict = {}
    for key in req_files.keys():
        for f in req_files.getlist(key):
            if f.name in ignore_files:
                continue

            mime_type = f.content_type.split('/')[0]
            name = '.'.join(f.name.split('.')[:-1])
            if mime_type == 'image':
                # if that name was before, it will overridden in accordance with form "replace" behaviour
                new_pages_dict[name] = (f, floor_captions.get(f.name, None))
    return new_pages_dict, floor_captions


def parse_offsets(req_post):
    CAPTION_LABEL = 'floor_caption_'
    OFFSET_LABEL = 'floor_offset_'

    floor_captions = {}
    floor_offsets = {}
    for k, v in req_post.items():
        if k.startswith(CAPTION_LABEL):
            encoded = k[len(CAPTION_LABEL):]
            filename = base64.decodebytes(encoded.encode('utf-8')).decode('utf-8')
            floor_captions[filename] = v
        elif k.startswith(OFFSET_LABEL):
            encoded = k[len(OFFSET_LABEL):]
            filename = base64.decodebytes(encoded.encode('utf-8')).decode('utf-8')
            floor_offsets[filename] = int(v)

    captions_to_offsets = {
        floor_captions[filename]: offset
        for filename, offset in floor_offsets.items()
    }
    floor_offsets = captions_to_offsets
    return floor_offsets


def parse_levels(req_post):
    CAPTION_LABEL = 'floor_caption_'
    LEVEL_LABEL = 'floor_level_'

    floor_captions = {}
    floor_levels = {}
    for k, v in req_post.items():
        if k.startswith(CAPTION_LABEL):
            encoded = k[len(CAPTION_LABEL):]
            filename = base64.decodebytes(encoded.encode('utf-8')).decode('utf-8')
            floor_captions[filename] = v
        elif k.startswith(LEVEL_LABEL):
            encoded = k[len(LEVEL_LABEL):]
            filename = base64.decodebytes(encoded.encode('utf-8')).decode('utf-8')
            floor_levels[filename] = v

    captions_to_levels = {
        floor_captions[filename]: offset
        for filename, offset in floor_levels.items()
    }
    floor_levels = captions_to_levels
    return floor_levels


def files_to_delete(req_post):
    """
    :return: tuple with two sets, first for .csv files and second with non-csv (pages)
    """
    to_delete = {v for k, v in req_post.items() if k.startswith('delete_file_')}
    csv_files = {v for v in to_delete if v.endswith('.csv')}
    non_csv_files = {v for v in to_delete if not v.endswith('.csv')}
    return csv_files, non_csv_files
