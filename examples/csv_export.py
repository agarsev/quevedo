# 2021-05-31 Antonio F. G. Sevilla <afgs@ucm.es>
# Licensed under the Open Software License version 3.0
#
# This script exports all annotations in the dataset into csv format, to be
# later able to compute frequency and co-occurence statistics.

from quevedo import Dataset, Grapheme, Logogram
import sys

SEPARATOR = ';'

if __name__ == '__main__':

    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} path/to/dataset')
        exit(0)

    ds = Dataset(sys.argv[1])

    print(SEPARATOR.join(ds.config['tag_schema']))

    for a in ds.get_annotations():
        if isinstance(a, Logogram):
            for g in a.graphemes:
                print(SEPARATOR.join(g.tags))
        elif isinstance(a, Grapheme):
            print(SEPARATOR.join(a.tags))
