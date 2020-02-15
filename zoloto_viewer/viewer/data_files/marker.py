import collections
import csv
import io
import json


def parse_path(path_str):
    try:
        return json.loads(path_str)
    except json.JSONDecodeError:
        return path_str


def parse_line(row):
    number, *m_vars, path = row
    return number, (parse_path(path), m_vars)


def parse_markers_file(file):
    tw = io.TextIOWrapper(file, encoding='utf-8')
    data = {}
    try:
        for row in csv.reader(tw):
            number, *m_vars, path = row
            data[number] = (parse_path(path), m_vars)
        return data
    except csv.Error:
        return None
    finally:
        tw.detach()


def reconfigure_markers_data(data):
    del data['number']
    reconfigured = collections.defaultdict(dict)
    numbers = set()
    for number, info in data.items():
        prefix, floor, n = number.split('/')
        # omit prefix check for now
        reconfigured[floor][n] = info + (number,)
        numbers.add(number)
    return reconfigured, numbers


def extend_markers_data(data):
    extended = {}
    for number, info in data.items():
        if number == 'number':
            continue
        prefix, floor, n = number.split('/')
        extended[number] = info + (floor, n)
    return extended     # { number -> (path, vars, indd_floor, n) }
