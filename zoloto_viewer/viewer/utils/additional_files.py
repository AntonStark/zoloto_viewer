import csv
import io

RGB_SCALE = 255
CMYK_SCALE = 100


def parse_layers_info(upload):
    tw = io.TextIOWrapper(upload.file, encoding='utf-8')
    data = {}
    try:
        for row in csv.reader(tw):
            title, desc, color = row
            data[title] = (desc, color)
    except csv.Error:
        return None
    finally:
        tw.detach()
    return data


def parse_maps_info(upload):
    """
    :return: { indd_floor -> (offset, bounds) }
    """
    tw = io.TextIOWrapper(upload.file, encoding='utf-8')
    data = {}
    try:
        for row in csv.reader(tw):
            offset, indd_floor, top, left, bottom, right = row
            data[indd_floor] = (offset, [top, left, bottom, right])
    except csv.Error:
        return None
    finally:
        tw.detach()
    return data


def color_as_hex(color_str):
    """
    :param color_str: in a form of "(CMYK, 100, 100, 100, 100)
    """
    def cmyk_to_rgb(c, m, y, k):
        """Very naive realization"""
        r = RGB_SCALE * (1.0 - c / float(CMYK_SCALE)) * (1.0 - k / float(CMYK_SCALE))
        g = RGB_SCALE * (1.0 - m / float(CMYK_SCALE)) * (1.0 - k / float(CMYK_SCALE))
        b = RGB_SCALE * (1.0 - y / float(CMYK_SCALE)) * (1.0 - k / float(CMYK_SCALE))
        return int(r), int(g), int(b)

    mode, *raw_vals = color_str[1:-1].split(',')
    vals = list(map(int, raw_vals))
    if mode == 'CMYK':
        rgb = cmyk_to_rgb(*vals)
    elif mode == 'RGB':
        rgb = vals
    else:
        rgb = 0, 0, 0
    return '#{:02x}{:02x}{:02x}'.format(*rgb)
