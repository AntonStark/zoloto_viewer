import sys


def scan_replace_table(csv_file):
    def parse_csv_line(line):
        return tuple(line.strip('\n').split(','))

    with open(csv_file, 'r') as cf:
        data = cf.readlines()
    data = [parse_csv_line(line) for line in data]
    return data


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args:
        raise ValueError('csv file path missing')
    csv_file = args[0]
    replace_table = scan_replace_table(csv_file)
