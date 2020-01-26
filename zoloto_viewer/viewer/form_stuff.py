import base64


def parse_ignore_files(req_post):
    return {v for k, v in req_post.items() if k.startswith('ignore_file_')}


def parse_pages(req_post, req_files):
    ignore_files = parse_ignore_files(req_post)
    floor_captions = {}
    for k, v in req_post.items():
        if k.startswith('floor_caption_'):
            encoded = k[14:]
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


def files_to_delete(req_post):
    """
    :return: tuple with two sets, first for .csv files and second with non-csv (pages)
    """
    to_delete = {v for k, v in req_post.items() if k.startswith('delete_file_')}
    csv_files = {v for v in to_delete if v.endswith('.csv')}
    non_csv_files = {v for v in to_delete if not v.endswith('.csv')}
    return csv_files, non_csv_files


# todo parse non layer csv files (maps_info, layers_info, poi_names, pict_codes)
#  maybe save them as project attributes
def parse_csv(req_post, req_files):
    ignore_files = parse_ignore_files(req_post)
    csv_dict = {}
    for key in req_files.keys():
        for f in req_files.getlist(key):
            if f.name in ignore_files:
                continue

            mime_type, ext = f.content_type.split('/')
            title = '.'.join(f.name.split('.')[:-1])
            if ext == 'csv':
                if title in csv_dict:   # duplicate file
                    return None
                else:
                    csv_dict[title] = f
    return csv_dict
