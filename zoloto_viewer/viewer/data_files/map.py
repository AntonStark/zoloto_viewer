import csv
import io


def parse_line(row):
    offset, indd_floor, top, left, bottom, right = row
    return indd_floor, (offset, [top, left, bottom, right])


def parse_maps_file(file):
    """
    :return: { indd_floor -> (offset, bounds) }
    """
    tw = io.TextIOWrapper(file, encoding='utf-8')
    data = {}
    try:
        for row in csv.reader(tw):
            offset, indd_floor, top, left, bottom, right = row
            data[indd_floor] = (offset, [top, left, bottom, right])
        return data
    except csv.Error:
        return None
    finally:
        tw.detach()
