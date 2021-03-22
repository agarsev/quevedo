# 2021-02-22 Antonio F. G. Sevilla <afgs@ucm.es>
#
# Example of a script that translates tags values (annotations) from an old
# naming schema to a new one. That is, it modifies the values written in by the
# annotators, keeping tag schema structure.

import sys

from quevedo.dataset import Dataset
from quevedo.annotation import Target

translation = {
    'symbol': 'Symbol',
    'face': 'Face',
    '': 'TODO',
}


if __name__ == '__main__':
    ds = Dataset(sys.argv[1])
    for t in ds.get_annotations(Target.TRAN):
        for s in t.anot.get('symbols', []):
            original = s['tags'][0]
            if original in translation:
                s['tags'][0] = translation[original]
            else:
                print('Tag {} not in translation dictionary'.format(
                    original))
        t.save()
