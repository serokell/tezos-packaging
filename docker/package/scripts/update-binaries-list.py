import os
import sys
import json

binaries_json_path_suffix = "/tests/binaries.json"
binaries_list_path_suffix = "/tmp/binaries.txt"

def update_binaries(binaries, field):
    binaries_json_path = os.environ["PWD"] + binaries_json_path_suffix
    with open(binaries_json_path, 'r') as file:
        data = json.load(file)

    data[field] = binaries
    with open(binaries_json_path, 'w') as file:
        json.dump(data, file, indent=4)


def main():
    tag = os.environ["BUILDKITE_TAG"]
    binaries = []

    binaries_list_path = os.environ["PWD"] + binaries_list_path_suffix
    with open(binaries_list_path, 'r') as f:
        binaries = [l.strip() for l in f.readlines()]
    print(binaries)
    if not binaries:
        raise Exception('Exception, while reading binaries list: binaries list is empty')

    field = 'released'
    if 'rc' in tag:
        field = 'candidates'

    update_binaries(binaries, field)
    os.remove(binaries_list_path)


if __name__ == '__main__':
    main()

